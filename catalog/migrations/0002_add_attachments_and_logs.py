from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attachment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attachment_type", models.CharField(choices=[('presentation', 'Presentation'), ('curriculum', 'Curriculum'), ('unit_briefing', 'Unit Briefing'), ('sop', 'Signed SOP'), ('video', 'Instructional Video'), ('other', 'Other')], default='other', max_length=32)),
                ("file", models.FileField(blank=True, null=True, upload_to='attachments/')),
                ("is_external", models.BooleanField(default=False)),
                ("external_url", models.URLField(blank=True)),
                ("allow_download", models.BooleanField(default=True)),
                ("upload_date", models.DateTimeField(auto_now_add=True)),
                ("year", models.IntegerField(blank=True, null=True)),
                ("class_field", models.CharField(blank=True, max_length=64)),
                (
                    "publication",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='catalog.publication'),
                ),
                (
                    "uploader",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-upload_date"]},
        ),
        migrations.CreateModel(
            name="ViewLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ip_address", models.CharField(max_length=45, blank=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "publication",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.publication'),
                ),
                (
                    "attachment",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.attachment'),
                ),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="DownloadOTP",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("used", models.BooleanField(default=False)),
                (
                    "attachment",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to='catalog.attachment'),
                ),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
