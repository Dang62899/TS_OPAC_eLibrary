from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='normalized_isbn',
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
        migrations.AddIndex(
            model_name='publication',
            index=models.Index(fields=['normalized_isbn'], name='catalog_publication_normisbn_idx'),
        ),
    ]
