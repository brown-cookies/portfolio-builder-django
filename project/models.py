from django.db import models

class Project(models.Model):
    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Page(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="pages")
    name = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)