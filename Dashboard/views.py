from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.contrib.auth.models import User
from TruNexApp.models import NewsArticle, NewsSource, NewsSourceSectionURL

# from django.shortcuts import redirect, get_object_or_404e
from django.shortcuts import redirect, get_object_or_404

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from TruNexApp.base import fetch_news_from_source
from TruNexApp.news_fetchers import fetch_and_store_news
from TruNexApp.models import (
    NewsArticle,
    NewsSource,
    Interest,
)  # تأكد أنك مستورد Interest
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.cache import cache
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import timedelta


from TruNexApp.realtime_broadcast import (
    push_toggle_state,
    push_updated_settings,
    push_countdown,
    push_log,
)
from django.http import JsonResponse


# ✅ شرط صلاحية الادمن
def admin_required(user):
    return user.is_authenticated and user.is_staff


# ✅ تسجيل دخول الادمن
def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect("dashboard_home")
        else:
            messages.error(
                request, "بيانات الدخول غير صحيحة أو ليس لديك صلاحيات كمسؤول."
            )
    return render(request, "login.html")


# ✅ تسجيل الخروج
def admin_logout_view(request):
    logout(request)
    return redirect("admin_login")


@user_passes_test(admin_required)
def admin_dashboard(request):
    users = User.objects.all()
    links = NewsSource.objects.exclude(news_source_id__isnull=True)
    sources = NewsSource.objects.all()  # ضروري لنموذج البحث

    # ✅ تصفية المقالات حسب مدخلات البحث
    articles = NewsArticle.objects.all()

    title = request.GET.get("title")
    if title:
        articles = articles.filter(
            Q(news_article_title__icontains=title)
            | Q(news_article_keywords__icontains=title)
        )

    source_id = request.GET.get("source_id")
    if source_id:
        articles = articles.filter(news_article_source__news_source_id=source_id)

    type_ = request.GET.get("type")
    if type_:
        articles = articles.filter(news_article_type__icontains=type_)

    published_from = request.GET.get("published_from")
    if published_from:
        articles = articles.filter(news_article_published_at__date__gte=published_from)

    published_to = request.GET.get("published_to")
    if published_to:
        articles = articles.filter(news_article_published_at__date__lte=published_to)

    # ✅ ترتيب حسب الأحدث أولًا
    articles = articles.order_by("-news_article_published_at", "-created_at")

    # ✅ تقسيم الصفحات
    article_page_number = request.GET.get("article_page", 1)
    user_page_number = request.GET.get("user_page", 1)
    link_page_number = request.GET.get("link_page", 1)

    article_paginator = Paginator(articles, 7)
    user_paginator = Paginator(users, 7)
    link_paginator = Paginator(links, 7)
    # _____________________________________________________________________________
    task = PeriodicTask.objects.filter(name="جلب الأخبار تلقائياً").first()
    is_fetching_enabled = task.enabled if task else False
    fetch_status = cache.get("fetching_status", "idle")

    source = (
        NewsSource.objects.exclude(last_fetched_at__isnull=True)
        .order_by("-last_fetched_at")
        .first()
    )
    fetch_interval = source.fetch_interval_minutes if source else 60
    fetch_limit = source.fetch_limit
    last_fetched_at = source.last_fetched_at if source else None
    next_fetch_time = (
        last_fetched_at + timedelta(minutes=fetch_interval) if last_fetched_at else None
    )
    return render(
        request,
        "dashboard.html",
        {
            "users": user_paginator.get_page(user_page_number),
            "articles": article_paginator.get_page(article_page_number),
            "links": link_paginator.get_page(link_page_number),
            "sources": sources,
            # ✅ هذه القيم المطلوبة للـ fetch_control.html:
            "is_fetching_enabled": is_fetching_enabled,
            "fetch_status": fetch_status,
            "fetch_interval": fetch_interval,
            "fetch_limit": fetch_limit,
            "last_fetched_at": last_fetched_at,
            "next_fetch_timestamp": (
                int(next_fetch_time.timestamp() * 1000) if next_fetch_time else None
            ),
        },
    )


@user_passes_test(lambda u: u.is_staff)
def edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")

        # تحديث القيم
        user.username = username
        user.email = email
        user.save()

        messages.success(request, "تم تعديل بيانات المستخدم بنجاح.")
        return redirect("dashboard_home")

    return render(request, "edit_user.html", {"user_obj": user})


