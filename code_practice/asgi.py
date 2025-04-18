# asgi.py

import os
from django.core.asgi import get_asgi_application
try:
    exec(open("render_migrate.py").read())
except Exception as e:
    print("⚠️ Không thể chạy render_migrate.py:", e)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_practice.settings')

application = get_asgi_application()
