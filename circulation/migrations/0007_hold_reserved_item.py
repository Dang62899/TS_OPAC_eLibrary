from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0011_attachment_tags"),
        ("circulation", "0006_notificationpreference_systemhealth_activitylog_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="hold",
            name="reserved_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reserved_for_holds",
                to="catalog.item",
            ),
        ),
    ]