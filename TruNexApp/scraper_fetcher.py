import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dateutil import parser
from .models import NewsSourceSectionURL
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from django.utils import timezone
import time


def get_section_url(source, target):
    try:
        section = source.section_urls.get(section_type=target)
        return section.section_url
    except:
        return None


def fetch_from_scraper(source, target="main"):

    # ⚙️ تحديد الرابط بناءً على نوع target
    if isinstance(target, NewsSourceSectionURL):
        url = target.section_url
        section_type = target.section_type
        section_region = target.section_region
    else:
        from .scraper_fetcher import get_section_url

        url = get_section_url(source, target) or source.news_source_url
        section_type = target
        section_region = "unknown"

    print(
        f"🧭 Scraping {source.news_source_name} - {section_type or 'main'} - {section_region or 'unknown'} from: {url}"
    )

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        # if "sana.sy" in url:
        #     return scrape_sana_with_selenium(source, override_url=url)
        if "alhadath" in url:
            return scrape_alhadath_with_selenium(source, override_url=url)
        # elif "elsport" in url:
        #     return scrape_elsport(source, override_url=url)
        # elif "syria.tv" in url:
        #     return scrape_syria_tv_with_selenium(source, override_url=url)
        elif "aljazeera" in url:
            return scrape_aljazeera(source)
        # elif "bbc" in url:
        #     return scrape_bbc(soup, source)
        else:
            print(f"⚠️ No custom scraper defined for {url}")
            return []

    except Exception as e:
        print(f"[SCRAPER ERROR] {source.news_source_name}: {e}")
        return []


