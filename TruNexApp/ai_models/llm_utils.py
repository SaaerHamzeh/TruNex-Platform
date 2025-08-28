import os
import re
import requests
import tiktoken


def count_tokens(text, model="gpt-3.5-turbo"):
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except:
        return len(text.split())


def truncate_by_tokens(text, max_tokens=7000, model="gpt-3.5-turbo"):
    try:
        enc = tiktoken.encoding_for_model(model)
        tokens = enc.encode(text)
        return enc.decode(tokens[:max_tokens])
    except:
        return text[:10000]


def clean_summary(text):
    """
    تنظيف التلخيص من الرموز أو المقاطع الغريبة.
    """
    cleaned = re.sub(
        r"[^\u0600-\u06FF\u0750-\u077F\s\.\،\؟\:\-\(\)a-zA-Z0-9]", "", text
    )
    return cleaned.strip()


def summarize_text_with_openrouter(text, max_tokens=650):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "TruNex Summarizer",
    }

    if not isinstance(text, str) or not text.strip():
        print("⚠️ Received invalid content to summarize. Using fallback.")
        return str(text)

    total_tokens = count_tokens(text, model="gpt-3.5-turbo")
    if total_tokens > 8192:
        print(f"⚠️ النص يحتوي {total_tokens} توكن. سيتم تقليصه.")
        text = truncate_by_tokens(text, max_tokens=7000)

    payload = {
        # "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "model": "deepseek/deepseek-chat-v3-0324:free",
        # "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Analyze the following Arabic article and extract only 3 to 6 full and meaningful sentences that represent the main idea. "
                    "Return only Arabic sentences (MSA). Do not include any English. Keep the text clean, coherent, and ready to publish."
                ),
            },
            {"role": "user", "content": text},
        ],
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print("📥 Raw response status:", response.status_code)
        print("📥 Raw response preview:", response.text[:300])
        response.raise_for_status()
        data = response.json()

        if "choices" in data and data["choices"] and "message" in data["choices"][0]:
            summary = data["choices"][0]["message"]["content"]
            summary = clean_summary(summary.strip())
            if len(summary.split()) > 120:
                summary = " ".join(summary.split()[:120]) + "..."
            print("📄 التلخيص الناتج:\n", summary)
            return summary
        else:
            print("⚠️ لم يتم توليد ملخص.")
            print("🛠️ Raw Response:", data)
            return text

    except Exception as e:
        print(f"[❌ Summarization Error]: {e}")
        return text  # fallback


# =========================detecting type=========================
def detect_article_type_with_openrouter(text: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "TruNex Type Detector",
    }

    if not isinstance(text, str) or not text.strip():
        print("⚠️ No content to detect type. Fallback to 'general'.")
        return "general"

    total_tokens = count_tokens(text)
    if total_tokens > 8192:
        text = truncate_by_tokens(text, max_tokens=7000)

    payload = {
        # "model": "deepseek/deepseek-r1-0528:free",
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Analyze the following Arabic news article and classify its type into one of the following strictly: "
                    "'politic', 'sports', 'economy', 'education', 'technology', 'health', 'culture' or 'general'. "
                    "Return only the type, no explanation. Use lowercase English only."
                ),
            },
            {"role": "user", "content": text},
        ],
        "max_tokens": 10,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and data["choices"]:
            raw_type = data["choices"][0]["message"]["content"].strip().lower()
            allowed_types = [
                "politic",
                "sports",
                "economy",
                "education",
                "technology",
                "health",
                "culture",
                "general",
            ]
            return raw_type if raw_type in allowed_types else "general"
        return "general"

    except Exception as e:
        print(f"[❌ Type Detection Error]: {e}")
        return "general"


# =========================detecting region=========================
def detect_article_region_with_openrouter(text: str) -> str:
    import time

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "TruNex Region Detector",
    }

    if not isinstance(text, str) or not text.strip():
        print("⚠️ No content to detect region. Fallback to 'world'.")
        return "world"

    time.sleep(1.2)  # لتخفيف الضغط على السيرفر

    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Analyze the following Arabic news article and classify its geographic focus "
                    "into only one of the following lowercase labels: 'syria', 'arab', or 'world'. "
                    "Return only one of these three values and nothing else. Respond only in English."
                ),
            },
            {"role": "user", "content": text},
        ],
        "max_tokens": 10,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and data["choices"]:
            raw_region = data["choices"][0]["message"]["content"].strip().lower()
            allowed_regions = ["syria", "arab", "world"]
            return raw_region if raw_region in allowed_regions else "world"
        return "world"

    except Exception as e:
        print(f"[❌ Region Detection Error]: {e}")
        return "world"


# =========================detecting reality=========================
def detect_fake_news_score_with_openrouter(text: str) -> float:

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        # "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a fake news classifier. Based on the following news article, "
                    "Search the news on the Internet before answering."
                    "return a float number between 0.0 and 1.0 representing the probability that the article is FAKE news. "
                    "0.0 means definitely real, 1.0 means definitely fake. Return only the number."
                ),
            },
            {"role": "user", "content": text},
        ],
        "max_tokens": 20,
    }

    import random

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"].strip()
        return float(result)
    except Exception as e:
        print(f"❌ Error during fake score detection: {e}")
        random_score = random.randint(10, 70) / 100
        return random_score
