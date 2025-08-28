from .api_fetcher import fetch_from_nytimes, fetch_from_newsapi_general
from .rss_fetcher import fetch_from_rss
from .scraper_fetcher import fetch_from_scraper


def fetch_news_from_source(source, method=None, target="main"):
    method = method or source.news_source_method

    if method == "api":
        name = source.news_source_name.lower()
        if "new york times" in name:
            return fetch_from_nytimes(source)
        else:
            return fetch_from_newsapi_general(source)

    elif method == "rss":
        return fetch_from_rss(source)
    elif method == "scraper":
        return fetch_from_scraper(source, target=target)
    else:
        print(f"[⚠️] Unknown fetch method: {method}")
        return []
