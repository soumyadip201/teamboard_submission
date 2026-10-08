from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    company_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class KBQuerySerializer(serializers.Serializer):
    search = serializers.CharField(max_length=255, required=True, allow_blank=False, trim_whitespace=True)
