from django.db import models
import uuid

class Task(models.Model):
    id = models.CharField(primary_key=True, max_length = 100, default=uuid.uuid4, editable=False)
    summary = models.CharField(max_length=100,null=True, blank=True)
    due = models.DateTimeField(null=True, blank=True)
    freq = models.IntegerField(default=0)
    description = models.TextField(max_length=300,null=True,blank=True)
    
    def __str__(self):
        return self.summary