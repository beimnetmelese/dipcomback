from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from catalog.models import Product
from notifications.services import create_notifications, notify_stock_change

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    productId = serializers.CharField(source='product.id', read_only=True)
    sellerId = serializers.UUIDField(source='seller.id', read_only=True)
    productName = serializers.CharField(source='product_name', read_only=True)
    brand = serializers.CharField(source='product.brand', read_only=True)
    categoryName = serializers.CharField(source='product.category.name', read_only=True)
    sellerName = serializers.CharField(source='seller_name', read_only=True)
    baseTotal = serializers.DecimalField(source='base_total', max_digits=12, decimal_places=2, read_only=True)
    finalTotal = serializers.DecimalField(source='final_total', max_digits=12, decimal_places=2, read_only=True)
    discountPercent = serializers.DecimalField(source='discount_percent', max_digits=5, decimal_places=2, read_only=True)
    unitPrice = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    deliveredAt = serializers.DateTimeField(source='delivered_at', read_only=True)
    rejectedAt = serializers.DateTimeField(source='removed_at', read_only=True)

    def get_unitPrice(self, obj):
        if not obj.quantity:
            return Decimal('0.00')
        return (Decimal(obj.final_total) / Decimal(obj.quantity)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'productId',
            'productName',
            'brand',
            'categoryName',
            'sellerId',
            'sellerName',
            'quantity',
            'unitPrice',
            'baseTotal',
            'finalTotal',
            'discountPercent',
            'status',
            'createdAt',
            'deliveredAt',
            'rejectedAt',
        ]


class ReservationCreateSerializer(serializers.Serializer):
    productId = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        try:
            product = Product.objects.get(id=attrs['productId'])
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError({'productId': 'Product not found.'}) from exc

        if product.stock < attrs['quantity']:
            raise serializers.ValidationError({'quantity': 'Quantity cannot be greater than available stock.'})

        attrs['product'] = product
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        product = validated_data['product']
        quantity = validated_data['quantity']

        seller = request.user
        if seller.role != 'seller':
            raise serializers.ValidationError({'detail': 'Only sellers can create reservations.'})

        from sitecore.models import PlatformSettings

        settings = PlatformSettings.get_solo()
        discount_percent = (
            seller.seller_discount_percent
            if seller.seller_discount_percent is not None
            else Decimal(settings.commission_percent)
        )
        base_total = Decimal(product.price) * Decimal(quantity)
        final_total = base_total * (Decimal('1') - discount_percent / Decimal('100'))
        admin_staff_users = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF])

        with transaction.atomic():
            previous_stock = int(product.stock)
            product.stock = previous_stock - quantity
            product.save(update_fields=['stock'])

            reservation = Reservation.objects.create(
                product=product,
                seller=seller,
                product_name=product.name,
                seller_name=seller.display_name or seller.name,
                quantity=quantity,
                base_total=base_total,
                final_total=final_total,
                discount_percent=discount_percent,
                status=Reservation.Status.PENDING,
            )

            create_notifications(
                admin_staff_users,
                kind='reservation_created',
                item_name=product.name,
                metadata={
                    'reservationId': reservation.id,
                    'sellerId': str(seller.id),
                    'sellerName': seller.display_name or seller.name,
                    'productId': product.id,
                    'quantity': quantity,
                    'targetPath': '/admin/reservations',
                },
            )
            notify_stock_change(
                users=admin_staff_users,
                item_name=product.name,
                old_stock=previous_stock,
                new_stock=int(product.stock),
                metadata={
                    'productId': product.id,
                    'reservationId': reservation.id,
                    'targetPath': '/admin/products',
                },
            )

        return reservation