from django.apps import AppConfig

class RegisterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'register'

    def ready(self):
        import register.signals  # This will register the signals when the app is ready
