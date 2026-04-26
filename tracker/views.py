from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import AppLoginForm, MasterUserEditForm, ProductForm, RegisterForm
from .models import DailyList, ExpirationEntry, Product, Training, TrainingStep, User


class MasterRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and getattr(u, "is_master", False)


class StaffOrSuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.is_staff or u.is_superuser)


def entry_warning_state(expiration_date, list_created_date):
    """
    Compare expiration to the calendar date the list was created.
    Returns: 'ok' | 'soon' | 'expired'
    """
    delta = expiration_date - list_created_date
    days = delta.days
    if days < 0:
        return "expired"
    if days <= 7:
        return "soon"
    return "ok"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/dashboard.html"


class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = "tracker/register.html"
    success_url = reverse_lazy("tracker:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_approved = False
        user.is_active = True
        user.save()
        form.save_m2m()
        messages.success(
            self.request,
            "Account request submitted. A master user must approve your account before you can sign in.",
        )
        return redirect(self.success_url)


class AppLoginView(LoginView):
    template_name = "tracker/login.html"
    authentication_form = AppLoginForm


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("tracker:login")


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "tracker/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.filter(location=self.request.user.location)


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "tracker/product_form.html"
    success_url = reverse_lazy("tracker:product_list")

    def form_valid(self, form):
        form.instance.location = self.request.user.location
        messages.success(self.request, "Product added.")
        return super().form_valid(form)


class DailyListCreateView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/daily_list_create.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = Product.objects.filter(location=self.request.user.location)
        ctx["product_form"] = ProductForm()
        return ctx

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "add_product":
            form = ProductForm(request.POST)
            if form.is_valid():
                form.instance.location = request.user.location
                try:
                    form.save()
                except IntegrityError:
                    messages.error(request, "A product with that name already exists.")
                else:
                    messages.success(request, "Product added.")
                return redirect("tracker:daily_list_create")

            ctx = self.get_context_data(**kwargs)
            ctx["product_form"] = form
            return self.render_to_response(ctx)

        products = list(Product.objects.filter(location=request.user.location))
        if not products:
            messages.warning(request, "Add at least one product before creating a list.")
            return redirect("tracker:daily_list_create")

        with transaction.atomic():
            dl = DailyList.objects.create(
                created_by=request.user,
                location=request.user.location,
            )
            saved = 0
            for product in products:
                key = f"exp_{product.pk}"
                raw = request.POST.get(key, "").strip()
                if not raw:
                    continue
                parsed = parse_date(raw)
                if parsed is None:
                    messages.error(request, f"Invalid date for {product.name}.")
                    dl.delete()
                    return redirect("tracker:daily_list_create")
                ExpirationEntry.objects.create(
                    daily_list=dl,
                    product=product,
                    expiration_date=parsed,
                )
                saved += 1

        if saved == 0:
            dl.delete()
            messages.warning(request, "No expiration dates were saved. Enter at least one date.")
            return redirect("tracker:daily_list_create")

        messages.success(request, "Daily list saved.")
        return redirect("tracker:history_detail", pk=dl.pk)


class HistoryListView(LoginRequiredMixin, ListView):
    model = DailyList
    template_name = "tracker/history_list.html"
    context_object_name = "daily_lists"
    paginate_by = getattr(settings, "DEFAULT_PAGINATION_PER_PAGE", 10)

    def get_queryset(self):
        return DailyList.objects.filter(location=self.request.user.location)


class HistoryDetailView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/history_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dl = get_object_or_404(
            DailyList.objects.select_related("created_by"),
            pk=self.kwargs["pk"],
            location=self.request.user.location,
        )
        entries = (
            ExpirationEntry.objects.filter(daily_list=dl)
            .select_related("product")
            .order_by("product__name")
        )
        list_date = dl.created_at.date()
        rows = []
        for e in entries:
            state = entry_warning_state(e.expiration_date, list_date)
            rows.append({"entry": e, "state": state})
        ctx["daily_list"] = dl
        ctx["rows"] = rows
        ctx["can_delete"] = self.request.user.is_master
        return ctx


class DailyListDeleteView(MasterRequiredMixin, View):
    def post(self, request, pk):
        dl = get_object_or_404(DailyList, pk=pk, location=request.user.location)
        dl.delete()
        messages.success(request, "Daily list deleted.")
        return redirect("tracker:history_list")


class MasterUserListView(MasterRequiredMixin, ListView):
    model = User
    template_name = "tracker/admin_users.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.select_related("location").order_by("location__name", "username")


class MasterUserUpdateView(MasterRequiredMixin, UpdateView):
    model = User
    form_class = MasterUserEditForm
    template_name = "tracker/user_edit.html"
    success_url = reverse_lazy("tracker:admin_users")

    def get_queryset(self):
        return User.objects.all()

    def form_valid(self, form):
        messages.success(self.request, "User updated.")
        return super().form_valid(form)


class MasterUserDeleteView(MasterRequiredMixin, View):
    def post(self, request, pk):
        if pk == request.user.pk:
            messages.error(request, "You cannot delete your own account.")
            return redirect("tracker:admin_users")
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, "User deleted.")
        return redirect("tracker:admin_users")


