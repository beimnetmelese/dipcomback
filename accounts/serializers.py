from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AdminAccount, User
from notifications.services import create_notifications
from sitecore.models import PlatformSettings


class UserSummarySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='display_name')
    businessName = serializers.CharField(source='business_name', required=False, allow_blank=True)
    phoneNumber = serializers.CharField(source='phone_number', required=False)
    location = serializers.CharField(required=False)
    tinNumber = serializers.CharField(source='tin_number', required=False)
    sellerStatus = serializers.SerializerMethodField()
    removed = serializers.BooleanField(source='is_removed', read_only=True)
    removalReason = serializers.CharField(source='removal_reason', read_only=True)
    removedAt = serializers.DateTimeField(source='removed_at', read_only=True)
    sellerDiscountPercent = serializers.DecimalField(
        source='seller_discount_percent',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=50,
        required=False,
    )
    joinedAt = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'role',
            'businessName',
            'phoneNumber',
            'location',
            'tinNumber',
            'sellerStatus',
            'removed',
            'removalReason',
            'removedAt',
            'sellerDiscountPercent',
            'joinedAt',
        ]

    def get_sellerStatus(self, instance):
        return 'removed' if getattr(instance, 'is_removed', False) else instance.seller_status


class SellerCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='display_name')
    businessName = serializers.CharField(source='business_name')
    phoneNumber = serializers.CharField(source='phone_number', required=True, allow_blank=False)
    location = serializers.CharField(required=True, allow_blank=False)
    tinNumber = serializers.CharField(source='tin_number', required=True, allow_blank=False)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['name', 'email', 'businessName', 'phoneNumber', 'location', 'tinNumber', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            display_name=validated_data.get('display_name', ''),
            business_name=validated_data.get('business_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            location=validated_data.get('location', 'Addis Ababa'),
            tin_number=validated_data.get('tin_number', '000000000'),
            seller_discount_percent=PlatformSettings.get_solo().commission_percent,
            role=User.Role.SELLER,
            seller_status=User.SellerStatus.PENDING,
        )

        admin_users = User.objects.filter(role=User.Role.ADMIN)
        create_notifications(
            admin_users,
            kind='seller_registered',
            item_name=user.display_name or user.business_name or user.email,
            metadata={
                'sellerId': str(user.id),
                'sellerName': user.display_name,
                'sellerEmail': user.email,
                'targetPath': '/admin/sellers',
            },
        )
        return user


class AdminAccountSerializer(serializers.ModelSerializer):
    joinedAt = serializers.DateTimeField(source='joined_at', read_only=True)
    role = serializers.CharField(read_only=True)
    roleType = serializers.ChoiceField(
        choices=[('admin', 'Admin'), ('staff', 'Staff Member')],
        write_only=True,
        required=False,
        default='staff',
    )
    password = serializers.CharField(write_only=True, min_length=6, required=False)

    class Meta:
        model = AdminAccount
        fields = ['id', 'name', 'email', 'role', 'roleType', 'password', 'joinedAt']

    def create(self, validated_data):
        role_type = validated_data.pop('roleType', 'staff')
        password = validated_data.pop('password', '')

        if not password:
            raise serializers.ValidationError({'password': 'Password is required.'})

        email = validated_data.get('email', '').strip().lower()
        name = validated_data.get('name', '').strip()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})

        if role_type == 'admin':
            user_role = User.Role.ADMIN
            role_label = 'Admin'
            is_superuser = True
        else:
            user_role = User.Role.STAFF
            role_label = 'Staff Member'
            is_superuser = False

        user = User.objects.create_user(
            email=email,
            password=password,
            display_name=name,
            role=user_role,
            seller_status=User.SellerStatus.APPROVED,
            business_name='',
        )
        user.is_staff = True
        user.is_superuser = is_superuser
        user.save(update_fields=['is_staff', 'is_superuser'])

        validated_data['email'] = email
        validated_data['name'] = name
        validated_data['role'] = role_label
        return super().create(validated_data)


class EmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(request=self.context.get('request'), username=email, password=password)
        if user is None:
            try:
                candidate = User.objects.get(email__iexact=email)
            except User.DoesNotExist as exc:
                raise AuthenticationFailed('No account found with this email address.') from exc

            if not candidate.check_password(password):
                raise AuthenticationFailed('Incorrect password. Please try again.')

            user = candidate

        if not user.is_active:
            raise AuthenticationFailed('Account is disabled.')

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSummarySerializer(user).data,
        }


class CurrentUserSerializer(UserSummarySerializer):
    class Meta(UserSummarySerializer.Meta):
        fields = UserSummarySerializer.Meta.fields