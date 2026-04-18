from django.urls import path

from .views import (
	NotificationDeviceRegisterView,
	NotificationListView,
	NotificationInboxView,
	NotificationMarkReadView,
	NotificationPushKeyView,
)

urlpatterns = [
	path('push-key/', NotificationPushKeyView.as_view(), name='notification-push-key'),
	path('list/', NotificationListView.as_view(), name='notification-list'),
	path('inbox/', NotificationInboxView.as_view(), name='notification-inbox'),
	path('mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
	path('devices/', NotificationDeviceRegisterView.as_view(), name='notification-device-register'),
]
