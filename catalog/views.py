from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from accounts.models import User
from accounts.permissions import IsAdminOrStaff, ReadOnlyOrAdminStaff
from notifications.services import create_notifications, notify_stock_change

from .models import Category, Product, SellerProduct
from .serializers import CategorySerializer, ProductSerializer, ProductWriteSerializer, SellerProductSerializer, SellerProductWriteSerializer
from dipcom.pagination import SellerListPagination


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


class PublicShopViewSet(viewsets.ViewSet):
    """One public, searchable feed containing admin and approved seller stock."""
    permission_classes = [permissions.AllowAny]
    pagination_class = SellerListPagination

    def list(self, request):
        query = request.query_params.get('q', '').strip()
        category_id = request.query_params.get('categoryId', '').strip()
        brand = request.query_params.get('brand', '').strip()
        stock_filter = request.query_params.get('stock', '').strip()
        hot_deal = request.query_params.get('hotDeal', '').strip()
        ordering = request.query_params.get('ordering', '-created_at').strip()
        products = Product.objects.select_related('category').all()
        seller_products = SellerProduct.objects.select_related('category', 'seller').filter(moderation_status=SellerProduct.ModerationStatus.APPROVED, is_available=True)
        if query:
            search = Q(name__icontains=query) | Q(brand__icontains=query) | Q(category__name__icontains=query)
            products, seller_products = products.filter(search), seller_products.filter(search)
        if category_id:
            products, seller_products = products.filter(category_id=category_id), seller_products.filter(category_id=category_id)
        if brand:
            products, seller_products = products.filter(brand__icontains=brand), seller_products.filter(brand__icontains=brand)
        if stock_filter == 'in-stock':
            products, seller_products = products.filter(stock__gt=3), seller_products.filter(stock__gt=3)
        elif stock_filter == 'low-stock':
            products, seller_products = products.filter(stock__gt=0, stock__lte=3), seller_products.filter(stock__gt=0, stock__lte=3)
        elif stock_filter == 'out-of-stock':
            products, seller_products = products.filter(stock=0), seller_products.filter(stock=0)
        if hot_deal == 'hot':
            products, seller_products = products.filter(hot_deal=True), seller_products.none()
        elif hot_deal == 'regular':
            products = products.filter(hot_deal=False)
        items = ([{**item, 'source': 'admin'} for item in ProductSerializer(products, many=True, context={'request': request}).data] +
                 [{**item, 'source': 'seller'} for item in SellerProductSerializer(seller_products, many=True, context={'request': request}).data])
        # Keep DIPCOM/admin stock ahead of seller posts, with admin hot deals first.
        # Python's stable sorting preserves this priority within every sort option.
        if ordering == 'price':
            items.sort(key=lambda item: float(item['price']))
        elif ordering == '-price':
            items.sort(key=lambda item: float(item['price']), reverse=True)
        else:
            items.sort(key=lambda item: item['createdAt'], reverse=True)

        def source_priority(item):
            if item['source'] == 'admin' and item.get('hotDeal'):
                return 0
            if item['source'] == 'admin':
                return 1
            return 2

        items.sort(key=source_priority)
        paginator = self.pagination_class()
        return paginator.get_paginated_response(paginator.paginate_queryset(items, request))


