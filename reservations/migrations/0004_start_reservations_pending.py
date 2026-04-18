from django.db import migrations, models


def forwards_map_statuses(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')
    Reservation.objects.filter(status='reserve').update(status='pending')


def backwards_map_statuses(apps, schema_editor):
    Reservation = apps.get_model('reservations', 'Reservation')
    Reservation.objects.filter(status='pending').update(status='reserve')


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0003_add_rejected_status'),
    ]

    operations = [
        migrations.RunPython(forwards_map_statuses, backwards_map_statuses),
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                    ('delivered', 'Delivered'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
