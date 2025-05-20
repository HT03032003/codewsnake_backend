from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('profile/update/', update_profile, name='update-profile'),
    path('profile/', profile_view, name='profile'), 
    path("exercise-progress/", exercise_progress_summary, name="exercise-progress"),
    path("exercise-list/", user_exercise_list, name="exercise-list"),
]