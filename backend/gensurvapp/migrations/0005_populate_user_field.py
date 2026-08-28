from django.conf import settings
from django.db import migrations


def set_default_user(apps, schema_editor):
    TodoItem = apps.get_model('gensurvapp', 'TodoItem')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    default_user = User.objects.first()  # Assuming the first user is the default
    if default_user:
        TodoItem.objects.filter(user__isnull=True).update(user=default_user)

class Migration(migrations.Migration):

    dependencies = [
        ('gensurvapp', '0003_rename_completed_item_complete'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # NOTE: the AddField for TodoItem.user was dropped here - 0004_todoitem_user
        # (a parallel branch merged in by 0006) already adds the same field, so
        # keeping both raised "column already exists" on a fresh database.
        migrations.RunPython(set_default_user),
    ]
