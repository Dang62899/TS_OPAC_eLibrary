from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_user_status_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="userstatushistory",
            name="username_snapshot",
            field=models.CharField(default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="userstatushistory",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="status_history",
                to="accounts.user",
            ),
        ),
    ]