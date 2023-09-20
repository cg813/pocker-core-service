from django.db import models


class Document(models.Model):
    name = models.CharField(max_length=500)
    body = models.TextField()

    def __str__(self):
        return self.name
