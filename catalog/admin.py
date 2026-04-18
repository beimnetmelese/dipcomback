from django.contrib import admin

from .models import Category, Product, SellerProduct


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'created_at', 'updated_at')
	search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'brand', 'category', 'price', 'stock', 'created_at')
	list_filter = ('category', 'brand')
	search_fields = ('name', 'brand', 'category')


@admin.register(SellerProduct)
class SellerProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'seller', 'brand', 'category', 'price', 'stock', 'created_at')
	list_filter = ('category', 'brand')
	search_fields = ('name', 'brand', 'seller__email', 'seller__display_name')
