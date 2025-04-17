from django.contrib.auth.models import User
from django.utils.text import slugify
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.files.storage import FileSystemStorage
from rest_framework.response import Response
from document.models import Document, Question, Choice
from document.serializers import DocumentSerializer
from exercise.models import Exercise
from community.models import Post, Vote, Comment
from exercise.serializers import ExerciseSerializer
from .serializers import UserSerializer
from django.conf import settings
import os

# --------- Dashboard------------------
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_admin_stats(request):
    total_users = User.objects.count()
    total_exercises = Exercise.objects.count()
    total_documents = Document.objects.count()
    total_posts = Post.objects.count()

    return Response({
        "total_users": total_users,
        "total_exercises": total_exercises,
        "total_documents": total_documents,
        "total_posts": total_posts,
    })

# --------- Users ---------------------
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_users(request):
    users = User.objects.all().select_related('profile')  # Lấy user kèm profile
    serializer = UserSerializer(users, many=True, context={"request": request})
    return Response(serializer.data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)
    except User.DoesNotExist:
        return Response({"error": "Không tìm thấy người dùng!"}, status=404)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return Response({"error": "Bạn không có quyền!"}, status=403)
    try:
        user = User.objects.get(id=user_id)
        if user.email == "admin@gmail.com":
            return Response({"error": "Không thể xóa admin!"}, status=403)
        user.delete()
        return Response({"message": "Xóa thành công!"}, status=200)
    except User.DoesNotExist:
        return Response({"error": "Không tìm thấy người dùng!"}, status=404)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if user.email == "admin@gmail.com":
            return Response({"error": "Không thể sửa admin!"}, status=403)
        user.username = request.data.get("username", user.username)
        user.email = request.data.get("email", user.email)
        if request.user.is_superuser:
            user.is_superuser = request.data.get("is_superuser", user.is_superuser)
        user.save()
        return Response({"message": "Cập nhật thành công!"}, status=200)
    except User.DoesNotExist:
        return Response({"error": "Không tìm thấy người dùng!"}, status=404)

