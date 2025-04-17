from django.apps import AppConfig

class AdminManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_management'

    def ready(self):
        import admin_management.signals
