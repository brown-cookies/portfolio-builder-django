from .models import Project, Page

from rest_framework import serializers

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'