@user_passes_test(lambda u: u.is_staff)
def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        if user.is_superuser:
            messages.error(request, "لا يمكن حذف المستخدم الرئيسي (superuser).")
        else:
            user.delete()
            messages.success(request, "تم حذف المستخدم بنجاح.")
        return redirect("admin_dashboard")


# إضافة/تعديل رابط
@user_passes_test(admin_required)
def news_source_form_view(request, source_id=None):
    news_source = (
        get_object_or_404(NewsSource, news_source_id=source_id) if source_id else None
    )

    if request.method == "POST":
        name = request.POST.get("name")
        url = request.POST.get("url")
        desc = request.POST.get("description")
        fetch_limit = request.POST.get("fetch_limit")
        interval = request.POST.get("fetch_interval")
        method = request.POST.get("fetch_method")
        language = request.POST.get("fetch_language")

        # الروابط الفرعية القادمة كقوائم
        section_urls = request.POST.getlist("section_url")
        section_types = request.POST.getlist("section_type")
        section_regions = request.POST.getlist("section_region")

        try:
            fetch_limit = int(fetch_limit)
        except:
            fetch_limit = 10
        try:
            interval = int(interval)
        except:
            interval = 60

        if news_source:
            # تعديل مصدر موجود
            news_source.news_source_name = name
            news_source.news_source_url = url
            news_source.description = desc
            news_source.fetch_limit = fetch_limit
            news_source.fetch_interval_minutes = interval
            news_source.news_source_method = method
            news_source.news_source_language = language
            news_source.save()

            # حذف كل الروابط القديمة
            news_source.section_urls.all().delete()
        else:
            # إنشاء مصدر جديد
            news_source = NewsSource.objects.create(
                news_source_name=name,
                news_source_url=url,
                description=desc,
                fetch_limit=fetch_limit,
                fetch_interval_minutes=interval,
                news_source_method=method,
                news_source_language=language,
            )

        # إضافة الروابط الفرعية الجديدة
        for url, type_, region in zip(section_urls, section_types, section_regions):
            if url.strip():
                NewsSourceSectionURL.objects.create(
                    source=news_source,
                    section_url=url,
                    section_type=type_ or None,
                    section_region=region or None,
                )

        messages.success(request, "✅ تم حفظ المصدر والروابط الفرعية بنجاح.")
        return redirect("dashboard_home")

    return render(request, "news_source_form.html", {"news_source": news_source})


# إضافة/تعديل مقال
@user_passes_test(admin_required)
def news_article_form_view(request, article_id=None):
    article = (
        get_object_or_404(NewsArticle, news_article_id=article_id)
        if article_id
        else None
    )

    sources = NewsSource.objects.all()
    categories = Interest.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        source_id = request.POST.get("source_id")
        type_ = request.POST.get("type")
        content = request.POST.get("content")
        keywords = request.POST.get("keywords")
        category_id = request.POST.get("category_id") or None
        image = request.POST.get("image") or None
        published_at = request.POST.get("published_at") or None

        source = get_object_or_404(NewsSource, news_source_id=source_id)
        category = (
            Interest.objects.filter(interest_id=category_id).first()
            if category_id
            else None
        )

        if article:
            article.news_article_title = title
            article.news_article_source = source
            article.news_article_type = type_
            article.news_article_content = content
            article.news_article_keywords = keywords
            article.news_article_category = category
            article.news_article_image = image
            article.news_article_published_at = published_at
            article.save()
            messages.success(request, "تم تعديل المقال بنجاح.")
        else:
            NewsArticle.objects.create(
                news_article_title=title,
                news_article_source=source,
                news_article_type=type_,
                news_article_content=content,
                news_article_keywords=keywords,
                news_article_category=category,
                news_article_image=image,
                news_article_published_at=published_at,
            )
            messages.success(request, "تمت إضافة المقال بنجاح.")

        return redirect("dashboard_home")

    return render(
        request,
        "news_article_form.html",
        {
            "article": article,
            "sources": sources,
            "categories": categories,
        },
    )


@user_passes_test(admin_required)
def delete_link_view(request, source_id):
    link = get_object_or_404(NewsSource, news_source_id=source_id)
    if request.method == "POST":
        link.delete()
        messages.success(request, "تم حذف الرابط بنجاح.")
    return redirect("dashboard_home")


@user_passes_test(admin_required)
def delete_article_view(request, article_id):
    article = get_object_or_404(NewsArticle, news_article_id=article_id)
    if request.method == "POST":
        article.delete()
        messages.success(request, "تم حذف المقال بنجاح.")
    return redirect("dashboard_home")


