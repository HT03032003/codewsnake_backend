import os
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "code_practice.settings")
django.setup()

call_command("migrate")

User = get_user_model()
username = 'admin'
email = 'admin@gmail.com'
password = '12345678'

user, created = User.objects.get_or_create(username=username, defaults={
    'email': email,
})

user.set_password(password)
user.email = email
user.is_superuser = True
user.is_staff = True
user.save()

print("✅ Admin user updated or created:", username, "/", password)
