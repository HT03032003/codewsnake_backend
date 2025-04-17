from django.urls import path
from .views import run_code, correct_code

urlpatterns = [
    path('run_code/', run_code, name='run_code'),
    path('correct_code/', correct_code, name='correct_code'),
]
