from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_start_reservations_pending'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='rejection_reason',
            field=models.TextField(blank=True, default=''),
        ),
    ]
