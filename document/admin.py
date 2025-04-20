from django.contrib import admin
from .models import Document, Question, Choice

# Register your models here.
admin.site.register(Document)
admin.site.register(Question)
admin.site.register(Choice)