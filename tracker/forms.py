from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, UserCreationForm

from .models import Product, User


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
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)


class AppLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)


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
        fields = ("username", "email", "first_name", "last_name", "is_active", "is_master")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)
