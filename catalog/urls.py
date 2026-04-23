from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet, SellerProductViewSet

router = DefaultRouter()
router.trailing_slash = '/?'
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'seller-products', SellerProductViewSet, basename='seller-products')

urlpatterns = router.urls