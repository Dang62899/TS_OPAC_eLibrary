from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_alter_attachment_id_alter_downloadotp_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="attachment",
            name="unit",
            field=models.CharField(blank=True, max_length=128),
        ),
    ]