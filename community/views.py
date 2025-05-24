from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Post, Comment, Vote
from .serializers import PostSerializer, CommentSerializer
import random
from cloudinary.uploader import upload

@api_view(['GET'])
def get_posts(request):
    try:
        posts = list(Post.objects.all())
        random.shuffle(posts)
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    data = request.data.copy()
    image = request.FILES.get('image')
    if image:
        result = upload(image, folder='CodewSnake/posts')
        data['image'] = result['secure_url']
    serializer = PostSerializer(data=data)
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response({'message': 'Tạo bài viết thành công!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_post(request, id):
    try:
        post = Post.objects.get(id=id)
        # Lấy tất cả comment gốc (parent=None)
        comments = Comment.objects.filter(post=post, parent=None).order_by('created_at')
        comments_serializer = CommentSerializer(comments, many=True)
        upvotes = Vote.objects.filter(post=post, vote_type=1).count()
        downvotes = Vote.objects.filter(post=post, vote_type=-1).count()
        data = {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'image': post.image if post.image else None,
            'author': post.author.username,
            'comments': comments_serializer.data,  # Dạng tree
            'upvotes': upvotes,
            'downvotes': downvotes
        }
        return Response(data)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    data = request.data.copy()
    data["post"] = post.id
    data["author"] = request.user.id
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_vote(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    vote_type = int(request.data.get('vote_type', 0))
    existing_vote = Vote.objects.filter(user=user, post=post).first()
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            existing_vote.delete()
            return Response({"message": "Vote removed"}, status=status.HTTP_200_OK)
        existing_vote.vote_type = vote_type
        existing_vote.save()
        return Response({"message": "Vote updated"}, status=status.HTTP_200_OK)
    Vote.objects.create(user=user, post=post, vote_type=vote_type)
    return Response({"message": "Vote added"}, status=status.HTTP_200_OK)
