from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Profile
from exercise.models import UserExerciseProgress, Exercise
from .serializers import *
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
from cloudinary.uploader import upload

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(username=user.username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        print(user.username, "-" ,user.is_superuser)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Login successful',
            'userId': user.id,
            'username': user.username,
            'isAdmin': user.is_superuser
        })
    else:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            # Kiểm tra sự tồn tại của username và email
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            # Tạo người dùng mới
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # Tạo profile mặc định cho người dùng mới
            profile = Profile.objects.create(
                user=user,
                avatar='https://res.cloudinary.com/duhbjegyn/image/upload/v1745568160/CodewSnake/avatars/qemhkjphxh5r6nc58jcw.jpg',  # Đặt ảnh mặc định
                address=None,  # Giá trị mặc định là None
                phone_number=None  # Giá trị mặc định là None
            )
            profile.save()

            return JsonResponse({'success': 'User registered successfully'}, status=201)

        except Exception as e:
            return JsonResponse({'error': 'An error occurred: {}'.format(str(e))}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)

        total_completed = UserExerciseProgress.objects.filter(user=user, is_completed=True).count()
        total_incompleted = UserExerciseProgress.objects.filter(user=user, is_completed=False).count()

        # Serialize dữ liệu
        serializer = UserProfileSerializer({
            'user': user,
            'profile': profile,
            'completed': total_completed,
            'incompleted': total_incompleted
        })

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Profile.DoesNotExist:
        return Response({"message": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'PUT'])
def update_profile(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        if 'username' in request.data:
            user.username = request.data['username']
            user.save()

        avatar = request.FILES.get('avatar')
        if avatar:
            print(avatar)
            result = upload(avatar, folder='CodewSnake/avatars')
            profile.avatar = result['secure_url']  # Lưu URL từ Cloudinary

        profile.address = request.data.get('address', profile.address)
        profile.phone_number = request.data.get('phone_number', profile.phone_number)
        profile.save()

        return Response({'message': 'Cập nhật thông tin thành công!', 'avatar': profile.avatar})

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    try:
        profile = Profile.objects.get(user=user)

        total_completed = UserExerciseProgress.objects.filter(user=user, is_completed=True).count()
        total_incompleted = UserExerciseProgress.objects.filter(user=user, is_completed=False).count()

        # Serialize dữ liệu
        serializer = UserProfileSerializer({
            'user': user,
            'profile': profile,
            'completed': total_completed,
            'incompleted': total_incompleted
        })

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Profile.DoesNotExist:
        return Response({"message": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def exercise_progress_summary(request):
    user = request.user
    total = Exercise.objects.count()
    done = UserExerciseProgress.objects.filter(user=user, is_completed=True).count()
    not_done = total - done
    percent = (done / total * 100) if total > 0 else 0

    return Response({
        "done": done,
        "not_done": not_done,
        "percent": round(percent, 2)
    })

# Django
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_exercise_list(request):
    user = request.user
    exercises = Exercise.objects.all()
    print(exercises)
    progress = UserExerciseProgress.objects.filter(user=user)
    done_ids = progress.filter(is_completed=True).values_list('exercise_id', flat=True)

    result = [{
        "title": ex.question_text,
        "difficulty": ex.difficulty,
        "status": "Đã làm" if ex.id in done_ids else "Chưa làm"
    } for ex in exercises]

    return Response(result)
