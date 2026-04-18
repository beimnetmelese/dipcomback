import uuid

from django.conf import settings
from django.db import models


def generate_string_id():
	return uuid.uuid4().hex


class Reservation(models.Model):
	class Status(models.TextChoices):
		PENDING = 'pending', 'Pending'
		APPROVED = 'approved', 'Approved'
		REJECTED = 'rejected', 'Rejected'
		DELIVERED = 'delivered', 'Delivered'

	id = models.CharField(primary_key=True, max_length=36, default=generate_string_id, editable=False)
	product = models.ForeignKey(
		'catalog.Product',
		on_delete=models.PROTECT,
		related_name='reservations',
	)
	seller = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='reservations',
	)
	product_name = models.CharField(max_length=255)
	seller_name = models.CharField(max_length=255)
	quantity = models.PositiveIntegerField()
	base_total = models.DecimalField(max_digits=12, decimal_places=2)
	final_total = models.DecimalField(max_digits=12, decimal_places=2)
	discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	delivered_at = models.DateTimeField(null=True, blank=True)
	removed_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.product_name} - {self.seller_name}'
