import uuid

from django.conf import settings
from django.db import models


def generate_string_id():
	return uuid.uuid4().hex


class CatalogItemBase(models.Model):
	id = models.CharField(primary_key=True, max_length=36, default=generate_string_id, editable=False)
	name = models.CharField(max_length=255)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock = models.PositiveIntegerField(default=0)
	brand = models.CharField(max_length=120)
	class Condition(models.TextChoices):
		NEW = 'new', 'Brand New'
		USED = 'used', 'Used'

	condition = models.CharField(max_length=12, choices=Condition.choices, default=Condition.NEW)
	image_url = models.ImageField(upload_to='catalog/', blank=True, null=True, max_length=500)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True
		ordering = ['-created_at', 'name']


class Category(models.Model):
	id = models.CharField(primary_key=True, max_length=36, default=generate_string_id, editable=False)
	name = models.CharField(max_length=120, unique=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='created_categories',
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Product(CatalogItemBase):
	category = models.ForeignKey(
		Category,
		on_delete=models.PROTECT,
		related_name='products',
	)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='catalog_products_created',
	)

	def __str__(self):
		return self.name


class SellerProduct(CatalogItemBase):
	category = models.ForeignKey(
		Category,
		on_delete=models.PROTECT,
		related_name='seller_products',
	)
	seller = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='seller_products',
	)

	def __str__(self):
		return f'{self.name} - {self.seller_id}'
