"""
WSGI config for code_practice project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_practice.settings')

application = get_wsgi_application()

if os.environ.get('RENDER'):
    from code_practice import render_migrate
