from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0009_attachment_merge_first_two_pages"),
    ]

    operations = [
        migrations.AddField(
            model_name="attachment",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="attachment",
            name="duration_seconds",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]