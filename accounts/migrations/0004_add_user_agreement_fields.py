from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_add_registry_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="agreed_to_terms",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="agreed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
