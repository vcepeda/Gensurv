from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.contrib.auth.models import User


def set_default_user(apps, schema_editor):
    TodoItem = apps.get_model('gensurvapp', 'TodoItem')
    default_user = User.objects.first()  # Assuming the first user is the default
    if default_user:
        TodoItem.objects.filter(user__isnull=True).update(user=default_user)

class Migration(migrations.Migration):

    dependencies = [
        ('gensurvapp', '0003_rename_completed_item_complete'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='todoitem',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.RunPython(set_default_user),
    ]
