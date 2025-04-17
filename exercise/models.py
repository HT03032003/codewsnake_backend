from django.db import models
from django.contrib.auth.models import User
# Đây là model đại diện cho mỗi bài tập.
class Exercise(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    difficulty = models.CharField(max_length=50)  # Dễ, Trung bình, Khó
    question_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def get_point_value(self):
        if self.difficulty.lower() == "dễ":
            return 5
        elif self.difficulty.lower() == "trung bình":
            return 10
        elif self.difficulty.lower() == "khó":
            return 15
        return 0

    def __str__(self):
        return self.title

class UserExerciseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    is_unlocked = models.BooleanField(default=True)  
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'exercise')

    def __str__(self):
        return f"{self.user.username} - {self.exercise.title}"