from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_otp_secret_user_two_factor_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="service_number",
            field=models.CharField(max_length=50, null=True, blank=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="unit",
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="student_class",
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="status",
            field=models.CharField(default="student", max_length=20, choices=[("student", "Student"), ("graduated", "Graduated"), ("alumni", "Alumni")]),
        ),
        migrations.AddField(
            model_name="user",
            name="date_enrolled",
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="date_graduated",
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="photo",
            field=models.ImageField(upload_to="profiles/", null=True, blank=True),
        ),
    ]
