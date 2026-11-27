from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0011_attachment_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="attachment",
            name="download_password_hash",
            field=models.CharField(blank=True, editable=False, max_length=256),
        ),
    ]