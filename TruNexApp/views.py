# from django.shortcuts import render, redirect
# from django.contrib.auth.models import User
# from .models import *
# from .serializer import *
from .models import *

from .serializer import (
    NoteSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    UserInterestSerializer,
    FullUserSerializer,
    CustomEmailTokenObtainPairSerializer,
    FavoriteSerializer,
    NewsArticleSerializer,
    InterestSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework.views import APIView


from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from django.db.models import Q


from .news_fetchers import fetch_and_store_news

# ---------------------------------------------


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomEmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(
                {"success": False, "error": e.detail[0]}, status=401  # 🔥 مهم جدا
            )

        tokens = serializer.validated_data

        access_token = tokens["access"]
        refresh_token = tokens["refresh"]

        res = Response(
            {
                "success": True,
                "access": access_token,
                "refresh": refresh_token,
            }
        )

        res.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
        )
        res.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
        )

        return res


class CustomRefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            request.data["refresh"] = refresh_token

            response = super().post(request, *args, **kwargs)
            tokens = response.data

            access_token = tokens["access"]

            res = Response()
            res.data = {"refreshed": True}

            res.set_cookie(
                "access_token",
                access_token,
                httponly=True,
                secure=False,  # ✅ أثناء التطوير
                samesite="Lax",  # ✅ الأفضل أثناء التطوير لتفادي قيود SameSite
                path="/",
            )

            return res
        except:
            return Response({"refreshed": False})


class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UserUpdateSerializer(
            user, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"updated": True})
        return Response(serializer.errors, status=400)


@api_view(["post"])
def logout(request):
    try:
        res = Response()
        res.data = {"success": True}
        res.delete_cookie("access_token", path="/", samesite="None")
        res.delete_cookie("refresh_token", path="/", samesite="None")
        return res
    except:
        return Response({"success": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def is_authenticated(request):
    return Response({"authenticated": True})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)  # 🔧 corrected "error" ➤ "errors"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_full_user_data(request):
    user = request.user
    serializer = FullUserSerializer(user)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_interests(request):
    user = request.user
    interests = UserInterest.objects.filter(user=user)
    serializer = UserInterestSerializer(interests, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_all_news_articles(request):
    articles = NewsArticle.objects.all().order_by("-news_article_id")
    serializer = NewsArticleSerializer(articles, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_article_detail(request, article_id):
    try:
        article = NewsArticle.objects.get(news_article_id=article_id)
        serializer = NewsArticleSerializer(article)
        return Response(serializer.data)
    except NewsArticle.DoesNotExist:
        return Response({"error": "الخبر غير موجود"}, status=404)


# ======================search=========================

from TruNexApp.ai_models.text_to_sql_api import run_nl_query
from TruNexApp.models import NewsArticle, NewsSource
from TruNexApp.serializer import NewsArticleSerializer
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import re


@api_view(["GET"])
@permission_classes([AllowAny])
def search_news(request):
    query = request.GET.get("q", "")
    if not query:
        return Response({"error": "يرجى إدخال عبارة للبحث."}, status=400)

    result = run_nl_query(query)
    print("🔍 SQL:", result["sql"])
    print("🔍 Full Result:", result)

    if result["rejected"]:
        return Response({"error": result.get("error", "الاستعلام غير صالح.")})

    rows = result.get("rows", [])
    if rows:
        ids = [row["news_article_id"] for row in rows]
        articles_map = {
            a.news_article_id: a
            for a in NewsArticle.objects.filter(news_article_id__in=ids)
        }
        ordered_articles = [articles_map[i] for i in ids if i in articles_map]
        serializer = NewsArticleSerializer(ordered_articles, many=True)

        return Response({"results": serializer.data})

    # ✅ إذا ما في نتائج -> عرض روابط المواقع فقط للمستخدم
    sources = NewsSource.objects.all().exclude(news_source_method="api")
    fallback_links = [
        {"source": s.news_source_name, "url": s.news_source_url} for s in sources
    ]

    return Response(
        {
            "results": [],
            "suggested_sources": fallback_links,
            "message": "لم يتم العثور على نتائج، جرّب البحث يدوياً في هذه المواقع.",
        }
    )


# ---------------------favorites-End-points--------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_favorites(request):
    article_id = request.data.get("article_id")
    try:
        article = NewsArticle.objects.get(news_article_id=article_id)
        Favorite.objects.get_or_create(user=request.user, news_article=article)
        return Response({"added": True})
    except NewsArticle.DoesNotExist:
        return Response({"error": "المقال غير موجود"}, status=404)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_favorites(request, article_id):
    try:
        favorite = Favorite.objects.get(user=request.user, news_article_id=article_id)
        favorite.delete()
        return Response({"removed": True})
    except Favorite.DoesNotExist:
        return Response({"error": "المفضلة غير موجودة"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_favorites(request):
    user = request.user
    favorites = Favorite.objects.filter(user=user)
    serializer = FavoriteSerializer(favorites, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def is_favorite(request, article_id):
    exists = Favorite.objects.filter(
        user=request.user, news_article_id=article_id
    ).exists()
    return Response({"is_favorite": exists})


# ------------------------------------------------------
# ------------------fitching--news----------------------
# ------------------------------------------------------


@api_view(["GET"])
@permission_classes([AllowAny])
def fetch_news_from_api(request):
    fetch_and_store_news()
    return Response({"status": "News fetched successfully!"})


@api_view(["GET"])
@permission_classes([AllowAny])
def get_articles_by_source(request, source_id):
    source = get_object_or_404(NewsSource, pk=source_id)
    articles = NewsArticle.objects.filter(news_article_source=source)
    serializer = NewsArticleSerializer(articles, many=True)
    return Response(serializer.data)


# ------------------------------------------------------
# ------------------------------------------------------
# ------------------------------------------------------
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def get_notes(request):
#     user = request.user
#     print(f"User: {user}, type: {type(user)}")
#     notes = Note.objects.filter(owner=user)
#     serializer = NoteSerializer(notes, many=True)
#     return Response(serializer.data)


# --------------------------------------------------------------------------------------------------------
