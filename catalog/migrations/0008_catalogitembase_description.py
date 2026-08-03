from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0007_product_hot_deal')]

    operations = [
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='sellerproduct',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
    ]
