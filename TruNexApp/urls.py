from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    CustomRefreshTokenView,
    logout,
    is_authenticated,
    register,
    get_user_favorites,
    get_user_interests,
    get_full_user_data,
    UpdateUserView,
    get_all_news_articles,
    get_article_detail,
    search_news,
    add_to_favorites,
    remove_from_favorites,
    is_favorite,
    fetch_news_from_api,
    get_articles_by_source,
    # get_notes,
)

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomRefreshTokenView.as_view(), name="token_refresh"),
    path("authenticated/", is_authenticated),
    path("register/", register),
    path("logout/", logout),
    path("update-profile/", UpdateUserView.as_view(), name="update_profile"),
    # -----------------------------------
    path("interests/", get_user_interests),
    path("data/", get_full_user_data),
    path("news/", get_all_news_articles, name="get_all_news_articles"),
    path("news/<int:article_id>/", get_article_detail),
    path("news/search/", search_news),
    # -----------------------------------
    path("favorites/add/", add_to_favorites),
    path("favorites/remove/<int:article_id>/", remove_from_favorites),
    path("favorites/", get_user_favorites),
    path("favorites/check/<int:article_id>/", is_favorite),
    # -----------------------------------
    # -----------------------------------
    path("articles/source/<int:source_id>/", get_articles_by_source),
    path("fetch-news/", fetch_news_from_api),
    # -----------------------------------
    # # -----------------------------------
    # path("notes/", get_notes),
]

# -----------------------------------------------------------------------------
