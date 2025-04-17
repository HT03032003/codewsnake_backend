from django.urls import path
from .views import *

urlpatterns = [
    path('get_documents/', get_documents, name="document"),
    path('<slug:slug>/', get_document_detail, name="document_detail"),  # Sử dụng slug thay vì id
    path('quiz/<slug:slug>/', quiz_by_slug, name='quiz-by-slug'),
]
