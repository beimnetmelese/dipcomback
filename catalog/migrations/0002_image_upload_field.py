from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image_url',
            field=models.ImageField(blank=True, max_length=500, null=True, upload_to='catalog/'),
        ),
        migrations.AlterField(
            model_name='sellerproduct',
            name='image_url',
            field=models.ImageField(blank=True, max_length=500, null=True, upload_to='catalog/'),
        ),
    ]
