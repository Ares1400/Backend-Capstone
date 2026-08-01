from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="email_verification_token",
        ),
        migrations.AlterField(
            model_name="user",
            name="is_email_verified",
            field=models.BooleanField(default=True),
        ),
    ]
