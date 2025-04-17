from django.urls import path
from .views import *

urlpatterns = [
    # Các URL khác
    path('posts/create/', create_post, name='create_post'),
    path('posts/', get_posts, name='get_posts'),
    path('post/<int:id>/', get_post, name='post'),
    path('post/<int:post_id>/comment/create/', create_comment, name='create_comment'),
    path('post/<int:post_id>/vote/', post_vote, name='post-vote'),
]
