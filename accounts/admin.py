from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .models import AdminAccount, User


class RemovalActionForm(forms.Form):
	removal_reason = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Reason for removal')


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	model = User
	list_display = ('email', 'display_name', 'business_name', 'phone_number', 'location', 'tin_number', 'role', 'seller_status', 'seller_discount_percent', 'is_removed', 'is_staff', 'is_active')
	list_filter = ('role', 'seller_status', 'is_removed', 'is_staff', 'is_active')
	search_fields = ('email', 'display_name', 'business_name', 'phone_number', 'username')
	ordering = ('email',)
	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		('Identity', {'fields': ('email', 'display_name', 'business_name', 'phone_number', 'location', 'tin_number', 'seller_discount_percent')}),
		('Permissions', {'fields': ('role', 'seller_status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Dates', {'fields': ('last_login', 'date_joined')}),
	)
	readonly_fields = ('last_login', 'date_joined')
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'username', 'display_name', 'business_name', 'phone_number', 'location', 'tin_number', 'seller_discount_percent', 'role', 'seller_status', 'password1', 'password2'),
		}),
	)

	# allow admin to provide a removal reason when performing the remove action
	action_form = RemovalActionForm

	def remove_sellers(self, request, queryset):
		"""Mark selected sellers as removed and record the provided reason."""
		reason = request.POST.get('removal_reason', '').strip()
		now = timezone.now()
		for user in queryset:
			user.is_removed = True
			user.removal_reason = reason
			user.removed_at = now
			user.is_active = False
			user.seller_status = User.SellerStatus.REJECTED
			user.save(update_fields=['is_removed', 'removal_reason', 'removed_at', 'is_active', 'seller_status'])

	remove_sellers.short_description = 'Mark selected sellers as removed and record reason'

	actions = ['remove_sellers']


@admin.register(AdminAccount)
class AdminAccountAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'role', 'joined_at')
	search_fields = ('name', 'email', 'role')
