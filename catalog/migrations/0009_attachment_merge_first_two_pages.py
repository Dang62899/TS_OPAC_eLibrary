from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_attachment_unit"),
    ]

    operations = [
        migrations.AddField(
            model_name="attachment",
            name="merge_first_two_pages",
            field=models.BooleanField(default=False),
        ),
    ]