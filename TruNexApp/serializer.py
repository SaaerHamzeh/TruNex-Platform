from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل.")
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("كلمتا السر غير متطابقتين.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            is_staff=False,
            is_superuser=False,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class CustomEmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError(
                "يرجى إدخال البريد الإلكتروني وكلمة المرور."
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("البريد الإلكتروني غير موجود.")

        if not user.check_password(password):
            raise serializers.ValidationError("كلمة المرور غير صحيحة.")

        if not user.is_active:
            raise serializers.ValidationError("الحساب غير مفعل.")

        # إنشاء التوكنز يدويًا
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "email", "current_password", "new_password"]

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم من قبل.")
        return value

    def validate(self, data):
        if data.get("new_password"):
            if not data.get("current_password"):
                raise serializers.ValidationError(
                    "يجب إدخال كلمة المرور الحالية لتغيير كلمة المرور."
                )
            user = self.context["request"].user
            if not user.check_password(data["current_password"]):
                raise serializers.ValidationError("كلمة المرور الحالية غير صحيحة.")
        return data

    def update(self, instance, validated_data):
        validated_data.pop("current_password", None)
        new_password = validated_data.pop("new_password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if new_password:
            instance.set_password(new_password)

        instance.save()
        return instance


# ------------------------------------------------------------
class NewsSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsSource
        fields = ["news_source_name", "news_source_url"]


class NewsArticleSerializer(serializers.ModelSerializer):
    news_article_source = NewsSourceSerializer()

    class Meta:
        model = NewsArticle
        fields = [
            "news_article_id",
            "news_article_source",
            "news_article_url",
            "news_article_title",
            "news_article_content",
            "news_article_type",
            "news_article_is_fake",
            "news_article_fake_score",
            "news_article_region",
            "news_article_keywords",
            "news_article_category",
            "news_article_image",
            "news_article_published_at",
            "created_at",
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    news_article = NewsArticleSerializer()

    class Meta:
        model = Favorite
        fields = ["favorite_id", "news_article"]


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ["interest_id", "name"]


class UserInterestSerializer(serializers.ModelSerializer):
    interest = InterestSerializer()

    class Meta:
        model = UserInterest
        fields = ["interest"]


class FullUserSerializer(serializers.ModelSerializer):
    interests = UserInterestSerializer(source="userinterest_set", many=True)
    favorites = FavoriteSerializer(source="favorite_set", many=True)

    class Meta:
        model = User
        fields = ["username", "email", "interests", "favorites"]


# ------------------------------------------------------------
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "description"]
