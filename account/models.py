from paypal.models import Subscription

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    
    pass


class Setting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="setting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)