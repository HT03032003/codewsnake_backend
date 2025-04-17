from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Document, Question
from .serializers import DocumentSerializer, QuestionSerializer
from rest_framework import status

@api_view(['GET'])
def get_documents(request):
    documents = Document.objects.all()
    serializer = DocumentSerializer(documents, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_document_detail(request, slug):
    try:
        document = Document.objects.get(slug=slug)  # Sử dụng slug để tìm tài liệu
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
    except Document.DoesNotExist:
        return Response({"error": "Document not found"}, status=404)

@api_view(['GET'])
def quiz_by_slug(request, slug):
    try:
        document = Document.objects.get(slug=slug)
    except Document.DoesNotExist:
        return Response({"error": "Không tìm thấy tài liệu"}, status=status.HTTP_404_NOT_FOUND)

    questions = Question.objects.filter(document=document)
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)