def infer_article_type(title: str) -> str:
    import re

    # تنظيف العنوان
    title = re.sub(r"[^\w\sء-ي]", "", title.lower())

    CATEGORY_KEYWORDS = {
        "politic": [
            "سياسة",
            "حكومة",
            "رئيس",
            "وزير",
            "رئاسة",
            "انتخابات",
            "دستور",
            "برلمان",
            "مجلس",
            "دولة",
            "زعيم",
            "احتلال",
            "إسرائيل",
            "ترامب",
            "بايدن",
            "معاهدة",
            "صراع",
            "نزاع",
            "سلطة",
            "مرسوم",
            "politics",
            "government",
            "president",
            "minister",
            "parliament",
            "election",
            "constitution",
            "conflict",
            "state",
            "leader",
            "treaty",
            "authority",
            "trump",
            "biden",
            "israel",
        ],
        "sports": [
            "رياضة",
            "دوري",
            "كأس",
            "مباراة",
            "لاعب",
            "منتخب",
            "بطولة",
            "جول",
            "هدف",
            "ركلة",
            "مدرب",
            "شوط",
            "ميسي",
            "رونالدو",
            "برشلونة",
            "ريال",
            "الاتحاد",
            "الهلال",
            "sport",
            "match",
            "game",
            "team",
            "league",
            "championship",
            "goal",
            "player",
            "coach",
            "half",
            "cup",
            "messi",
            "ronaldo",
            "barcelona",
            "madrid",
            "alhilal",
            "ittihad",
        ],
        "health": [
            "صحة",
            "مريض",
            "دواء",
            "دوائية",
            "مستشفى",
            "طبيب",
            "جراحة",
            "لقاح",
            "كورونا",
            "فايروس",
            "مرض",
            "وباء",
            "إصابة",
            "تحاليل",
            "أعراض",
            "نقل دم",
            "عيادة",
            "ضغط",
            "سكري",
            "كوليسترول",
            "إنفلونزا",
            "health",
            "hospital",
            "doctor",
            "surgery",
            "medicine",
            "vaccine",
            "covid",
            "pandemic",
            "virus",
            "infection",
            "disease",
            "symptoms",
            "clinic",
            "test",
            "flu",
            "blood pressure",
            "diabetes",
            "cholesterol",
        ],
        "economy": [
            "اقتصاد",
            "مال",
            "سوق",
            "بورصة",
            "تضخم",
            "عملة",
            "دولار",
            "يورو",
            "ذهب",
            "نفط",
            "أسعار",
            "غلاء",
            "دخل",
            "رواتب",
            "ضرائب",
            "بنك",
            "قرض",
            "تمويل",
            "استثمار",
            "عجز",
            "ميزانية",
            "economy",
            "finance",
            "market",
            "stock",
            "dollar",
            "euro",
            "gold",
            "oil",
            "price",
            "income",
            "salary",
            "bank",
            "loan",
            "budget",
            "investment",
            "deficit",
            "tax",
            "inflation",
            "currency",
        ],
        "education": [
            "تعليم",
            "دراسة",
            "مدرسة",
            "طلاب",
            "امتحان",
            "شهادة",
            "منهاج",
            "علامات",
            "نتائج",
            "نجاح",
            "سنة دراسية",
            "مدرسي",
            "جامعة",
            "دكتوراه",
            "ماجستير",
            "مقرر",
            "تحصيل",
            "اختبار",
            "تعليم عن بعد",
            "education",
            "study",
            "school",
            "student",
            "exam",
            "certificate",
            "grade",
            "result",
            "university",
            "phd",
            "masters",
            "curriculum",
            "distance learning",
            "academic",
            "syllabus",
            "semester",
        ],
        "technology": [
            "تكنولوجيا",
            "تقنية",
            "هاتف",
            "ذكاء اصطناعي",
            "روبوت",
            "برمجيات",
            "تطبيق",
            "برنامج",
            "حاسوب",
            "إنترنت",
            "تشفير",
            "موبايل",
            "برمجة",
            "شبكة",
            "سيليكون",
            "كاميرا",
            "شاشة",
            "معالج",
            "ألعاب",
            "تشات جي بي تي",
            "كود",
            "واقع افتراضي",
            "خوارزمية",
            "technology",
            "tech",
            "ai",
            "artificial intelligence",
            "robot",
            "software",
            "app",
            "program",
            "mobile",
            "internet",
            "encryption",
            "vr",
            "virtual reality",
            "hardware",
            "processor",
            "code",
            "gaming",
            "machine learning",
        ],
        "space": [
            "فضاء",
            "ناسا",
            "قمر",
            "مريخ",
            "مركبة فضائية",
            "مجرة",
            "كوكب",
            "تلسكوب",
            "رائد فضاء",
            "صاروخ",
            "مهمة",
            "space",
            "nasa",
            "moon",
            "mars",
            "galaxy",
            "planet",
            "telescope",
            "rocket",
            "astronaut",
            "mission",
        ],
        "security": [
            "أمن",
            "هجوم",
            "اختراق",
            "قراصنة",
            "تسريب",
            "هجوم إلكتروني",
            "حماية",
            "تشفير",
            "دفاع",
            "مخابرات",
            "تهديد",
            "تفجير",
            "إرهاب",
            "security",
            "cyber",
            "hacking",
            "hacker",
            "breach",
            "leak",
            "cyberattack",
            "defense",
            "encryption",
            "intelligence",
            "terrorism",
        ],
    }

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in title for word in keywords):
            return category

    return "general"


