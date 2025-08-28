import requests
from datetime import datetime
from rapidfuzz import fuzz


def infer_api_article_type_advanced(
    title: str, section: str = "", abstract: str = "", facets: list = None
) -> str:
    import re

    # جمع المحتوى العام للتمييز
    text = f"{title or ''} {section or ''} {abstract or ''} {' '.join(facets or [])}".lower()

    # جدول التصنيفات مع الكلمات الدلالية
    CATEGORY_KEYWORDS = {
        "politics": [
            "politics",
            "government",
            "president",
            "election",
            "democrat",
            "republican",
            "congress",
            "white house",
        ],
        "sports": [
            "sports",
            "match",
            "football",
            "soccer",
            "nba",
            "mlb",
            "tennis",
            "olympics",
            "goal",
            "game",
        ],
        "health": [
            "health",
            "medicine",
            "vaccine",
            "covid",
            "virus",
            "pandemic",
            "mental health",
            "disease",
            "hospital",
        ],
        "technology": [
            "technology",
            "ai",
            "artificial intelligence",
            "software",
            "app",
            "gadget",
            "internet",
            "robot",
            "machine learning",
        ],
        "economy": [
            "economy",
            "stock",
            "finance",
            "inflation",
            "market",
            "budget",
            "economics",
            "investment",
            "business",
            "dollar",
        ],
        "education": [
            "education",
            "school",
            "university",
            "student",
            "teacher",
            "learning",
            "curriculum",
            "academic",
        ],
        "security": [
            "security",
            "terror",
            "cyber",
            "attack",
            "intelligence",
            "crime",
            "espionage",
            "surveillance",
            "military",
        ],
        "space": [
            "space",
            "nasa",
            "moon",
            "mars",
            "planet",
            "rocket",
            "telescope",
            "astronaut",
            "galaxy",
        ],
    }

    # تقييم تقريبي بالنقاط
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        max_score = max(fuzz.partial_ratio(text, kw) for kw in keywords)
        scores[category] = max_score

    # إرجاع التصنيف الأعلى فوق عتبة معينة
    best_match = max(scores.items(), key=lambda x: x[1])
    if best_match[1] >= 60:
        return best_match[0]

    return "general"


def extract_keywords(text, max_words=7):
    import re
    from collections import Counter

    # تنظيف النص وتحويله إلى حروف صغيرة
    text = re.sub(r"[^\w\sء-ي]", "", text.lower())

    # تجزئة إلى كلمات
    words = re.findall(r"\b[\wء-ي]+\b", text)

    stopwords = set(
        [
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "been",
            "from",
            "not",
            "will",
            "would",
            "can",
            "could",
            "should",
            "you",
            "your",
            "they",
            "their",
            "but",
            "about",
            "what",
            "when",
            "where",
            "which",
            "who",
            "whom",
            "how",
            "why",
            "there",
        ]
    )

    # تصفية الكلمات
    filtered = [word for word in words if word not in stopwords and len(word) > 2]

    # إحصاء التكرار واختيار الأكثر شيوعًا
    most_common = Counter(filtered).most_common(max_words)

    # إرجاعها كسلسلة مفصولة بفواصل
    return ", ".join(word for word, _ in most_common)


# ✅ NewsAPI.org
def fetch_from_newsapi_general(source):
    import requests
    from datetime import datetime
    from .scraper_fetcher import get_section_url

    API_KEY = "e3581d458d1944b7949fc41b74c2f165"
    url = source.news_source_url

    # ⚠️ خذ category و country من section_url إذا موجود
    from urllib.parse import urlparse, parse_qs

    try:
        parsed_url = urlparse(get_section_url(source, target="main") or "")
        query_params = parse_qs(parsed_url.query)
        category = query_params.get("category", [None])[0]
        country = query_params.get("country", ["us"])[0]
    except:
        category = None
        country = "us"

    params = {"apiKey": API_KEY, "pageSize": 10, "country": country}
    if category:
        params["category"] = category

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        results = data.get("articles", [])
        print(f"📥 NewsAPI GENERAL returned {len(results)} raw articles")

        articles = []
        for item in results:
            title = item.get("title")
            if not title:
                continue

            content = item.get("content") or item.get("description") or title
            image = item.get("urlToImage")
            published_at = None
            if item.get("publishedAt"):
                try:
                    published_at = datetime.fromisoformat(
                        item["publishedAt"].replace("Z", "+00:00")
                    )
                except:
                    pass

            articles.append(
                {
                    "title": title,
                    "content": content,
                    "keywords": extract_keywords(title),
                    "image": image,
                    "published_at": published_at,
                    "type": infer_api_article_type_advanced(
                        title,
                        section=item.get("section"),
                        abstract=item.get("abstract"),
                        facets=item.get("des_facet"),
                    ),
                    "category": category,
                    "region": "world",
                    "url": item.get("url"),
                }
            )

        return articles

    except Exception as e:
        print(f"[NewsAPI GENERAL ERROR]: {e}")
        return []


# ✅ New York Times
def fetch_from_nytimes(source):
    print(f"🚀 NYTimes handler running for source: {source.news_source_name}")
    print("🧠 NYT: Start processing")

    API_KEY = "2h0LvM2IkDAiGompBH5Gtiw9nsUjvWVx"  # ⬅️ حط مفتاحك الصحيح هون
    url = source.news_source_url

    try:
        response = requests.get(url, params={"api-key": API_KEY}, timeout=10)
        data = response.json()

        results = data.get("results", [])
        print(f"📥 NYTimes returned {len(results)} raw articles")

        articles = []
        for item in results[:10]:
            title = item.get("title")
            if not title:
                continue

            content = item.get("abstract") or title
            image = None

            multimedia = item.get("multimedia")
            if multimedia and isinstance(multimedia, list) and len(multimedia) > 0:
                image = multimedia[0].get("url")

            published_at = None
            date_str = item.get("published_date")
            if date_str:
                try:
                    published_at = datetime.fromisoformat(date_str)
                except:
                    pass

            articles.append(
                {
                    "title": title,
                    "content": content,
                    "keywords": extract_keywords(title),
                    "image": image,
                    "published_at": published_at,
                    "type": infer_api_article_type_advanced(
                        title,
                        section=item.get("section"),
                        abstract=item.get("abstract"),
                        facets=item.get("des_facet"),
                    ),
                    "category": None,
                    "region": "world",
                    "url": item.get("url"),
                }
            )

        return articles

    except Exception as e:
        print(f"[NYT API ERROR] {source.news_source_name}: {e}")
        return []
