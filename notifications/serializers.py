from rest_framework import serializers

from .models import Notification, NotificationDevice


class NotificationSerializer(serializers.ModelSerializer):
	createdAt = serializers.DateTimeField(source='created_at', read_only=True)
	readAt = serializers.DateTimeField(source='read_at', read_only=True)
	isRead = serializers.BooleanField(source='is_read', read_only=True)

	class Meta:
		model = Notification
		fields = [
			'id',
			'title',
			'message',
			'kind',
			'metadata',
			'isRead',
			'readAt',
			'createdAt',
		]


class NotificationDeviceSerializer(serializers.ModelSerializer):
	deviceKey = serializers.CharField(source='device_key')
	subscription = serializers.JSONField(required=False)
	userAgent = serializers.CharField(source='user_agent', required=False, allow_blank=True)
	lastSeenAt = serializers.DateTimeField(source='last_seen_at', read_only=True)
	createdAt = serializers.DateTimeField(source='created_at', read_only=True)
	updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

	class Meta:
		model = NotificationDevice
		fields = [
			'id',
			'deviceKey',
			'subscription',
			'label',
			'platform',
			'userAgent',
			'lastSeenAt',
			'createdAt',
			'updatedAt',
		]
