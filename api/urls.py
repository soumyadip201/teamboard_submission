from django.urls import path

from .views import KBQueryView, LoginView, RegisterView, UsageSummaryView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("kb/query/", KBQueryView.as_view(), name="kb-query"),
    path("admin/usage-summary/", UsageSummaryView.as_view(), name="admin-usage-summary"),
]
