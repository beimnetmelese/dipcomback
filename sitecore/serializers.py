from rest_framework import serializers

from .models import PlatformSettings


class PlatformSettingsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    commissionPercent = serializers.DecimalField(source='commission_percent', max_digits=5, decimal_places=2)
    contactPhone = serializers.CharField(source='contact_phone', allow_blank=True, required=False)
    contactAddress = serializers.CharField(source='contact_address', allow_blank=True, required=False)
    businessHours = serializers.CharField(source='business_hours', allow_blank=True, required=False)
    tiktokUrl = serializers.URLField(source='tiktok_url', allow_blank=True, required=False)
    mapUrl = serializers.URLField(source='map_url', allow_blank=True, required=False)
    heroTagline = serializers.CharField(source='hero_tagline', allow_blank=True, required=False)
    heroTitle = serializers.CharField(source='hero_title', allow_blank=True, required=False)
    heroDescription = serializers.CharField(source='hero_description', allow_blank=True, required=False)
    aboutTitle = serializers.CharField(source='about_title', allow_blank=True, required=False)
    aboutDescription = serializers.CharField(source='about_description', allow_blank=True, required=False)
    yearsExperience = serializers.IntegerField(source='years_experience', required=False)
    studentsTrained = serializers.IntegerField(source='students_trained', required=False)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = PlatformSettings
        fields = [
            'id',
            'commissionPercent',
            'contactPhone',
            'contactAddress',
            'businessHours',
            'tiktokUrl',
            'mapUrl',
            'heroTagline',
            'heroTitle',
            'heroDescription',
            'aboutTitle',
            'aboutDescription',
            'yearsExperience',
            'studentsTrained',
            'updatedAt',
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance