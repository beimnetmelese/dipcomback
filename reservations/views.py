from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdminOrStaff
from accounts.models import User
from notifications.services import create_notifications, notify_stock_change
from dipcom.pagination import SellerListPagination

from .models import Reservation
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related('product', 'product__category', 'seller').all()
    serializer_class = ReservationSerializer
    pagination_class = SellerListPagination

    def get_permissions(self):
        if self.action in {'public_by_seller_phone', 'public_update_status'}:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in {'public_by_seller_phone', 'public_update_status'}:
            return queryset.order_by('-created_at')

        user = self.request.user

        if user.role not in {'admin', 'staff'}:
            queryset = queryset.filter(seller=user)

        query = self.request.query_params.get('q', '').strip()
        status_filter = self.request.query_params.get('status', '').strip()
        scope = self.request.query_params.get('scope', '').strip()
        date_from = self.request.query_params.get('dateFrom', '').strip()
        date_to = self.request.query_params.get('dateTo', '').strip()

        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query)
                | Q(seller_name__icontains=query)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if scope == 'active':
            queryset = queryset.filter(status__in=[Reservation.Status.PENDING, Reservation.Status.APPROVED])
        elif scope == 'history':
            queryset = queryset.filter(status__in=[Reservation.Status.DELIVERED, Reservation.Status.REJECTED]).annotate(
                reference_at=Coalesce('delivered_at', 'rejected_at', 'created_at')
            )
            if date_from:
                queryset = queryset.filter(reference_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(reference_at__date__lte=date_to)
            return queryset.order_by('-reference_at')

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        self._ensure_admin_or_staff(request)
        queryset = Reservation.objects.all().annotate(
            reference_at=Coalesce('delivered_at', 'rejected_at', 'created_at')
        )
        status_filter = request.query_params.get('status', '').strip()
        date_from = request.query_params.get('dateFrom', '').strip()
        date_to = request.query_params.get('dateTo', '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(reference_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(reference_at__date__lte=date_to)

        totals = queryset.aggregate(units=Sum('quantity'), value=Sum('final_total'))
        sellers = queryset.values('seller_id', 'seller_name').annotate(
            reservations=Count('id'), units=Sum('quantity'), value=Sum('final_total')
        ).order_by('-value')
        return Response({
            'totalUnits': totals['units'] or 0,
            'totalValue': totals['value'] or 0,
            'sellers': [{
                'sellerId': item['seller_id'], 'sellerName': item['seller_name'],
                'reservations': item['reservations'], 'units': item['units'] or 0,
                'value': item['value'] or 0,
            } for item in sellers],
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()
        return Response(ReservationSerializer(reservation).data, status=201)

    def _ensure_admin_or_staff(self, request):
        if request.user.role not in {'admin', 'staff'}:
            raise PermissionDenied('Only admin or staff can update reservation workflow status.')

    @action(detail=True, methods=['post'])
    def pending(self, request, pk=None):
        self._ensure_admin_or_staff(request)
        reservation = self.get_object()
        reservation.status = Reservation.Status.PENDING
        reservation.save(update_fields=['status'])
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        self._ensure_admin_or_staff(request)
        reservation = self.get_object()
        reservation.status = Reservation.Status.APPROVED
        reservation.save(update_fields=['status'])
        create_notifications(
            [reservation.seller],
            kind='reservation_approved',
            item_name=reservation.product_name,
            metadata={
                'reservationId': reservation.id,
                'productId': reservation.product_id,
                'targetPath': '/seller/reservations',
            },
        )
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        self._ensure_admin_or_staff(request)
        reservation = self.get_object()
        reservation.status = Reservation.Status.DELIVERED
        reservation.delivered_at = timezone.now()
        reservation.save(update_fields=['status', 'delivered_at'])
        create_notifications(
            [reservation.seller],
            kind='reservation_delivered',
            item_name=reservation.product_name,
            metadata={
                'reservationId': reservation.id,
                'productId': reservation.product_id,
                'targetPath': '/seller/reservations',
            },
        )
        return Response(self.get_serializer(reservation).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        self._ensure_admin_or_staff(request)
        reservation = self.get_object()
        reason = str(request.data.get('reason', '')).strip()

        with transaction.atomic():
            reservation = (
                Reservation.objects.select_for_update()
                .select_related('product')
                .get(pk=reservation.pk)
            )

            if reservation.status == Reservation.Status.DELIVERED:
                raise ValidationError({'detail': 'Delivered reservations cannot be rejected.'})

            if reservation.status == Reservation.Status.REJECTED:
                return Response(self.get_serializer(reservation).data)

            previous_stock = int(reservation.product.stock)
            new_stock = previous_stock + int(reservation.quantity)
            reservation.product.stock = new_stock
            reservation.product.save(update_fields=['stock'])

            reservation.status = Reservation.Status.REJECTED
            reservation.removed_at = timezone.now()
            reservation.rejection_reason = reason
            reservation.save(update_fields=['status', 'removed_at', 'rejection_reason'])

            notify_stock_change(
                users=User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF]),
                item_name=reservation.product.name,
                old_stock=previous_stock,
                new_stock=new_stock,
                metadata={
                    'productId': reservation.product_id,
                    'reservationId': reservation.id,
                },
            )

            create_notifications(
                [reservation.seller],
                kind='reservation_rejected',
                item_name=reservation.product_name,
                metadata={
                    'reservationId': reservation.id,
                    'productId': reservation.product_id,
                    'targetPath': '/seller/reservations',
                },
            )

        return Response(self.get_serializer(reservation).data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        queryset = self.get_queryset().filter(
            status__in=[Reservation.Status.DELIVERED, Reservation.Status.REJECTED],
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        authentication_classes=[],
        permission_classes=[permissions.AllowAny],
        url_path='public/by-seller-phone',
    )
    def public_by_seller_phone(self, request):
        phone_number = request.query_params.get('phoneNumber', '').strip()
        if not phone_number:
            raise ValidationError({'phoneNumber': 'This query parameter is required.'})

        queryset = (
            Reservation.objects.select_related('product', 'seller')
            .filter(seller__phone_number=phone_number)
            .exclude(status=Reservation.Status.DELIVERED)
            .order_by('-created_at')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['patch'],
        authentication_classes=[],
        permission_classes=[permissions.AllowAny],
        url_path='public/status',
    )
    def public_update_status(self, request, pk=None):
        reservation = self.get_object()
        next_status = str(request.data.get('status', '')).strip().lower()
        reason = str(request.data.get('reason', '')).strip()
        allowed_statuses = {choice[0] for choice in Reservation.Status.choices}

        if next_status not in allowed_statuses:
            raise ValidationError({'status': f'Invalid status. Allowed values: {sorted(allowed_statuses)}'})

        with transaction.atomic():
            reservation = (
                Reservation.objects.select_for_update()
                .select_related('product')
                .get(pk=reservation.pk)
            )

            current_status = reservation.status
            if current_status == next_status:
                return Response(self.get_serializer(reservation).data)

            if current_status == Reservation.Status.REJECTED and next_status != Reservation.Status.REJECTED:
                previous_stock = int(reservation.product.stock)
                required_stock = int(reservation.quantity)
                if previous_stock < required_stock:
                    raise ValidationError({'status': 'Not enough stock to move reservation out of rejected status.'})
                reservation.product.stock = previous_stock - required_stock
                reservation.product.save(update_fields=['stock'])

            if next_status == Reservation.Status.REJECTED and current_status != Reservation.Status.REJECTED:
                previous_stock = int(reservation.product.stock)
                reservation.product.stock = previous_stock + int(reservation.quantity)
                reservation.product.save(update_fields=['stock'])
                reservation.removed_at = timezone.now()
                reservation.rejection_reason = reason
            elif next_status != Reservation.Status.REJECTED:
                reservation.removed_at = None
                reservation.rejection_reason = ''

            if next_status == Reservation.Status.DELIVERED:
                reservation.delivered_at = timezone.now()
            elif next_status != Reservation.Status.DELIVERED:
                reservation.delivered_at = None

            reservation.status = next_status
            reservation.save(update_fields=['status', 'delivered_at', 'removed_at', 'rejection_reason'])

        return Response(self.get_serializer(reservation).data)

# Create your views here.
