from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ShortURL",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("long_url", models.URLField(max_length=2048)),
                (
                    "short_code",
                    models.CharField(
                        max_length=50,
                        unique=True,
                        validators=[django.core.validators.RegexValidator(regex="^[A-Za-z0-9_-]+$", message="Use only letters, numbers, hyphens, and underscores.")],
                    ),
                ),
                ("click_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "constraints": [models.UniqueConstraint(fields=("short_code",), name="unique_short_code")],
            },
        ),
    ]
