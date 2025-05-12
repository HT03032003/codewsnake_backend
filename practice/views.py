from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import tempfile
import subprocess
import ast
import openai
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

# Load env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Sử dụng biến môi trường để linh hoạt giữa Windows / Linux
PYTHON_EXECUTABLE = os.getenv('PYTHON_EXECUTABLE', 'python')  # Mặc định là 'python'

def is_code_safe(code):
    ALLOWED_IMPORTS = {'math', 'random', 'datetime', 'numpy'}

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Cấm các loại import không nằm trong whitelist
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in ALLOWED_IMPORTS:
                        return False

            if isinstance(node, ast.ImportFrom):
                if node.module not in ALLOWED_IMPORTS:
                    return False

            # Cấm các lệnh gọi hàm nguy hiểm
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'compile', 'open', '__import__', 'globals', 'locals']:
                        return False

        return True
    except Exception as e:
        print("AST parsing error:", e)
        return False

@csrf_exempt
@api_view(['POST'])
def run_code(request):
    try:
        body = json.loads(request.body)
        code = body.get("code", "")
        inputs = body.get("inputs", [])
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid input"}, status=400)

    if not code:
        return JsonResponse({"error": "No code provided"}, status=400)

    if not is_code_safe(code):
        return JsonResponse({"output": "❌ERROR!"}, status=400)

    try:
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name
    except Exception as e:
        return JsonResponse({"output": f"Lỗi khi tạo file tạm: {str(e)}"}, status=500)

    try:
        input_data = '\n'.join(inputs)
        result = subprocess.run(
            [PYTHON_EXECUTABLE, tmp_path],
            input=input_data.encode(),
            capture_output=True,
            timeout=3
        )
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()

        if stderr:
            return JsonResponse({
                "output": stdout + "\n" + stderr,
                "requiresInput": False
            }, status=400)

        return JsonResponse({
            "output": stdout,
            "requiresInput": False
        }, status=200)
    except subprocess.TimeoutExpired:
        return JsonResponse({
            "output": "⏰ Mã chạy quá lâu hoặc có vòng lặp vô hạn.",
            "requiresInput": False
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "output": f"⚠️ Lỗi không xác định: {str(e)}",
            "requiresInput": False
        }, status=500)
    finally:
        os.remove(tmp_path)

@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def correct_code(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            code_to_correct = body.get('code', '')
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid input"}, status=400)

        if not code_to_correct:
            return JsonResponse({"error": "No code provided"}, status=400)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Please correct the following Python code and add error comments directly below each line that contains a mistake. "
                        f"The comments should describe the specific error that was corrected. Return the complete corrected code block:\n\n{code_to_correct}"
                    )
                }]
            )
            corrected_code = response['choices'][0]['message']['content'].strip()
            return JsonResponse({"corrected_code": corrected_code}, status=200)
        except openai.error.OpenAIError as e:
            return JsonResponse({"error": f"OpenAI API Error: {str(e)}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
