from django.utils import timezone
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationDevice
from .vapid import get_vapid_public_key
from .serializers import NotificationDeviceSerializer, NotificationSerializer


class NotificationListView(ListAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = NotificationSerializer

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user)


class NotificationInboxView(ListAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = NotificationSerializer

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user, is_read=False)


class NotificationMarkReadView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		ids = request.data.get('ids', [])
		if not isinstance(ids, list):
			ids = []

		updated = Notification.objects.filter(
			recipient=request.user,
			id__in=ids,
			is_read=False,
		).update(is_read=True, read_at=timezone.now())

		return Response({'updated': updated})


class NotificationDeviceRegisterView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request):
		serializer = NotificationDeviceSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		validated = serializer.validated_data
		device_key = validated['device_key']

		device, _ = NotificationDevice.objects.update_or_create(
			user=request.user,
			device_key=device_key,
			defaults={
				'subscription': validated.get('subscription', {}),
				'label': validated.get('label', ''),
				'platform': validated.get('platform', ''),
				'user_agent': validated.get('user_agent', ''),
				'is_active': True,
				'last_seen_at': timezone.now(),
			},
		)
		return Response(NotificationDeviceSerializer(device).data, status=201)


class NotificationPushKeyView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		return Response({'publicKey': get_vapid_public_key()})
