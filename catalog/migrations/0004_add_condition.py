from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_category_alter_product_category_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="condition",
            field=models.CharField(default="new", max_length=12),
        ),
        migrations.AddField(
            model_name="sellerproduct",
            name="condition",
            field=models.CharField(default="new", max_length=12),
        ),
    ]
