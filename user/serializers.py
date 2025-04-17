from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

# Serializer cho bảng User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_superuser']  # Các trường bạn cần từ bảng User

# Serializer cho bảng Profile
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['address', 'phone_number', 'avatar', 'points']  # Các trường từ bảng Profile

# Serializer kết hợp thông tin từ cả User và Profile
class UserProfileSerializer(serializers.Serializer):
    user = UserSerializer()
    profile = ProfileSerializer()
    completed = serializers.IntegerField()
    incompleted = serializers.IntegerField()

    class Meta:
        fields = ['user', 'profile']
