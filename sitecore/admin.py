from django.contrib import admin

from .models import PlatformSettings


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
	def has_add_permission(self, request):
		return not PlatformSettings.objects.exists()
