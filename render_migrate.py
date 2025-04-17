import os
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "code_practice.settings")
django.setup()

call_command("migrate")

User = get_user_model()
if not User.objects.filter(username='adminCodewSnake').exists():
    user = User.objects.create_superuser(
        username='adminCodewSnake',
        email='admincodewsnake@gmail.com',
        password='12345678'
    )
    print("✅ Admin user created: adminCodewSnake / 12345678")
