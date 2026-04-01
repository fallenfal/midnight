from collections import OrderedDict

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm
from django.contrib.auth import authenticate

from .models import Location, Product, User


def _bootstrap_widgets(form):
    for name, field in form.fields.items():
        w = field.widget
        if isinstance(w, forms.CheckboxInput):
            w.attrs.setdefault("class", "form-check-input")
        else:
            w.attrs.setdefault("class", "form-control")


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("location", "username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)


class AppLoginForm(AuthenticationForm):
    location = forms.ModelChoiceField(queryset=Location.objects.none(), empty_label=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].queryset = Location.objects.all()
        self.fields = OrderedDict(
            (k, self.fields[k]) for k in ("location", "username", "password") if k in self.fields
        )
        _bootstrap_widgets(self)

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        location = self.cleaned_data.get("location")
        if not username or not password or not location:
            return self.cleaned_data

        self.user_cache = authenticate(
            self.request,
            username=username,
            password=password,
            location=location,
        )
        if self.user_cache is None:
            raise self.get_invalid_login_error()
        self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)


class MasterUserEditForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = (
            "location",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_approved",
            "is_master",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)