# --------- Documents ---------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_document(request):
    title = request.data.get("title")
    content = request.data.get("content")
    if not title or not content:
        return Response({"error": "Không được để trống!"}, status=400)
    slug = slugify(title)
    document = Document.objects.create(title=title, slug=slug, content=content)
    serializer = DocumentSerializer(document)
    return Response(serializer.data, status=201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=200)
    except Document.DoesNotExist:
        return Response({"error": "Không tìm thấy tài liệu!"}, status=404)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_document(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
        document.title = request.data.get("title", document.title)
        document.content = request.data.get("content", document.content)
        document.slug = request.data.get("slug", document.slug)
        document.save()
        return Response({"message": "Cập nhật thành công!"}, status=200)
    except Document.DoesNotExist:
        return Response({"error": "Không tìm thấy tài liệu!"}, status=404)
    
# ------------ Questions ---------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_questions(request):
    questions = Question.objects.select_related('document').all().values(
        'id',
        'content',
        'document__title'  # Lấy tên tài liệu
    )
    return Response(list(questions))

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_question(request, question_id):
    try:
        question = Question.objects.get(id=question_id)
        choices = Choice.objects.filter(question=question).values('id', 'content', 'is_correct')

        data = {
            "id": question.id,
            "content": question.content,
            "choices": list(choices),
        }

        return Response(data, status=200)
    except Question.DoesNotExist:
        return Response({"error": "Không tìm thấy câu hỏi!"}, status=404)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_question(request, question_id):
    try:
        question = Question.objects.get(id=question_id)
        data = request.data

        # Cập nhật nội dung câu hỏi
        question.content = data.get("content", question.content)
        question.save()

        # Lấy danh sách đáp án mới từ request
        new_choices = data.get("choices", [])

        # Danh sách id đáp án gửi từ frontend
        sent_ids = [c["id"] for c in new_choices if isinstance(c.get("id"), int)]

        # Xóa những đáp án cũ không còn nữa
        Choice.objects.filter(question=question).exclude(id__in=sent_ids).delete()

        # Duyệt từng đáp án để cập nhật hoặc tạo mới
        for c in new_choices:
            content = c.get("content", "").strip()
            is_correct = c.get("is_correct", False)

            if not content:
                continue  # Bỏ qua đáp án rỗng

            # Kiểm tra xem đáp án có tồn tại không
            choice = Choice.objects.filter(question=question, id=c.get("id")).first()

            if choice:
                # Cập nhật đáp án cũ
                choice.content = content
                choice.is_correct = is_correct
                choice.save()
            else:
                # Tạo mới đáp án nếu không tồn tại
                Choice.objects.create(
                    question=question,  # Cần truyền question vào
                    content=content,    # Cần truyền nội dung đáp án vào
                    is_correct=is_correct  # Cần xác định đáp án đúng hay sai
                )

        return Response({"message": "Cập nhật thành công!"})

    except Question.DoesNotExist:
        return Response({"error": "Không tìm thấy câu hỏi"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# --------- Exercises ---------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_exercise(request):
    serializer = ExerciseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_exercise(request, exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        serializer = ExerciseSerializer(exercise)
        return Response(serializer.data, status=200)
    except Exercise.DoesNotExist:
        return Response({"error": "Không tìm thấy bài tập!"}, status=404)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_exercise(request, exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        serializer = ExerciseSerializer(exercise, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
    except Exercise.DoesNotExist:
        return Response({"error": "Không tìm thấy bài tập!"}, status=404)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_exercise(request, exercise_id):
    try:
        exercise = Exercise.objects.get(id=exercise_id)
        exercise.delete()
        return Response({"message": "Xóa thành công!"}, status=200)
    except Exercise.DoesNotExist:
        return Response({"error": "Không tìm thấy bài tập!"}, status=404)
    
# ------------ Posts ---------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posts(request):
    posts = Post.objects.all()
    data = []

    for post in posts:
        upvotes = Vote.objects.filter(post=post, vote_type=1).count()
        downvotes = Vote.objects.filter(post=post, vote_type=-1).count()
        comment_count = Comment.objects.filter(post=post).count()

        post_data = {
            "id": post.id,
            "title": post.title,
            "author": post.author.username,
            "content": post.content,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "comment_count": comment_count,
        }
        data.append(post_data)

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_detail(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        comments = Comment.objects.filter(post=post)

        post_data = {
            "id": post.id,
            "title": post.title,
            "author": post.author.username,
            "content": post.content,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "upvotes": Vote.objects.filter(post=post, vote_type=1).count(),
            "downvotes": Vote.objects.filter(post=post, vote_type=-1).count(),
            "comments": [
                {
                    "id": c.id,
                    "author": c.author.username,
                    "content": c.content,
                    "created_at": c.created_at,
                } for c in comments
            ]
        }
        return Response(post_data)
    except Post.DoesNotExist:
        return Response({"error": "Bài đăng không tồn tại"}, status=404)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        if request.user == comment.author or request.user.is_staff:
            comment.delete()
            return Response({"message": "Xóa bình luận thành công!"})
        return Response({"error": "Bạn không có quyền xóa bình luận này!"}, status=403)
    except Comment.DoesNotExist:
        return Response({"error": "Bình luận không tồn tại"}, status=404)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        post.delete()
        return Response({"message": "Xóa thành công!"}, status=200)
    except Exercise.DoesNotExist:
        return Response({"error": "Không tìm thấy bài tập!"}, status=404)
    

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)

        # Kiểm tra quyền chỉnh sửa (nếu muốn chỉ tác giả được sửa)
        if post.author != request.user:
            return Response({"error": "Bạn không có quyền chỉnh sửa bài viết này."}, status=403)

        # Cập nhật dữ liệu
        post.title = request.data.get("title", post.title)
        post.content = request.data.get("content", post.content)

        # Nếu có ảnh mới, cập nhật ảnh
        image = request.FILES.get('image')
        if image:
            fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'media/post_images'))
            if fs.exists(image.name):
                fs.delete(image.name)
            filename = fs.save(image.name, image)
            post.image = f"post_images/{filename}"

        post.save()
        return Response({"message": "Cập nhật bài viết thành công!"}, status=200)

    except Post.DoesNotExist:
        return Response({"error": "Không tìm thấy bài viết."}, status=404)
