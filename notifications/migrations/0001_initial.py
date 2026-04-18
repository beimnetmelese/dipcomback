# Generated manually for notifications app.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

	initial = True

	dependencies = [
		migrations.swappable_dependency(settings.AUTH_USER_MODEL),
	]

	operations = [
		migrations.CreateModel(
			name='Notification',
			fields=[
				('id', models.CharField(default=uuid.uuid4, editable=False, max_length=36, primary_key=True, serialize=False)),
				('title', models.CharField(max_length=180)),
				('message', models.CharField(max_length=500)),
				('kind', models.CharField(choices=[('stock_low', 'Stock Low'), ('stock_out', 'Stock Out'), ('reservation_created', 'Reservation Created'), ('reservation_approved', 'Reservation Approved'), ('reservation_rejected', 'Reservation Rejected'), ('reservation_delivered', 'Reservation Delivered')], max_length=40)),
				('metadata', models.JSONField(blank=True, default=dict)),
				('is_read', models.BooleanField(default=False)),
				('read_at', models.DateTimeField(blank=True, null=True)),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
			],
			options={
				'ordering': ['-created_at'],
			},
		),
		migrations.CreateModel(
			name='NotificationDevice',
			fields=[
				('id', models.CharField(default=uuid.uuid4, editable=False, max_length=36, primary_key=True, serialize=False)),
				('device_key', models.CharField(max_length=128)),
				('label', models.CharField(blank=True, max_length=255)),
				('platform', models.CharField(blank=True, max_length=64)),
				('user_agent', models.TextField(blank=True)),
				('is_active', models.BooleanField(default=True)),
				('last_seen_at', models.DateTimeField()),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('updated_at', models.DateTimeField(auto_now=True)),
				('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_devices', to=settings.AUTH_USER_MODEL)),
			],
			options={
				'ordering': ['-last_seen_at'],
				'unique_together': {('user', 'device_key')},
			},
		),
	]
