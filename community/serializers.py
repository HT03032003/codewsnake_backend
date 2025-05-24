from rest_framework import serializers
from .models import Post, Comment, Notification

class RecursiveCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_username', 'content', 'parent', 'created_at', 'replies']

    def get_replies(self, obj):
        # Lấy tất cả replies (comment con) của comment hiện tại
        children = obj.replies.all().order_by('created_at')
        if children:
            return RecursiveCommentSerializer(children, many=True).data
        return []

class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_username', 'content', 'parent', 'created_at', 'replies']

    def get_replies(self, obj):
        children = obj.replies.all().order_by('created_at')
        if children:
            return RecursiveCommentSerializer(children, many=True).data
        return []

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'author_username', 'image']

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'sender', 'sender_name', 'post', 'post_title', 'notification_type', 'content', 'is_read', 'created_at']
