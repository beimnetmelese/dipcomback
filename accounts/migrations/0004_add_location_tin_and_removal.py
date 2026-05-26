from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_seller_discount_percent"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="location",
            field=models.CharField(default="Addis Ababa", max_length=255),
        ),
        migrations.AddField(
            model_name="user",
            name="tin_number",
            field=models.CharField(default="000000000", max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="is_removed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="removal_reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="user",
            name="removed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
