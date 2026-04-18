from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
	list_display = ('product_name', 'seller_name', 'quantity', 'status', 'base_total', 'final_total', 'created_at')
	list_filter = ('status',)
	search_fields = ('product_name', 'seller_name')
