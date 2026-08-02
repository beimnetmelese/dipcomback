from rest_framework.routers import DefaultRouter

from django.urls import path
from .views import AdminDashboardSummaryView, PlatformSettingsViewSet

router = DefaultRouter()
router.register(r'settings', PlatformSettingsViewSet, basename='settings')

urlpatterns = router.urls + [path('dashboard-summary/', AdminDashboardSummaryView.as_view(), name='dashboard-summary')]
