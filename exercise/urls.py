from django.urls import path
from .views import  *

urlpatterns = [
    path('get_exercises/', get_all_exercises, name='get_exercises'),
    path('public_exercises/', get_exercises, name='public_exercises'),
    path('<int:id>/', get_exercise_detail, name='exercise-detail'),
    path('check-code/<int:exercise_id>/', check_user_code, name='check-user-code'),
]
