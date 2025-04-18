import os
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model
from user.models import Profile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "code_practice.settings")
django.setup()

call_command("migrate")

User = get_user_model()

User.objects.all().delete()
username = 'admin'
email = 'admin@gmail.com'
password = '12345678'

try:
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': email,
    })

    if created:
        print("🆕 User created")
    else:
        print("⚠️ User already exists, updating...")

    user.set_password(password)
    user.email = email
    user.is_superuser = True
    user.is_staff = True
    user.save()

    profile = Profile.objects.create(
        user=user,
        avatar='avatars/admin.jpg',  # Đặt ảnh mặc định
        address=None,  # Giá trị mặc định là None
        phone_number=None  # Giá trị mặc định là None
    )
    profile.save()

    print("✅ Admin user updated or created:", username, "/", password)
except Exception as e:
    print("❌ Error creating admin:", str(e))
