from django.contrib.auth.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_admin_user(sender, **kwargs):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("✅ Admin user created: admin / admin123")
