from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255)  # Tiêu đề
    slug = models.SlugField(unique=True)  # Để tạo URL đẹp
    content = models.TextField()  # Lưu nội dung tài liệu (HTML hoặc Markdown)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    document = models.ForeignKey(Document, related_name='questions', on_delete=models.CASCADE)
    content = models.TextField()  # Nội dung câu hỏi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content[:50]


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    content = models.CharField(max_length=255)  # Nội dung đáp án
    is_correct = models.BooleanField(default=False)  # Có phải đáp án đúng không
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content