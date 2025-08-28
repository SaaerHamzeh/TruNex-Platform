import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from .scraper_fetcher import (
    extract_keywords,
    infer_article_type,
)  # لإضافة نوع المقال والكلمات المفتاحية


def fetch_from_rss(source):
    try:
        feed = feedparser.parse(source.news_source_url)
        articles = []

        for entry in feed.entries[:10]:
            title = entry.title
            content_html = entry.get("summary", "") or entry.get("content", [{}])[
                0
            ].get("value", "")
            published_at = None

            # 📅 تاريخ النشر
            if hasattr(entry, "published_parsed"):
                published_at = datetime(*entry.published_parsed[:6])

            # 🖼️ استخراج صورة إذا موجودة
            soup = BeautifulSoup(content_html, "html.parser")
            img_tag = soup.find("img")
            image = img_tag.get("src") if img_tag else None

            # 🔑 كلمات مفتاحية
            keywords = extract_keywords(title + " " + soup.get_text())

            # 🧠 نوع المقال (سياسة، صحة، رياضة..)
            article_type = infer_article_type(title)

            # 🖋️ الرابط (مهم جدًا لو بدك تزوره لاحقًا)
            link = entry.get("link", None)

            articles.append(
                {
                    "title": title,
                    "content": soup.get_text(),
                    "keywords": keywords,
                    "image": image,
                    "published_at": published_at,
                    "type": article_type,
                    "category": None,
                    "url": link,
                }
            )

        return articles

    except Exception as e:
        print(f"[RSS ERROR] {source.news_source_name}: {e}")
        return []
