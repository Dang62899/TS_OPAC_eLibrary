from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_add_attachments_and_logs"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="research_year",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="publication",
            name="research_class",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
