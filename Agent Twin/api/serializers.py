"""
Django REST Framework Serializers
"""
from rest_framework import serializers
from .models import WritingStyle, Experience, PersonalInfo, DocumentMemory


class WritingStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingStyle
        fields = '__all__'


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'


class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInfo
        fields = '__all__'


class DocumentMemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentMemory
        fields = '__all__'

