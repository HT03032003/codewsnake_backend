from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import openai
import io
import sys
import traceback
import os
import ast
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

# Load .env
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


def is_code_safe(code):
    """
    Kiểm tra mã có chứa import nguy hiểm hoặc gọi hàm độc hại không
    """
    ALLOWED_IMPORTS = {'math', 'random', 'datetime'}

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in ALLOWED_IMPORTS:
                        return False

            if isinstance(node, ast.ImportFrom):
                if node.module not in ALLOWED_IMPORTS:
                    return False

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'compile', 'open', '__import__', 'globals', 'locals', 'os', 'system']:
                        return False
        return True
    except Exception:
        return False


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


@csrf_exempt
def run_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        body = json.loads(request.body)
        code_to_run = body.get("code", "")
        user_inputs = body.get("inputs", [])
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid input"}, status=400)

    if not code_to_run:
        return JsonResponse({"error": "No code provided"}, status=400)

    if not is_code_safe(code_to_run):
        return JsonResponse({"output": "❌ Mã chứa thao tác không an toàn."}, status=400)

    output_buffer = io.StringIO()
    sys.stdout = output_buffer
    input_counter = 0

    def input_mock(prompt=""):
        nonlocal input_counter
        if input_counter < len(user_inputs):
            val = user_inputs[input_counter]
            input_counter += 1
            return val
        else:
            raise ValueError("Input required but not provided")

    try:
        safe_globals = {"__builtins__": {"print": print, "range": range, "len": len, "int": int, "str": str, "float": float, "input": input_mock}}
        exec(code_to_run, safe_globals)
        output = output_buffer.getvalue()
        sys.stdout = sys.__stdout__
        return JsonResponse({
            "output": output,
            "requiresInput": False
        }, status=200)

    except ValueError as e:
        output = output_buffer.getvalue()
        sys.stdout = sys.__stdout__
        return JsonResponse({
            "output": output,
            "requiresInput": True,
            "inputRequestIndex": input_counter
        }, status=200)

    except Exception as e:
        output = output_buffer.getvalue()
        sys.stdout = sys.__stdout__
        return JsonResponse({
            "output": output + f"\nError: {str(e)}\n" + traceback.format_exc(),
            "requiresInput": False
        }, status=400)
