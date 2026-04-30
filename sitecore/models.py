from django.db import models


class PlatformSettings(models.Model):
	commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
	contact_phone = models.CharField(max_length=50, blank=True)
	contact_address = models.CharField(max_length=255, blank=True)
	business_hours = models.CharField(max_length=120, blank=True)
	tiktok_url = models.URLField(blank=True)
	map_url = models.URLField(max_length=2000, blank=True)
	hero_tagline = models.CharField(max_length=255, blank=True)
	hero_title = models.CharField(max_length=255, blank=True)
	hero_description = models.TextField(blank=True)
	about_title = models.CharField(max_length=255, blank=True)
	about_description = models.TextField(blank=True)
	years_experience = models.PositiveIntegerField(default=18)
	students_trained = models.PositiveIntegerField(default=200)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Platform settings'
		verbose_name_plural = 'Platform settings'

	@classmethod
	def get_solo(cls):
		obj, _ = cls.objects.get_or_create(pk=1)
		return obj
