from django.urls import path
from .views import *

urlpatterns = [
    path("login/", admin_login_view, name="admin_login"),
    path("logout/", admin_logout_view, name="admin_logout"),
    path("", admin_dashboard, name="dashboard_home"),
    path("admin/users/edit/<int:user_id>/", edit_user_view, name="edit_user"),
    path("admin/users/delete/<int:user_id>/", delete_user_view, name="delete_user"),
    path("admin/link/", news_source_form_view, name="add_link"),
    path("admin/link/<int:source_id>/", news_source_form_view, name="edit_link"),
    path("admin/article/", news_article_form_view, name="add_article"),
    path(
        "admin/article/<int:article_id>/", news_article_form_view, name="edit_article"
    ),
    path("admin/link/delete/<int:source_id>/", delete_link_view, name="delete_link"),
    path(
        "admin/article/delete/<int:article_id>/",
        delete_article_view,
        name="delete_article",
    ),
    path(
        "admin/article/delete-multiple/",
        delete_multiple_articles_view,
        name="delete_multiple_articles",
    ),
    # =======================================================================================
    # path("admin/fetch-control/", fetch_control_view, name="fetch_control"),
    path("admin/fetch/toggle/", toggle_fetching_status, name="toggle_fetch"),
    path("admin/fetch/now/", run_fetch_now, name="run_fetch_now"),
    path("admin/fetch/update-interval/", update_fetch_interval, name="update_fetch_interval"),
    path("admin/stats/", dashboard_stats_api, name="dashboard_stats_api"),


]
