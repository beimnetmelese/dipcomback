from django.db import migrations, models


def forwards_map_statuses(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')

    # Keep already rejected-looking rows in rejected bucket when migrating forward.
    Reservation.objects.filter(status='pending', removed_at__isnull=False).update(status='rejected')


def backwards_map_statuses(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')
    Reservation.objects.filter(status='rejected').update(status='pending')


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0002_reservation_status_flow'),
    ]

    operations = [
        migrations.RunPython(forwards_map_statuses, backwards_map_statuses),
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(
                choices=[
                    ('reserve', 'Reserve'),
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                    ('delivered', 'Delivered'),
                ],
                default='reserve',
                max_length=20,
            ),
        ),
    ]
