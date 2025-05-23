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

ALLOWED_MODULES = {
    "math", "random", "datetime", "time", "string", "re",
    "collections", "itertools", "functools", "statistics"
}
FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "shutil", "threading", "multiprocessing", "socket", "http", "requests", "ftplib"
}

def check_imports_safe(code):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split('.')[0]
                    if mod in FORBIDDEN_MODULES:
                        return False, f"Import of module '{mod}' is not allowed."
                    if mod not in ALLOWED_MODULES:
                        return False, f"Module '{mod}' is not in allowed list."
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or '').split('.')[0]
                if mod in FORBIDDEN_MODULES:
                    return False, f"Import of module '{mod}' is not allowed."
                if mod not in ALLOWED_MODULES:
                    return False, f"Module '{mod}' is not in allowed list."
        return True, ""
    except Exception as e:
        return False, f"Failed to parse code for import check: {e}"

def check_no_infinite_loop(code):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Tìm while True
            if isinstance(node, ast.While) and isinstance(node.test, ast.Constant):
                if node.test.value is True:
                    return False, "Infinite while loop is not allowed."
        return True, ""
    except Exception as e:
        return False, f"Failed to parse code for infinite loop check: {e}"

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
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            code_to_run = body.get("code", "")
            user_inputs = body.get("inputs", [])
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid input"}, status=400)

        if not code_to_run:
            return JsonResponse({"error": "No code provided"}, status=400)

        # Check imports
        ok, err = check_imports_safe(code_to_run)
        if not ok:
            return JsonResponse({"output": "", "error": err, "requiresInput": False}, status=400)
        # Check infinite loop
        ok, err = check_no_infinite_loop(code_to_run)
        if not ok:
            return JsonResponse({"output": "", "error": err, "requiresInput": False}, status=400)

        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        input_counter = 0

        def input_mock(prompt=""):
            nonlocal input_counter
            if input_counter < len(user_inputs):
                user_input = user_inputs[input_counter]
                input_counter += 1
                return user_input
            else:
                raise ValueError("Input required but not provided")

        # --- Thêm custom import ---
        def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
            root_mod = name.split('.')[0]
            if root_mod not in ALLOWED_MODULES:
                raise ImportError(f"Import of module '{root_mod}' is not allowed.")
            return __import__(name, globals, locals, fromlist, level)
        # --------------------------

        allowed_builtins = {
            '__import__': custom_import,
            'print': print,
            'input': input_mock,
            'range': range,
            'len': len,
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'enumerate': enumerate,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'zip': zip,
            'sorted': sorted,
        }
        safe_globals = {
            '__builtins__': allowed_builtins,
        }
        # Cho phép các thư viện an toàn đã kiểm tra
        for mod in ALLOWED_MODULES:
            try:
                safe_globals[mod] = __import__(mod)
            except ImportError:
                pass  # Nếu module không có, bỏ qua

        try:
            exec(code_to_run, safe_globals)
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
        finally:
            sys.stdout = sys.__stdout__

        output = output_buffer.getvalue()
        return JsonResponse({
            "output": output,
            "requiresInput": False
        })
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
