from django.db import migrations, models


def forwards_map_statuses(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')

    status_map = {
        'active': 'reserve',
        'removed': 'pending',
        'delivered': 'delivered',
    }

    for old_status, new_status in status_map.items():
        Reservation.objects.filter(status=old_status).update(status=new_status)


def backwards_map_statuses(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')

    status_map = {
        'reserve': 'active',
        'pending': 'removed',
        'approved': 'delivered',
        'delivered': 'delivered',
    }

    for old_status, new_status in status_map.items():
        Reservation.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
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
                    ('delivered', 'Delivered'),
                ],
                default='reserve',
                max_length=20,
            ),
        ),
    ]
