from django.contrib import admin

from .models import Notification, NotificationDevice


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('title', 'recipient', 'kind', 'is_read', 'created_at')
	list_filter = ('kind', 'is_read', 'created_at')
	search_fields = ('title', 'message', 'recipient__email', 'recipient__display_name')


@admin.register(NotificationDevice)
class NotificationDeviceAdmin(admin.ModelAdmin):
	list_display = ('user', 'label', 'platform', 'device_key', 'is_active', 'last_seen_at')
	list_filter = ('platform', 'is_active', 'last_seen_at')
	search_fields = ('user__email', 'user__display_name', 'label', 'device_key')
