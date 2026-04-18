from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AdminAccountViewSet, CurrentUserView, LoginView, SellerRegistrationView, SellerViewSet

router = DefaultRouter()
router.register(r'sellers', SellerViewSet, basename='sellers')
router.register(r'admins', AdminAccountViewSet, basename='admins')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/seller/', SellerRegistrationView.as_view(), name='register-seller'),
    path('me/', CurrentUserView.as_view(), name='me'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('', include(router.urls)),
]