class TrainingListView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/training_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        trainings = (
            Training.objects.filter(location=self.request.user.location)
            .prefetch_related("steps")
            .select_related("created_by")
            .order_by("-created_at")
        )
        ctx["trainings"] = trainings
        return ctx


class TrainingDetailView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/training_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        training = get_object_or_404(
            Training.objects.filter(location=self.request.user.location)
            .prefetch_related("steps")
            .select_related("created_by"),
            pk=self.kwargs["pk"],
        )
        ctx["training"] = training
        ctx["steps"] = list(training.steps.all())
        return ctx


class TrainingCreateView(StaffOrSuperuserRequiredMixin, TemplateView):
    template_name = "tracker/training_create.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("form_data", {"title": "", "steps": [{"id": "s1", "title": "", "description": "", "image_url": ""}]})
        ctx.setdefault("errors", {})
        return ctx

    def post(self, request, *args, **kwargs):
        if not request.user.location_id:
            messages.error(request, "Your account has no location set, so you cannot create trainings.")
            return redirect("tracker:training_list")

        title = (request.POST.get("training_title") or "").strip()
        step_ids_raw = (request.POST.get("step_ids") or "").strip()
        step_ids = [s for s in step_ids_raw.split(",") if s.strip()]

        steps = []
        errors = {}

        if not title:
            errors["training_title"] = "Training title cannot be empty."

        if not step_ids:
            errors["steps"] = "Add at least one step."

        for idx, sid in enumerate(step_ids):
            st = (request.POST.get(f"step_{sid}_title") or "").strip()
            sd = (request.POST.get(f"step_{sid}_description") or "").strip()
            su = (request.POST.get(f"step_{sid}_image_url") or "").strip()
            sf = request.FILES.get(f"step_{sid}_image_file")

            if not st:
                errors[f"step_{sid}_title"] = "Step title cannot be empty."
            if not sd:
                errors[f"step_{sid}_description"] = "Step description cannot be empty."

            steps.append(
                {
                    "id": sid,
                    "title": st,
                    "description": sd,
                    "image_url": su,
                    "has_file": bool(sf),
                }
            )

        if errors:
            ctx = self.get_context_data(**kwargs)
            ctx["errors"] = errors
            ctx["form_data"] = {"title": title, "steps": steps or [{"id": "s1", "title": "", "description": "", "image_url": ""}]}
            return self.render_to_response(ctx)

        tr = Training.objects.create(
            location=request.user.location,
            created_by=request.user,
            title=title,
        )
        for order, sid in enumerate(step_ids):
            st = (request.POST.get(f"step_{sid}_title") or "").strip()
            sd = (request.POST.get(f"step_{sid}_description") or "").strip()
            su = (request.POST.get(f"step_{sid}_image_url") or "").strip()
            sf = request.FILES.get(f"step_{sid}_image_file")

            step = TrainingStep.objects.create(
                training=tr,
                order=order,
                title=st,
                description=sd,
                image_url=su,
            )
            if sf:
                step.image = sf
                step.save(update_fields=["image"])

        messages.success(request, "Training saved.")
        return redirect("tracker:dashboard")

