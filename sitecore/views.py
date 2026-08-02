from django.db.models import F, Sum
from rest_framework import permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.permissions import IsAdminOnly
from accounts.models import User
from catalog.models import Category, Product
from reservations.models import Reservation

from .models import PlatformSettings
from .serializers import PlatformSettingsSerializer


class PlatformSettingsViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action in {'update', 'partial_update'}:
            return [permissions.IsAuthenticated(), IsAdminOnly()]
        return [permissions.AllowAny()]

    def list(self, request):
        settings = PlatformSettings.get_solo()
        return Response(PlatformSettingsSerializer(settings).data)

    def retrieve(self, request, pk=None):
        settings = PlatformSettings.get_solo()
        return Response(PlatformSettingsSerializer(settings).data)

    def update(self, request, pk=None):
        settings = PlatformSettings.get_solo()
        serializer = PlatformSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    partial_update = update


class AdminDashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOnly]

    def get(self, request):
        products = Product.objects.all()
        return Response({
            'totalProducts': products.count(),
            'stockValue': products.aggregate(value=Sum(F('stock') * F('price')))['value'] or 0,
            'totalSellers': User.objects.filter(role=User.Role.SELLER).count(),
            'brands': list(products.values('brand').annotate(units=Sum('stock')).order_by('-units', 'brand')[:6]),
            'categories': list(Category.objects.values('id', 'name').annotate(units=Sum('products__stock')).order_by('name')),
            'recentReservations': list(Reservation.objects.values('id', 'product_name', 'seller_name', 'final_total').order_by('-created_at')[:6]),
        })
