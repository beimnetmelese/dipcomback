from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_location_tin_and_removal'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='rejection_reason',
            field=models.TextField(blank=True, default=''),
        ),
    ]
