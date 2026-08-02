from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet, PublicShopViewSet, SellerProductViewSet

router = DefaultRouter()
router.trailing_slash = '/?'
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'shop-items', PublicShopViewSet, basename='shop-items')
router.register(r'seller-products', SellerProductViewSet, basename='seller-products')

urlpatterns = router.urls
