from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user with Master/Admin flag for elevated permissions."""

    is_master = models.BooleanField(
        default=False,
        help_text="Designates whether this user can manage other users and delete daily lists.",
    )

    def __str__(self):
        return self.username


class Product(models.Model):
    """Base inventory item."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DailyList(models.Model):
    """A single expiration check session for one day."""

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="daily_lists",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Daily list {self.created_at.date()} ({self.pk})"


class ExpirationEntry(models.Model):
    """Links a product to a daily list with the expiration date recorded that day."""

    daily_list = models.ForeignKey(
        DailyList,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="expiration_entries",
    )
    expiration_date = models.DateField()

    class Meta:
        ordering = ["product__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["daily_list", "product"],
                name="unique_product_per_daily_list",
            )
        ]

    def __str__(self):
        return f"{self.product} → {self.expiration_date}"
