import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


def generate_string_id():
	return uuid.uuid4().hex


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Users must have an email address.')

		email = self.normalize_email(email)
		extra_fields.setdefault('role', User.Role.SELLER)
		extra_fields.setdefault('seller_status', User.SellerStatus.PENDING)
		extra_fields.setdefault('seller_discount_percent', 0)
		extra_fields.setdefault('display_name', '')

		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('role', User.Role.ADMIN)
		extra_fields.setdefault('seller_status', User.SellerStatus.APPROVED)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('Superuser must have is_staff=True.')
		if extra_fields.get('is_superuser') is not True:
			raise ValueError('Superuser must have is_superuser=True.')

		return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = 'admin', 'Admin'
		SELLER = 'seller', 'Seller'
		STAFF = 'staff', 'Staff'

	class SellerStatus(models.TextChoices):
		PENDING = 'pending', 'Pending'
		APPROVED = 'approved', 'Approved'
		REJECTED = 'rejected', 'Rejected'

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	email = models.EmailField(unique=True)
	display_name = models.CharField(max_length=150, blank=True)
	business_name = models.CharField(max_length=255, blank=True)
	phone_number = models.CharField(max_length=30, default='+251900000000')
	location = models.CharField(max_length=255, default='Addis Ababa')
	tin_number = models.CharField(max_length=32, default='000000000')
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.SELLER)
	seller_status = models.CharField(
		max_length=20,
		choices=SellerStatus.choices,
		default=SellerStatus.PENDING,
	)
	seller_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
	# removal tracking when an admin removes or deactivates a seller
	is_removed = models.BooleanField(default=False)
	removal_reason = models.TextField(blank=True, default='')
	removed_at = models.DateTimeField(null=True, blank=True)
	rejection_reason = models.TextField(blank=True, default='')
	rejected_at = models.DateTimeField(null=True, blank=True)

	objects = UserManager()

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	class Meta:
		ordering = ['display_name', 'email']

	def save(self, *args, **kwargs):
		if not self.username:
			prefix = self.email.split('@')[0] if self.email else 'user'
			self.username = f'{prefix}-{uuid.uuid4().hex[:8]}'

		if not self.display_name:
			self.display_name = self.get_full_name() or self.username

		if self.role != self.Role.SELLER:
			self.seller_status = self.SellerStatus.APPROVED
		elif self.seller_status not in {
			self.SellerStatus.PENDING,
			self.SellerStatus.APPROVED,
			self.SellerStatus.REJECTED,
		}:
			self.seller_status = self.SellerStatus.PENDING

		super().save(*args, **kwargs)

	@property
	def name(self):
		return self.display_name or self.get_full_name() or self.username


class AdminAccount(models.Model):
	id = models.CharField(primary_key=True, max_length=36, default=generate_string_id, editable=False)
	name = models.CharField(max_length=150)
	email = models.EmailField(unique=True)
	role = models.CharField(max_length=120)
	joined_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ['-joined_at', 'name']

	def __str__(self):
		return f'{self.name} ({self.role})'
