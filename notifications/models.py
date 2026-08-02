import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_string_id():
	return uuid.uuid4().hex


class Notification(models.Model):
	class Kind(models.TextChoices):
		STOCK_LOW = 'stock_low', 'Stock Low'
		STOCK_OUT = 'stock_out', 'Stock Out'
		SELLER_REGISTERED = 'seller_registered', 'Seller Registered'
		SELLER_PRODUCT_SUBMITTED = 'seller_product_submitted', 'Seller Product Submitted'
		SELLER_PRODUCT_APPROVED = 'seller_product_approved', 'Seller Product Approved'
		SELLER_PRODUCT_REJECTED = 'seller_product_rejected', 'Seller Product Rejected'
		SELLER_PRODUCT_UNAVAILABLE = 'seller_product_unavailable', 'Seller Product Unavailable'
		RESERVATION_CREATED = 'reservation_created', 'Reservation Created'
		RESERVATION_APPROVED = 'reservation_approved', 'Reservation Approved'
		RESERVATION_REJECTED = 'reservation_rejected', 'Reservation Rejected'
		RESERVATION_DELIVERED = 'reservation_delivered', 'Reservation Delivered'

	id = models.CharField(primary_key=True, max_length=36, default=generate_string_id, editable=False)
	recipient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='notifications',
	)
	title = models.CharField(max_length=180)
	message = models.CharField(max_length=500)
	kind = models.CharField(max_length=40, choices=Kind.choices)
	metadata = models.JSONField(default=dict, blank=True)
	is_read = models.BooleanField(default=False)
	read_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def mark_read(self):
		if self.is_read:
			return

		self.is_read = True
		self.read_at = timezone.now()
		self.save(update_fields=['is_read', 'read_at'])

	def __str__(self):
		return f'{self.title} -> {self.recipient_id}'


class NotificationDevice(models.Model):
	id = models.CharField(primary_key=True, max_length=36, default=generate_string_id, editable=False)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='notification_devices',
	)
	device_key = models.CharField(max_length=128)
	subscription = models.JSONField(default=dict, blank=True)
	label = models.CharField(max_length=255, blank=True)
	platform = models.CharField(max_length=64, blank=True)
	user_agent = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	last_seen_at = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = [('user', 'device_key')]
		ordering = ['-last_seen_at']

	def __str__(self):
		return f'{self.user_id} / {self.device_key}'
