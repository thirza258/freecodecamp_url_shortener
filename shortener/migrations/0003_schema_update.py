from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("shortener", "0002_redirectevent"),
    ]

    operations = [
        migrations.RenameField(
            model_name="shorturl",
            old_name="long_url",
            new_name="original_url",
        ),
        migrations.AlterField(
            model_name="shorturl",
            name="click_count",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name="shorturl",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="shorturl",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AddField(
            model_name="shorturl",
            name="last_accessed_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="shorturl",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.CreateModel(
            name="ClickEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, db_index=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("referer", models.TextField(blank=True)),
                (
                    "short_url",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="click_events", to="shortener.shorturl"),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
                "indexes": [
                    models.Index(fields=["short_url", "-timestamp"], name="clickevent_short_ts_idx"),
                    models.Index(fields=["-timestamp"], name="clickevent_ts_idx"),
                    models.Index(fields=["ip_address", "-timestamp"], name="clickevent_ip_ts_idx"),
                ],
            },
        ),
        migrations.RemoveConstraint(
            model_name="shorturl",
            name="unique_short_code",
        ),
    ]
