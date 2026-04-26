from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.AppLoginView.as_view(), name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/new/", views.ProductCreateView.as_view(), name="product_create"),
    path("daily-list/new/", views.DailyListCreateView.as_view(), name="daily_list_create"),
    path("history/", views.HistoryListView.as_view(), name="history_list"),
    path("history/<int:pk>/", views.HistoryDetailView.as_view(), name="history_detail"),
    path("history/<int:pk>/delete/", views.DailyListDeleteView.as_view(), name="daily_list_delete"),
    path("trainings/", views.TrainingListView.as_view(), name="training_list"),
    path("trainings/new/", views.TrainingCreateView.as_view(), name="training_create"),
    path("trainings/<int:pk>/", views.TrainingDetailView.as_view(), name="training_detail"),
    path("admin/users/", views.MasterUserListView.as_view(), name="admin_users"),
    path("admin/users/<int:pk>/edit/", views.MasterUserUpdateView.as_view(), name="admin_user_edit"),
    path("admin/users/<int:pk>/delete/", views.MasterUserDeleteView.as_view(), name="admin_user_delete"),
]
