from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_attachment_video_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="attachment",
            name="tags",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]