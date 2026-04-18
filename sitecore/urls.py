from rest_framework.routers import DefaultRouter

from .views import PlatformSettingsViewSet

router = DefaultRouter()
router.register(r'settings', PlatformSettingsViewSet, basename='settings')

urlpatterns = router.urls