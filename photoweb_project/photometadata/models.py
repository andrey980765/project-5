from django.db import models
class PhotoMetadata(models.Model):
    title = models.CharField(max_length=200)
    photographer = models.CharField(max_length=200)
    date_taken = models.DateField()
    url = models.URLField()
    description = models.TextField()
    location = models.CharField(max_length=200)
    tags = models.TextField(blank=True)   # храню как CSV
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    camera = models.CharField(max_length=200)
    license = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # уникальность можно не ставить на уровне БД, проверяем в коде (даёт гибкость)
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.date_taken})"
# Create your models here.
