from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='seller_discount_percent',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=5),
        ),
    ]