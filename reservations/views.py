from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdminOrStaff
from accounts.models import User
from notifications.services import create_notifications, notify_stock_change

from .models import Reservation
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related('product', 'seller').all()
    serializer_class = ReservationSerializer

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role not in {'admin', 'staff'}:
            queryset = queryset.filter(seller=user)

        query = self.request.query_params.get('q', '').strip()
        status_filter = self.request.query_params.get('status', '').strip()

        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query)
                | Q(seller_name__icontains=query)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return ReservationCreateSerializer
        return ReservationSerializer

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
            reservation.save(update_fields=['status', 'removed_at'])

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

# Create your views here.
