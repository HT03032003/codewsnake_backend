from django.urls import path
from .views import *

urlpatterns = [
    path("stats/", get_admin_stats),
    path('users/', get_users, name='user-list'),
    path("users/<int:user_id>/", get_user_detail, name="get_user_detail"),
    path("users/delete/<int:user_id>/", delete_user, name="delete_user"),
    path("users/update/<int:user_id>/", update_user, name="update_user"),
    path("document/create/", create_document, name="create_document"),
    path("document/<int:document_id>/", get_document, name="get_document"),
    path("document/update/<int:document_id>/", update_document, name="update_document"),
    path("document/<int:id>/questions/", get_questions, name="questions"),
    path("document/<int:id>/question/create/", create_question, name="create_question"),
    path("question/<int:question_id>/", get_question, name="question"),
    path("question/update/<int:question_id>/", update_question, name="update_question"),
    path("exercise/create/", create_exercise, name="create_exercise"),
    path("exercise/<int:exercise_id>/", get_exercise, name="get_exercise"),
    path("exercise/update/<int:exercise_id>/", update_exercise, name="update_exercise"),
    path("posts/", get_posts, name="admin_get_post"),
    path("post/<int:post_id>/", get_post_detail, name="get_post_detail"),
    path("post/delete/<int:post_id>/", delete_post, name="delete_post"),
    path("post/update/<int:post_id>/", update_post, name="update_post"),
    path("comments/<int:comment_id>/delete/", delete_comment, name="delete_comment"),
]
