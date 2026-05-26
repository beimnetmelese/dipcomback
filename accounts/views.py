from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone


from .models import AdminAccount, User
from .permissions import IsAdminOnly, IsAdminOrStaff
from .serializers import (
    AdminAccountSerializer,
    CurrentUserSerializer,
    EmailTokenObtainPairSerializer,
    SellerCreateSerializer,
    UserSummarySerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailTokenObtainPairSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class CurrentUserView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return self.request.user


class SellerRegistrationView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SellerCreateSerializer


class SellerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    serializer_class = UserSummarySerializer
    http_method_names = ['get', 'put', 'patch', 'delete', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = User.objects.filter(role=User.Role.SELLER).order_by('-date_joined')
        query = self.request.query_params.get('q', '').strip()
        status_filter = self.request.query_params.get('status', '').strip()

        if query:
            queryset = queryset.filter(display_name__icontains=query) | queryset.filter(business_name__icontains=query) | queryset.filter(email__icontains=query)

        if status_filter == 'removed':
            queryset = queryset.filter(is_removed=True)
        elif status_filter in {User.SellerStatus.PENDING, User.SellerStatus.APPROVED, User.SellerStatus.REJECTED}:
            queryset = queryset.filter(seller_status=status_filter)

        return queryset.distinct()

    def _ensure_not_removed(self, seller):
        if seller.is_removed:
            raise ValidationError({'detail': 'Removed sellers must be reactivated before any other action.'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        seller = self.get_object()
        self._ensure_not_removed(seller)
        seller.seller_status = User.SellerStatus.APPROVED
        seller.rejection_reason = ''
        seller.rejected_at = None
        seller.save(update_fields=['seller_status', 'rejection_reason', 'rejected_at'])
        return Response(self.get_serializer(seller).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        seller = self.get_object()
        self._ensure_not_removed(seller)
        reason = str(request.data.get('reason', '')).strip()
        seller.seller_status = User.SellerStatus.REJECTED
        seller.rejection_reason = reason
        seller.rejected_at = timezone.now()
        seller.save(update_fields=['seller_status', 'rejection_reason', 'rejected_at'])
        return Response(self.get_serializer(seller).data)

    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        seller = self.get_object()
        self._ensure_not_removed(seller)
        reason = str(request.data.get('reason', '')).strip()
        seller.is_removed = True
        seller.removal_reason = reason
        seller.removed_at = timezone.now()
        seller.is_active = False
        seller.seller_status = User.SellerStatus.REJECTED
        seller.save(update_fields=['is_removed', 'removal_reason', 'removed_at', 'is_active', 'seller_status'])
        return Response(self.get_serializer(seller).data)

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        seller = self.get_object()
        seller.is_removed = False
        seller.removal_reason = ''
        seller.removed_at = None
        seller.is_active = True
        seller.seller_status = User.SellerStatus.APPROVED
        seller.rejection_reason = ''
        seller.rejected_at = None
        seller.save(update_fields=['is_removed', 'removal_reason', 'removed_at', 'is_active', 'seller_status', 'rejection_reason', 'rejected_at'])
        return Response(self.get_serializer(seller).data)


class AdminAccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOnly]
    serializer_class = AdminAccountSerializer
    queryset = AdminAccount.objects.all().order_by('-joined_at')

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query) | queryset.filter(email__icontains=query) | queryset.filter(role__icontains=query)
        return queryset.distinct() 

    def perform_destroy(self, instance):
        User.objects.filter(email__iexact=instance.email).delete()
        instance.delete()

# Create your views here.
