from __future__ import annotations

from typing import Any

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password

from .models import Location, User


class LocationBackend(BaseBackend):
    """
    Authenticate using (location, username, password).

    This allows the same username to exist in different locations while keeping
    per-location isolation.
    """

    def authenticate(
        self,
        request,
        username: str | None = None,
        password: str | None = None,
        location: Location | int | str | None = None,
        **kwargs: Any,
    ):
        if username is None or password is None or location is None:
            return None

        if isinstance(location, Location):
            location_obj = location
        else:
            try:
                location_obj = Location.objects.get(pk=location)
            except (Location.DoesNotExist, ValueError, TypeError):
                return None

        try:
            user = User.objects.get(username=username, location=location_obj)
        except User.DoesNotExist:
            return None

        if not user.is_active or not getattr(user, "is_approved", False):
            return None

        if not check_password(password, user.password):
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

