from rest_framework import serializers
from django.contrib.auth.models import User
from user.models import Profile
from document.models import Document

class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.URLField()

    class Meta:
        model = Profile
        fields = ['avatar', 'address', 'phone_number']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser", "profile"]

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'slug', 'content', 'created_at']