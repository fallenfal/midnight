from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import AppLoginForm, MasterUserEditForm, ProductForm, RegisterForm
from .models import DailyList, ExpirationEntry, Product, User


class MasterRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and getattr(u, "is_master", False)


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
        messages.success(self.request, "Account created. You can sign in now.")
        return super().form_valid(form)


class AppLoginView(LoginView):
    template_name = "tracker/login.html"
    authentication_form = AppLoginForm


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("tracker:login")


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "tracker/product_list.html"
    context_object_name = "products"


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "tracker/product_form.html"
    success_url = reverse_lazy("tracker:product_list")

    def form_valid(self, form):
        messages.success(self.request, "Product added.")
        return super().form_valid(form)


class DailyListCreateView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/daily_list_create.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = Product.objects.all()
        return ctx

    def post(self, request, *args, **kwargs):
        products = list(Product.objects.all())
        if not products:
            messages.warning(request, "Add at least one product before creating a list.")
            return redirect("tracker:daily_list_create")

        with transaction.atomic():
            dl = DailyList.objects.create(created_by=request.user)
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


class HistoryDetailView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/history_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dl = get_object_or_404(DailyList.objects.select_related("created_by"), pk=self.kwargs["pk"])
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
        dl = get_object_or_404(DailyList, pk=pk)
        dl.delete()
        messages.success(request, "Daily list deleted.")
        return redirect("tracker:history_list")


class MasterUserListView(MasterRequiredMixin, ListView):
    model = User
    template_name = "tracker/admin_users.html"
    context_object_name = "users"
    ordering = ["username"]


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

