from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Exercise, UserExerciseProgress
from user.models import Profile
from .serializers import ExerciseSerializer
from django.views import View
from django.http import JsonResponse
import openai

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication


@api_view(['GET'])
def get_exercises(request):
    exercises = Exercise.objects.all()
    serializer = ExerciseSerializer(exercises, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_exercises(request):
    user = request.user
    exercises = Exercise.objects.all()
    serialized_data = []

    for exercise in exercises:
        is_completed = UserExerciseProgress.objects.filter(user=user, exercise=exercise, is_completed=True).exists()
        is_unlocked = UserExerciseProgress.objects.filter(user=user, exercise=exercise, is_unlocked=True).exists()

        # Serialize từng bài và thêm trường `is_completed`
        serialized_ex = ExerciseSerializer(exercise).data
        serialized_ex['is_completed'] = is_completed
        serialized_ex['is_unlocked'] = is_unlocked

        serialized_data.append(serialized_ex)

    return Response(serialized_data)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exercise_detail(request, id):
    user = request.user

    # Lấy bài tập
    try:
        exercise = Exercise.objects.get(id=id)
    except Exercise.DoesNotExist:
        return Response({'error': 'Bài tập không tồn tại'}, status=404)

    # Lấy hoặc tạo Profile
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Response({'error': 'Không tìm thấy hồ sơ người dùng.'}, status=404)

    # Điểm yêu cầu để mở bài tập
    required_points = exercise.get_point_value()

    # Kiểm tra xem user đã có tiến trình với bài này chưa
    progress = UserExerciseProgress.objects.filter(user=user, exercise=exercise).first()

    if progress and progress.is_unlocked:
        # Nếu đã mở bài → trả về dữ liệu
        data = {
            'id': exercise.id,
            'title': exercise.title,
            'description': exercise.description,
            'question_text': exercise.question_text,
            'difficulty': exercise.difficulty,
            'point': required_points,
        }
        return Response(data)

    # Nếu chưa mở → kiểm tra điểm
    if profile.points < required_points:
        return Response({'error': 'Bạn không đủ điểm để mở bài tập này.'}, status=403)

    # Trừ điểm và tạo progress
    profile.points -= required_points
    profile.save()

    UserExerciseProgress.objects.create(
        user=user,
        exercise=exercise,
        is_unlocked=True,
        is_completed=False
    )

    # Trả lại dữ liệu bài tập sau khi mở thành công
    data = {
        'id': exercise.id,
        'title': exercise.title,
        'description': exercise.description,
        'question_text': exercise.question_text,
        'difficulty': exercise.difficulty,
        'point': required_points,
    }
    return Response(data)

@permission_classes([IsAuthenticated])
@api_view(['POST'])
def check_user_code(request, exercise_id):
    user = request.user
    print(user)
    user_code = request.data.get('code')
    try:
        exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
        return Response({'error': 'Bài tập không tồn tại.'}, status=404)

    # Tạo prompt cho OpenAI
    prompt = f"""
        Bạn là một trình chấm bài tự động.

        # Mô tả bài tập:
        {exercise.question_text}

        # Mã người dùng:
        {user_code}

        # Yêu cầu:
        So sánh đoạn mã người dùng với yêu cầu đề bài.

        Hãy kiểm tra:
        - Mã có thực hiện đúng yêu cầu hay không.
        - Không cần chấm điểm chi tiết, chỉ cần xác định đúng/sai.

        # QUAN TRỌNG:
        Chỉ trả lời bằng một trong hai từ: success hoặc failure.
        Không được giải thích, không in thêm nội dung gì khác.

        Ví dụ:
        - Nếu đúng, trả về: success
        - Nếu sai, trả về: failure

        Bây giờ hãy trả lời:
        """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )
        result = response['choices'][0]['message']['content']
        
        if result.strip() == "success":
            profile = Profile.objects.get(user=user)
            progress = UserExerciseProgress.objects.filter(user=user, exercise=exercise).first()

            if progress and not progress.is_completed:
                point = exercise.get_point_value()
                profile.points += point
                profile.save()

                progress.is_completed = True
                progress.save()

        return Response({'result': result.strip()})
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
