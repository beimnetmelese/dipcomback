from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitecore', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platformsettings',
            name='map_url',
            field=models.URLField(blank=True, max_length=2000),
        ),
    ]