def extract_keywords(text, max_words=7):
    import re
    from collections import Counter

    # تنظيف النص وتحويله إلى حروف صغيرة
    text = re.sub(r"[^\w\sء-ي]", "", text.lower())

    # تجزئة إلى كلمات
    words = re.findall(r"\b[\wء-ي]+\b", text)

    # قائمة كلمات التوقف الموسعة (عربي + إنجليزي)
    stopwords = set(
        [
            # عربية
            "في",
            "من",
            "على",
            "عن",
            "إلى",
            "و",
            "مع",
            "أن",
            "هذا",
            "ما",
            "لم",
            "كان",
            "قد",
            "لا",
            "هو",
            "هي",
            "كما",
            "ذلك",
            "بعد",
            "أو",
            "كل",
            "أي",
            "تم",
            "تكون",
            "قبل",
            "بين",
            "أكثر",
            "أقل",
            "منذ",
            "حتى",
            "حيث",
            "إلا",
            "أحد",
            "أخرى",
            "أمام",
            "لدى",
            "لذلك",
            # إنجليزية
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


# --------------الحدث--------------
def scrape_alhadath_with_selenium(source, override_url=None):

    # ✅ إجبار الذهاب للصفحة الرئيسية فقط
    url = source.news_source_url

    options = Options()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service("D:/chromedriver/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    articles = []

    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        cards = soup.select("li.list-item")
        print(f"🧩 Found {len(cards)} cards in AlHadath")

        for card in cards[:10]:
            try:
                link_tag = card.select_one("a.article-content-wrapper")
                full_link = (
                    urljoin(source.news_source_url, link_tag["href"])
                    if link_tag and link_tag.has_attr("href")
                    else "#"
                )

                title_tag = card.select_one("span.title")
                title = title_tag.get_text(strip=True) if title_tag else "بدون عنوان"

                image_tag = card.select_one("span.img-box img")
                image_url = (
                    urljoin(source.news_source_url, image_tag["src"])
                    if image_tag and image_tag.has_attr("src")
                    else None
                )

                # 📝 نكتفي بالبيانات من الصفحة الرئيسية فقط
                article_content = title
                published_at = None

                articles.append(
                    {
                        "title": title,
                        "content": article_content,
                        "keywords": extract_keywords(title + " " + article_content),
                        "image": image_url,
                        "published_at": published_at,
                        "type": infer_article_type(title),
                        "category": None,
                        "url": full_link,
                    }
                )

            except Exception as e:
                print(f"⚠️ AlHadath card parsing error: {e}")

    except Exception as e:
        print(f"❌ Selenium failed for AlHadath: {e}")

    finally:
        driver.quit()

    return articles


# --------------سانا--------------
def scrape_sana_with_selenium(source, override_url=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    import time

    url = override_url or source.news_source_url

    options = Options()
    options.headless = True
    service = Service("D:/chromedriver/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    articles = []
    try:
        driver.get(url)
        time.sleep(5)  # بمهل ليحمّل الصور والـ JS
        soup = BeautifulSoup(driver.page_source, "html.parser")

        cards = soup.select("article.item-list")

        print(f"🧩 Found {len(cards)} articles in SANA [via Selenium]")

        for card in cards[:5]:
            try:
                title_tag = card.select_one("h2.post-box-title a")
                title = title_tag.get_text(strip=True) if title_tag else "بدون عنوان"
                full_link = (
                    urljoin(source.news_source_url, title_tag["href"])
                    if title_tag
                    else "#"
                )

                image_tag = card.select_one("div.post-thumbnail img")
                image_url = None
                if image_tag and image_tag.has_attr("src"):
                    image_url = urljoin(source.news_source_url, image_tag["src"])

                # افتح صفحة المقال لجلب التفاصيل والتاريخ
                published_at = None
                article_content = title  # افتراضي

                if full_link != "#":
                    try:
                        driver.get(full_link)
                        time.sleep(2)
                        article_soup = BeautifulSoup(driver.page_source, "html.parser")

                        # جلب الفقرات كمحتوى
                        paragraphs = article_soup.select("div.entry p")
                        if paragraphs:
                            article_content = "\n".join(
                                p.get_text(strip=True) for p in paragraphs
                            )

                        # جلب التاريخ
                        from dateutil import parser

                        date_tag = article_soup.select_one("span.tie-date")
                        if date_tag:
                            date_text = date_tag.get_text(strip=True)
                            try:
                                published_at = parser.parse(date_text)
                            except Exception as err:
                                print(f"⚠️ Failed to parse date: {err} — '{date_text}'")
                    except Exception as e:
                        print(f"⚠️ Failed to fetch full article: {e}")

                articles.append(
                    {
                        "title": title,
                        "content": article_content,
                        "keywords": extract_keywords(title + " " + article_content),
                        "image": image_url,
                        "published_at": published_at,
                        "type": infer_article_type(title),
                        "category": None,
                        "url": full_link,
                    }
                )

            except Exception as e:
                print(f"⚠️ SANA card error: {e}")

    except Exception as e:
        print(f"❌ Selenium failed for SANA: {e}")
    finally:
        driver.quit()

    return articles


# --------------الجزيرة--------------
def scrape_aljazeera(source):

    url = source.news_source_url or "https://www.aljazeera.net/"
    print(f"🧭 Scraping Al-Jazeera from main page: {url}")

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"❌ Failed to load Al-Jazeera main page: {e}")
        return []

    cards = soup.select("a.u-clickable-card__link")
    print(f"🧩 Found {len(cards)} cards")

    articles = []
    seen_links = set()

    for i, card in enumerate(cards[:15]):
        try:
            href = card.get("href")
            full_link = urljoin(url, href) if href else None

            if not full_link or full_link in seen_links:
                continue
            seen_links.add(full_link)

            title_tag = card.select_one(
                "h3.article-card__title span"
            ) or card.select_one("h3.article-card__title")
            title = title_tag.get_text(strip=True) if title_tag else "بدون عنوان"
            if not title or title == "بدون عنوان":
                continue

            # جلب صفحة المقال
            try:
                article_res = requests.get(full_link, headers=headers, timeout=10)
                article_soup = BeautifulSoup(article_res.content, "html.parser")

                # ✅ جلب المحتوى
                paragraphs = article_soup.select("div[class*='wysiwyg'] p")
                content = (
                    "\n".join(p.get_text(strip=True) for p in paragraphs)
                    if paragraphs
                    else title
                )

                # ✅ جلب التاريخ
                published_at = None
                date_tag = article_soup.select_one("span.article-dates__published")
                if date_tag:
                    try:
                        published_at = parser.parse(
                            date_tag.get_text(strip=True), dayfirst=True
                        )
                    except:
                        pass

                # ✅ جلب الصورة من صفحة المقال
                image_url = None
                img_tag = article_soup.select_one(
                    "figure img"
                ) or article_soup.select_one("img")
                if img_tag and img_tag.has_attr("src"):
                    image_url = urljoin(full_link, img_tag["src"])

                articles.append(
                    {
                        "title": title,
                        "content": content,
                        "keywords": extract_keywords(title + " " + content),
                        "image": image_url,
                        "published_at": published_at,
                        "type": infer_article_type(title),
                        "category": None,
                        "url": full_link,
                    }
                )
                print(f"✅ Article added: {title}")

            except Exception as e:
                print(f"⚠️ Failed to fetch full article: {e}")

        except Exception as e:
            print(f"⚠️ Error parsing card #{i+1}: {e}")

    print(f"\n🟢 Total articles scraped: {len(articles)}")
    return articles


# --------------BBC--------------scrape_bbc_with_playwright
def scrape_bbc(soup=None, source=None):
    url = source.news_source_url
    print(f"🧭 Scraping BBC main page: {url}")

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"❌ Failed to load BBC main page: {e}")
        return []

    articles = []

    # ✅ عناصر المقالات ضمن روابط /arabic/articles/..
    cards = soup.select("a[href*='/arabic/articles/']")
    print(f"🧩 Found {len(cards)} BBC article links")

    seen_links = set()
    fetch_limit = getattr(source, "fetch_limit", 3)

    for card in cards:
        try:
            full_link = urljoin(url, card["href"])
            if full_link in seen_links:
                continue  # لتجنب التكرار
            seen_links.add(full_link)

            title = card.get_text(strip=True)
            if not title or title == "بدون عنوان":
                print("⛔ Skipping article with no valid title")
                continue

            # جلب صفحة الخبر
            try:
                article_res = requests.get(
                    full_link, headers={"User-Agent": "Mozilla/5.0"}
                )
                article_soup = BeautifulSoup(article_res.content, "html.parser")

                # ✅ المحتوى (article > p أو fallback إلى div > p)
                paragraphs = article_soup.select("article p") or article_soup.select(
                    "div p"
                )
                article_content = (
                    "\n".join(p.get_text(strip=True) for p in paragraphs)
                    if paragraphs
                    else title
                )

                if not paragraphs:
                    print(f"⚠️ No content found in: {full_link}")

                # التاريخ
                published_at = None
                time_tag = article_soup.select_one("time")
                if time_tag and time_tag.has_attr("datetime"):
                    published_at = parser.parse(time_tag["datetime"])

                # الصورة
                image_url = None
                img_tag = article_soup.select_one("figure img")
                if img_tag and img_tag.has_attr("src"):
                    image_url = urljoin(full_link, img_tag["src"])

                # تخزين
                articles.append(
                    {
                        "title": title,
                        "content": article_content,
                        "keywords": extract_keywords(title + " " + article_content),
                        "image": image_url,
                        "published_at": published_at,
                        "type": infer_article_type(title),
                        "category": None,
                        "url": full_link,
                    }
                )
                print(f"✅ Article added: {title}")

                if len(articles) >= fetch_limit:
                    break  # نكتفي بعدد مقالات محدد حسب المصدر

            except Exception as e:
                print(f"⚠️ Failed to fetch article page: {e}")

        except Exception as e:
            print(f"⚠️ BBC card parsing error: {e}")

    print(f"\n🟢 Total articles scraped: {len(articles)}")
    return articles


# --------------elsport--------------
def parse_arabic_datetime(date_str, time_str):
    month_map = {
        "كانون الثاني": "01",
        "شباط": "02",
        "آذار": "03",
        "نيسان": "04",
        "أيار": "05",
        "حزيران": "06",
        "تموز": "07",
        "آب": "08",
        "أيلول": "09",
        "تشرين الأول": "10",
        "تشرين الثاني": "11",
        "كانون الأول": "12",
    }

    for ar_month, num in month_map.items():
        if ar_month in date_str:
            date_str = date_str.replace(ar_month, num)
            break

    # مثال الناتج: "08 06 2025"
    parts = date_str.strip().split()
    if len(parts) >= 3:
        day = parts[-3]
        month = parts[-2]
        year = parts[-1]
        return parser.parse(f"{year}-{month}-{day} {time_str}")
    return None


def scrape_elsport(source, override_url=None):

    url = override_url or source.news_source_url
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"❌ Failed to load Elsport: {e}")
        return []

    articles = []
    cards = soup.select("li.newsfeed-main")
    print(f"🧩 Found {len(cards)} cards on Elsport")

    for card in cards[:10]:
        try:
            link_tag = card.select_one("a.news-title")
            title = link_tag.get_text(strip=True) if link_tag else "بدون عنوان"
            full_link = urljoin(url, link_tag["href"]) if link_tag else "#"

            image_tag = card.select_one("img")
            image_url = (
                urljoin(url, image_tag["src"])
                if image_tag and image_tag.has_attr("src")
                else None
            )

            article_content = title
            published_at = None

            if full_link != "#":
                try:
                    article_res = requests.get(full_link, headers=headers, timeout=10)
                    article_soup = BeautifulSoup(article_res.content, "html.parser")

                    # ✅ جلب الفقرات
                    # ✅ جلب الفقرات
                    # paragraphs = article_soup.select("div.article-text p")
                    paragraphs = article_soup.select("div.articleBody p")

                    if paragraphs:
                        article_content = "\n".join(
                            p.get_text(strip=True) for p in paragraphs
                        )

                    # ✅ جلب التاريخ من div.news-info span
                    # ✅ جلب التاريخ والوقت
                    date_tag = article_soup.select("strong.desktop-date")
                    time_tag = article_soup.select_one("strong.desktop-time")

                    if len(date_tag) >= 1 and time_tag:
                        date_text = date_tag[0].get_text(strip=True)
                        time_text = time_tag.get_text(strip=True)
                        published_at = parse_arabic_datetime(date_text, time_text)

                except Exception as e:
                    print(f"⚠️ Failed to fetch full article: {e}")

            if article_content.strip() == title.strip():
                print(f"⚠️ Warning: Content fallback to title for {title}")

            articles.append(
                {
                    "title": title,
                    "content": article_content,
                    "keywords": extract_keywords(title + " " + article_content),
                    "image": image_url,
                    "published_at": published_at,
                    "type": infer_article_type(title),
                    "category": None,
                    "url": full_link,
                }
            )

        except Exception as e:
            print(f"⚠️ Error parsing Elsport card: {e}")

    return articles


# --------------tishreen--syria-tv-----------
def parse_arabic_date(date_str):
    # أشهر عربية شائعة
    months = {
        "كانون الثاني": "01",
        "شباط": "02",
        "آذار": "03",
        "نيسان": "04",
        "أيار": "05",
        "حزيران": "06",
        "تموز": "07",
        "آب": "08",
        "أيلول": "09",
        "تشرين الأول": "10",
        "تشرين الثاني": "11",
        "كانون الأول": "12",
    }

    import re
    from dateutil import parser

    try:
        match = re.match(r"(\d{1,2})-([^\d]+)-(\d{4})", date_str.strip())
        if match:
            day, ar_month, year = match.groups()
            month = months.get(ar_month.strip(), "01")
            date_fixed = f"{year}-{month}-{day.zfill(2)}"
            return parser.parse(date_fixed)
    except Exception as e:
        print(f"❌ Failed to convert Arabic date: {e}")

    return None


def scrape_syria_tv_with_selenium(source, override_url=None):

    url = override_url or source.news_source_url
    print(f"🧭 Scraping Syria TV with Selenium from: {url}")

    options = Options()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    service = Service("D:/chromedriver/chromedriver.exe")  # 🔁 عدّل إذا عندك مسار آخر
    driver = webdriver.Chrome(service=service, options=options)

    articles = []

    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        cards = soup.select("div.node--type-article")
        print(f"🧩 Found {len(cards)} cards")

        for card in cards[:3]:
            try:
                title_tag = card.select_one("div.field--name-node-title h2 a")
                title = title_tag.get_text(strip=True) if title_tag else "بدون عنوان"
                full_link = urljoin(url, title_tag["href"]) if title_tag else "#"

                image_tag = card.select_one("img.media__image")
                image_url = (
                    urljoin(url, image_tag["src"])
                    if image_tag and image_tag.has_attr("src")
                    else None
                )
                published_at = None
                date_tag = card.select_one("div.field--name-field-published-date")
                if date_tag:
                    raw_date = date_tag.get_text(strip=True)
                    print(f"📅 Raw date: {raw_date}")
                    try:
                        published_at = parse_arabic_date(raw_date)
                        print(f"✅ Parsed date: {published_at}")
                    except Exception as e:
                        print(f"⚠️ Failed to parse date: {e}")

                article_content = title
                try:
                    driver.get(full_link)
                    time.sleep(3)
                    article_soup = BeautifulSoup(driver.page_source, "html.parser")

                    paragraphs = article_soup.select("div.field--name-body p")
                    article_content = "\n".join(
                        p.get_text(strip=True) for p in paragraphs
                    )
                except Exception as e:
                    print(f"⚠️ Failed to fetch full article with Selenium: {e}")

                articles.append(
                    {
                        "title": title,
                        "content": article_content,
                        "keywords": extract_keywords(title + " " + article_content),
                        "image": image_url,
                        "published_at": published_at,
                        "type": infer_article_type(title),
                        "category": None,
                        "url": full_link,
                    }
                )

                print(f"✅ Article added: {title}")

            except Exception as e:
                print(f"⚠️ Card parsing error: {e}")

    except Exception as e:
        print(f"❌ Selenium failed for Syria TV: {e}")

    finally:
        driver.quit()

    return articles
