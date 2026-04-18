from __future__ import annotations

import json
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from pywebpush import WebPushException, webpush

from .models import Notification
from .vapid import get_vapid_claims, get_vapid_private_key_pem

User = get_user_model()

LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK_THRESHOLD = 0


def stock_level(stock: int):
	if stock <= OUT_OF_STOCK_THRESHOLD:
		return Notification.Kind.STOCK_OUT
	if stock < LOW_STOCK_THRESHOLD:
		return Notification.Kind.STOCK_LOW
	return None


def notification_title_and_message(kind: str, item_name: str):
	if kind == Notification.Kind.STOCK_OUT:
		return f'Out of stock: {item_name}', f'{item_name} is now out of stock.'
	if kind == Notification.Kind.STOCK_LOW:
		return f'Low stock: {item_name}', f'{item_name} stock is below {LOW_STOCK_THRESHOLD}.'
	if kind == Notification.Kind.RESERVATION_CREATED:
		return 'New reservation request', f'A seller reserved {item_name}.'
	if kind == Notification.Kind.RESERVATION_APPROVED:
		return 'Reservation approved', f'Your reservation for {item_name} was approved.'
	if kind == Notification.Kind.RESERVATION_REJECTED:
		return 'Reservation rejected', f'Your reservation for {item_name} was rejected.'
	if kind == Notification.Kind.RESERVATION_DELIVERED:
		return 'Reservation delivered', f'Your reservation for {item_name} was delivered.'
	return 'Notification', item_name


def _normalize_users(users: Iterable[User] | QuerySet[User]):
	seen = set()
	result = []
	for user in users:
		if not user or not getattr(user, 'is_active', True):
			continue
		if user.id in seen:
			continue
		seen.add(user.id)
		result.append(user)
	return result


def create_notifications(users, *, kind: str, item_name: str, metadata: dict | None = None):
	users = _normalize_users(users)
	if not users:
		return []

	title, message = notification_title_and_message(kind, item_name)
	notifications = []
	for user in users:
		notifications.append(
			Notification.objects.create(
				recipient=user,
				title=title,
				message=message,
				kind=kind,
				metadata=metadata or {},
			),
		)

	send_push_notifications(notifications)
	return notifications


def send_push_notifications(notifications: Iterable[Notification]):
	from .models import NotificationDevice

	for notification in notifications:
		devices = NotificationDevice.objects.filter(
			user=notification.recipient,
			is_active=True,
		).exclude(subscription={})

		payload = {
			'id': notification.id,
			'title': notification.title,
			'message': notification.message,
			'kind': notification.kind,
			'metadata': notification.metadata,
			'createdAt': notification.created_at.isoformat(),
		}

		for device in devices:
			try:
				webpush(
					subscription_info=device.subscription,
					data=json.dumps(payload),
					vapid_private_key=get_vapid_private_key_pem(),
					vapid_claims=get_vapid_claims(),
				)
			except WebPushException as error:
				response = getattr(error, 'response', None)
				status_code = getattr(response, 'status_code', None)
				if status_code in {404, 410}:
					device.is_active = False
					device.save(update_fields=['is_active'])


def notify_stock_change(
	*,
	users,
	item_name: str,
	old_stock: int | None,
	new_stock: int,
	metadata: dict | None = None,
):
	new_kind = stock_level(int(new_stock))
	old_kind = stock_level(int(old_stock)) if old_stock is not None else None
	if not new_kind or new_kind == old_kind:
		return []

	return create_notifications(
		users,
		kind=new_kind,
		item_name=item_name,
		metadata=metadata,
	)
