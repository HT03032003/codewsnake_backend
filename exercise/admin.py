from django.contrib import admin
from .models import Exercise, UserExerciseProgress

# Register your models here.
admin.site.register(Exercise)
admin.site.register(UserExerciseProgress)