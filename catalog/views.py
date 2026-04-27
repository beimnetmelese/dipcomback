from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from accounts.models import User
from accounts.permissions import IsAdminOrStaff, ReadOnlyOrAdminStaff
from notifications.services import notify_stock_change

from .models import Category, Product, SellerProduct
from .serializers import CategorySerializer, ProductSerializer, ProductWriteSerializer, SellerProductSerializer, SellerProductWriteSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminOrStaff()]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return ProductWriteSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve', 'subtract_stock', 'add_stock'}:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminOrStaff()]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        category = self.request.query_params.get('category', '').strip()
        category_id = self.request.query_params.get('categoryId', '').strip()
        brand = self.request.query_params.get('brand', '').strip()

        if query:
            queryset = queryset.filter(name__icontains=query) | queryset.filter(brand__icontains=query) | queryset.filter(category__name__icontains=query)

        if category:
            queryset = queryset.filter(category__name=category)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if brand:
            queryset = queryset.filter(brand__icontains=brand)

        return queryset.distinct()

    def perform_create(self, serializer):
        product = serializer.save(created_by=self.request.user)
        notify_stock_change(
            users=User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
            item_name=product.name,
            old_stock=None,
            new_stock=int(product.stock),
            metadata={
                'itemType': 'product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'targetPath': '/admin/products',
            },
        )

    def perform_update(self, serializer):
        previous_stock = serializer.instance.stock
        product = serializer.save()
        notify_stock_change(
            users=User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
            item_name=product.name,
            old_stock=int(previous_stock),
            new_stock=int(product.stock),
            metadata={
                'itemType': 'product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'targetPath': '/admin/products',
            },
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='subtract-stock',
        authentication_classes=[],
        permission_classes=[permissions.AllowAny],
    )
    def subtract_stock(self, request, pk=None):
        product = self.get_object()
        raw_units = request.data.get('unit', request.data.get('units'))

        try:
            units = int(raw_units)
        except (TypeError, ValueError) as exc:
            raise ValidationError({'unit': 'unit must be a positive integer.'}) from exc

        if units < 1:
            raise ValidationError({'unit': 'unit must be at least 1.'})

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=product.pk)
            previous_stock = int(product.stock)

            if units > previous_stock:
                raise ValidationError({'unit': 'Not enough stock to subtract the requested units.'})

            product.stock = previous_stock - units
            product.save(update_fields=['stock', 'updated_at'])

        notify_stock_change(
            users=User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
            item_name=product.name,
            old_stock=previous_stock,
            new_stock=int(product.stock),
            metadata={
                'itemType': 'product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'targetPath': '/admin/products',
                'changeType': 'subtract_stock',
                'units': units,
            },
        )

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        url_path='add-stock',
        authentication_classes=[],
        permission_classes=[permissions.AllowAny],
    )
    def add_stock(self, request, pk=None):
        product = self.get_object()
        raw_units = request.data.get('unit', request.data.get('units'))

        try:
            units = int(raw_units)
        except (TypeError, ValueError) as exc:
            raise ValidationError({'unit': 'unit must be a positive integer.'}) from exc

        if units < 1:
            raise ValidationError({'unit': 'unit must be at least 1.'})

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=product.pk)
            previous_stock = int(product.stock)
            product.stock = previous_stock + units
            product.save(update_fields=['stock', 'updated_at'])

        notify_stock_change(
            users=User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
            item_name=product.name,
            old_stock=previous_stock,
            new_stock=int(product.stock),
            metadata={
                'itemType': 'product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'targetPath': '/admin/products',
                'changeType': 'add_stock',
                'units': units,
            },
        )

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)


class SellerProductViewSet(viewsets.ModelViewSet):
    queryset = SellerProduct.objects.select_related('seller').all().order_by('-created_at')

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return SellerProductWriteSerializer
        return SellerProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_staff and user.role != 'admin':
            queryset = queryset.filter(seller=user)

        query = self.request.query_params.get('q', '').strip()
        category = self.request.query_params.get('category', '').strip()
        category_id = self.request.query_params.get('categoryId', '').strip()
        stock_filter = self.request.query_params.get('stock', '').strip()

        if query:
            queryset = queryset.filter(name__icontains=query) | queryset.filter(brand__icontains=query) | queryset.filter(category__name__icontains=query)

        if category:
            queryset = queryset.filter(category__name=category)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if stock_filter == 'available':
            queryset = queryset.filter(stock__gt=3)
        elif stock_filter == 'low':
            queryset = queryset.filter(stock__gt=0, stock__lte=3)
        elif stock_filter == 'empty':
            queryset = queryset.filter(stock=0)

        return queryset.distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['seller'] = self.request.user
        return context

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'seller' and not user.is_staff:
            product = serializer.save(seller=user)
            notify_stock_change(
                users=[product.seller],
                item_name=product.name,
                old_stock=None,
                new_stock=int(product.stock),
                metadata={
                    'itemType': 'seller_product',
                    'itemId': product.id,
                    'categoryId': product.category_id,
                    'sellerId': str(product.seller_id),
                    'targetPath': '/seller/products',
                },
            )
            return

        seller_id = self.request.data.get('sellerId')
        seller = user if not seller_id else User.objects.get(id=seller_id)
        product = serializer.save(seller=seller)
        notify_stock_change(
            users=[product.seller],
            item_name=product.name,
            old_stock=None,
            new_stock=int(product.stock),
            metadata={
                'itemType': 'seller_product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'sellerId': str(product.seller_id),
                    'targetPath': '/seller/products',
            },
        )

    def perform_update(self, serializer):
        previous_stock = serializer.instance.stock
        product = serializer.save()
        notify_stock_change(
            users=[product.seller],
            item_name=product.name,
            old_stock=int(previous_stock),
            new_stock=int(product.stock),
            metadata={
                'itemType': 'seller_product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'sellerId': str(product.seller_id),
                'targetPath': '/seller/products',
            },
        )

    @action(detail=True, methods=['post'], url_path='subtract-stock')
    def subtract_stock(self, request, pk=None):
        product = self.get_object()
        raw_units = request.data.get('unit', request.data.get('units'))

        try:
            units = int(raw_units)
        except (TypeError, ValueError) as exc:
            raise ValidationError({'unit': 'unit must be a positive integer.'}) from exc

        if units < 1:
            raise ValidationError({'unit': 'unit must be at least 1.'})

        if request.user.role not in {'seller', 'admin'} and not request.user.is_staff:
            raise ValidationError({'detail': 'You do not have permission to subtract this stock.'})

        if request.user.role == 'seller' and str(product.seller_id) != str(request.user.id):
            raise ValidationError({'detail': 'You can only update your own stock.'})

        with transaction.atomic():
            product = SellerProduct.objects.select_for_update().get(pk=product.pk)
            previous_stock = int(product.stock)

            if units > previous_stock:
                raise ValidationError({'unit': 'Not enough stock to subtract the requested units.'})

            product.stock = previous_stock - units
            product.save(update_fields=['stock', 'updated_at'])

        notify_stock_change(
            users=[product.seller],
            item_name=product.name,
            old_stock=previous_stock,
            new_stock=int(product.stock),
            metadata={
                'itemType': 'seller_product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'sellerId': str(product.seller_id),
                'targetPath': '/seller/products',
                'changeType': 'subtract_stock',
                'units': units,
            },
        )

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)