class SellerProductViewSet(viewsets.ModelViewSet):
    queryset = SellerProduct.objects.select_related('seller', 'moderated_by').all().order_by('-created_at')
    pagination_class = SellerListPagination

    def get_permissions(self):
        if self.action == 'summary':
            return [permissions.IsAuthenticated()]
        if self.action in {'list', 'retrieve'}:
            return [permissions.AllowAny()]
        if self.action in {'approve', 'reject'}:
            return [permissions.IsAuthenticated(), IsAdminOrStaff()]
        if self.action in {'mark_available', 'mark_unavailable'}:
            return [permissions.IsAuthenticated()]
        if self.action in {'update', 'partial_update'}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        if request.user.role != 'seller' and not request.user.is_staff:
            raise ValidationError({'detail': 'Only sellers can view this summary.'})
        queryset = SellerProduct.objects.filter(seller=request.user)
        totals = queryset.aggregate(products=Count('id'), units=Sum('stock'))
        return Response({
            'products': totals['products'], 'totalUnits': totals['units'] or 0,
            'inventoryValue': sum(item.price * item.stock for item in queryset),
            'healthy': queryset.filter(stock__gt=3).count(),
            'lowStock': queryset.filter(stock__gt=0, stock__lte=3).count(),
            'outOfStock': queryset.filter(stock=0).count(),
            'categories': list(queryset.values('category__name').annotate(count=Count('id'))),
            'topProducts': list(queryset.values('name').annotate(units=Sum('stock')).order_by('-units')[:5]),
        })

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return SellerProductWriteSerializer
        return SellerProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated and (user.is_staff or user.role == 'admin'):
            pass
        elif user.is_authenticated and user.role == 'seller':
            queryset = queryset.filter(seller=user)
        else:
            queryset = queryset.filter(
                moderation_status=SellerProduct.ModerationStatus.APPROVED,
                is_available=True,
            )

        query = self.request.query_params.get('q', '').strip()
        category = self.request.query_params.get('category', '').strip()
        category_id = self.request.query_params.get('categoryId', '').strip()
        stock_filter = self.request.query_params.get('stock', '').strip()
        status_filter = self.request.query_params.get('status', '').strip()
        availability_filter = self.request.query_params.get('availability', '').strip()

        if query:
            queryset = queryset.filter(
                name__icontains=query,
            ) | queryset.filter(brand__icontains=query) | queryset.filter(category__name__icontains=query)

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

        if status_filter == 'reviewed':
            queryset = queryset.exclude(moderation_status=SellerProduct.ModerationStatus.PENDING)
        elif status_filter in {choice[0] for choice in SellerProduct.ModerationStatus.choices}:
            queryset = queryset.filter(moderation_status=status_filter)

        if availability_filter == 'available':
            queryset = queryset.filter(is_available=True)
        elif availability_filter == 'unavailable':
            queryset = queryset.filter(is_available=False)

        return queryset.distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['seller'] = self.request.user
        return context

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'seller' and not user.is_staff:
            product = serializer.save(seller=user)
        else:
            seller_id = self.request.data.get('sellerId')
            seller = user if not seller_id else User.objects.get(id=seller_id)
            product = serializer.save(seller=seller)

        create_notifications(
            User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
            kind='seller_product_submitted',
            item_name=product.name,
            metadata={
                'itemType': 'seller_product',
                'itemId': product.id,
                'categoryId': product.category_id,
                'sellerId': str(product.seller_id),
                'targetPath': '/admin/posts',
            },
        )

    def perform_update(self, serializer):
        previous_stock = serializer.instance.stock
        previous_status = serializer.instance.moderation_status
        product = serializer.save()

        if self.request.user.role == 'seller' and not self.request.user.is_staff:
            product.moderation_status = SellerProduct.ModerationStatus.PENDING
            product.moderation_note = ''
            product.moderated_by = None
            product.moderated_at = None
            product.is_available = True
            product.save(update_fields=['moderation_status', 'moderation_note', 'moderated_by', 'moderated_at', 'is_available', 'updated_at'])

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
                'targetPath': '/seller/stock',
            },
        )

        if self.request.user.role == 'seller' and not self.request.user.is_staff and previous_status == SellerProduct.ModerationStatus.REJECTED:
            create_notifications(
                User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
                kind='seller_product_submitted',
                item_name=product.name,
                metadata={
                    'itemType': 'seller_product',
                    'itemId': product.id,
                    'categoryId': product.category_id,
                    'sellerId': str(product.seller_id),
                    'targetPath': '/admin/posts',
                },
            )

    @action(detail=True, methods=['post'], url_path='mark-unavailable')
    def mark_unavailable(self, request, pk=None):
        product = self.get_object()

        if request.user.role == 'seller' and str(product.seller_id) != str(request.user.id):
            raise ValidationError({'detail': 'You can only update your own post.'})

        if request.user.role not in {'seller', 'admin'} and not request.user.is_staff:
            raise ValidationError({'detail': 'You do not have permission to update this post.'})

        product.is_available = False
        product.save(update_fields=['is_available', 'updated_at'])

        if request.user.role == 'seller' and not request.user.is_staff:
            create_notifications(
                User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
                kind='seller_product_unavailable',
                item_name=product.name,
                metadata={
                    'itemType': 'seller_product',
                    'itemId': product.id,
                    'sellerId': str(product.seller_id),
                    'targetPath': '/admin/posts',
                },
            )

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-available')
    def mark_available(self, request, pk=None):
        product = self.get_object()

        if request.user.role == 'seller' and str(product.seller_id) != str(request.user.id):
            raise ValidationError({'detail': 'You can only update your own post.'})

        if request.user.role not in {'seller', 'admin'} and not request.user.is_staff:
            raise ValidationError({'detail': 'You do not have permission to update this post.'})

        product.is_available = True
        product.save(update_fields=['is_available', 'updated_at'])

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        product = self.get_object()
        product.moderation_status = SellerProduct.ModerationStatus.APPROVED
        product.moderation_note = ''
        product.moderated_by = request.user
        product.moderated_at = timezone.now()
        product.is_available = True
        product.save(update_fields=['moderation_status', 'moderation_note', 'moderated_by', 'moderated_at', 'is_available', 'updated_at'])

        create_notifications(
            [product.seller],
            kind='seller_product_approved',
            item_name=product.name,
            metadata={
                'itemType': 'seller_product',
                'itemId': product.id,
                'sellerId': str(product.seller_id),
                'targetPath': '/seller/posts',
            },
        )

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        product = self.get_object()
        note = str(request.data.get('note', '')).strip()
        if not note:
            raise ValidationError({'note': 'A rejection note is required.'})

        product.moderation_status = SellerProduct.ModerationStatus.REJECTED
        product.moderation_note = note
        product.moderated_by = request.user
        product.moderated_at = timezone.now()
        product.is_available = False
        product.save(update_fields=['moderation_status', 'moderation_note', 'moderated_by', 'moderated_at', 'is_available', 'updated_at'])

        create_notifications(
            [product.seller],
            kind='seller_product_rejected',
            item_name=product.name,
            metadata={
                'itemType': 'seller_product',
                'itemId': product.id,
                'sellerId': str(product.seller_id),
                'targetPath': '/seller/posts',
            },
        )

        return Response(self.get_serializer(product).data, status=status.HTTP_200_OK)