@user_passes_test(admin_required)
def delete_multiple_articles_view(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_articles")
        if selected_ids:
            NewsArticle.objects.filter(news_article_id__in=selected_ids).delete()
            messages.success(request, "تم حذف المقالات المحددة بنجاح.")
        else:
            messages.warning(request, "لم يتم تحديد أي مقالات.")
    return redirect("dashboard_home")


# _________________________________________
# _________________________________________


@user_passes_test(admin_required)
@require_POST
def toggle_fetching_status(request):
    schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period="minutes")

    task, created = PeriodicTask.objects.get_or_create(
        name="جلب الأخبار تلقائياً",
        defaults={
            "interval": schedule,
            "task": "TruNexApp.tasks.scheduled_fetch_news",
            "enabled": True,
            "start_time": timezone.now(),
        },
    )

    if not created:
        task.enabled = not task.enabled
        if task.enabled:
            task.start_time = timezone.now()
        task.save()

    # ✅ بث حالة التفعيل/الإيقاف
    push_toggle_state(task.enabled)

    return redirect("dashboard_home")


@user_passes_test(admin_required)
@require_POST
def run_fetch_now(request):
    from TruNexApp.news_fetchers import fetch_and_store_news
    from datetime import datetime, timedelta

    fetch_and_store_news()

    # 🟢 بث العد التنازلي الجديد
    next_time = datetime.utcnow() + timedelta(
        minutes=NewsSource.objects.first().fetch_interval_minutes
    )
    push_countdown(int(next_time.timestamp()))

    # (اختياري) بث Log أو رسالة
    push_log("✅ تم جلب الأخبار يدوياً")

    return JsonResponse({"ok": True})


@user_passes_test(admin_required)
@require_POST
def update_fetch_interval(request):
    try:
        minutes = int(request.POST.get("fetch_interval"))
        fetch_limit = int(request.POST.get("fetch_limit"))

        NewsSource.objects.all().update(
            fetch_interval_minutes=minutes,
            fetch_limit=fetch_limit,
        )

        messages.success(
            request,
            f"✅ تم تعديل الفاصل الزمني إلى {minutes} دقيقة وعدد المقالات إلى {fetch_limit}.",
        )

        # ✅ بث التحديث للجميع
        push_updated_settings(minutes, fetch_limit)

        # تحديث إعدادات Celery
        from TruNexApp.signals import update_celery_interval

        dummy_source = NewsSource.objects.first()
        if dummy_source:
            update_celery_interval(NewsSource, dummy_source)

    except Exception as e:
        messages.error(request, f"❌ فشل تعديل القيم: {e}")

    return redirect("dashboard_home")


# _________________________________________
# _________________________________________
from django.db.models import Count


def dashboard_stats_api(request):
    # 📰 عدد الأخبار الكلي
    total_articles = NewsArticle.objects.count()

    # 📊 توزيع أنواع الأخبار
    type_counts = (
        NewsArticle.objects.values("news_article_type")
        .annotate(count=Count("news_article_id"))
        .order_by("-count")
    )
    type_data = {
        item["news_article_type"] or "unknown": item["count"] for item in type_counts
    }

    # 🌍 توزيع حسب المناطق

    region_counts = (
        NewsArticle.objects.values("news_article_region")
        .annotate(count=Count("news_article_id"))
        .order_by("-count")
    )
    region_data = {
        item["news_article_region"] or "unknown": item["count"]
        for item in region_counts
    }

    # 📉 نسبة الأخبار المزيفة/الحقيقية
    real_count = NewsArticle.objects.filter(news_article_is_fake=False).count()
    fake_count = NewsArticle.objects.filter(news_article_is_fake=True).count()
    unknown_count = NewsArticle.objects.filter(
        news_article_is_fake__isnull=True
    ).count()

    # 💾 أكثر المصادر إنتاجاً للأخبار
    top_sources = NewsSource.objects.annotate(
        article_count=Count("newsarticle")
    ).order_by("-article_count")[:5]
    top_sources_data = {
        source.news_source_name: source.article_count for source in top_sources
    }

    return JsonResponse(
        {
            "total_articles": total_articles,
            "news_types": type_data,
            "regions": region_data,
            "fake_real": {
                "Real": real_count,
                "Fake": fake_count,
                "Unknown": unknown_count,
            },
            "top_sources": top_sources_data,
        }
    )
