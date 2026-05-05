from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AdminAccount, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	model = User
	list_display = ('email', 'display_name', 'phone_number', 'role', 'seller_status', 'seller_discount_percent', 'is_staff', 'is_active')
	list_filter = ('role', 'seller_status', 'is_staff', 'is_active')
	search_fields = ('email', 'display_name', 'business_name', 'phone_number', 'username')
	ordering = ('email',)
	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		('Identity', {'fields': ('email', 'display_name', 'business_name', 'phone_number', 'seller_discount_percent')}),
		('Permissions', {'fields': ('role', 'seller_status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Dates', {'fields': ('last_login', 'date_joined')}),
	)
	readonly_fields = ('last_login', 'date_joined')
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'username', 'display_name', 'business_name', 'phone_number', 'seller_discount_percent', 'role', 'seller_status', 'password1', 'password2'),
		}),
	)


@admin.register(AdminAccount)
class AdminAccountAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'role', 'joined_at')
	search_fields = ('name', 'email', 'role')
