from sqlalchemy import create_engine, text as sql_text
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from TruNexApp.ai_models.llm_openrouter import OpenRouterLLM
from pathlib import Path

# إعداد LLM
Settings.llm = OpenRouterLLM(
    model="deepseek/deepseek-chat-v3-0324:free",
    # api_key="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",
    # api_key="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",
    api_key="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",
)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# برومبت مخصص
Settings.system_prompt = (
    "You are a SQL assistant. Your job is to generate raw SQL queries only.\n"
    "Always include 'news_article_id' in your SELECT statement.\n"
    "Never use any table named TruNexApp_interest.\n"
    "Never use any column that includes the word 'category'.\n"
    "To determine the article type, use only the column 'news_article_type'.\n"
    "Use the exact article types: 'politic','sports','economy','culture','health','technology','general'.\n"
    "Do not use country codes like 'SY' or 'ME'. Use only the full lowercase region values as defined: syria, arab, or world.\n"
    "Normalize user queries to handle Arabic spelling variants. For example, treat 'ايران' as equivalent to 'إيران', and 'اسرائيل' as 'إسرائيل'. Apply normalization only when interpreting the user's input, not when querying or modifying the database."
    "Always apply normalization when using LIKE in WHERE conditions on Arabic text.\n"
    "Never generate more than one SQL statement. Only return a single SELECT statement without any comments or explanations."
)


# الاتصال بقاعدة البيانات
db_path = Path(__file__).resolve().parent.parent.parent / "db.sqlite3"
engine = create_engine(f"sqlite:///{db_path}")
sql_database = SQLDatabase(engine, include_tables=["TruNexApp_newsarticle"])

table_desc = {
    "TruNexApp_newsarticle": (
        "This table contains news articles with the following fields:\n"
        "- news_article_id: ID\n"
        "- news_article_url: URL of the article\n"
        "- news_article_type: 'politic','sports','economy','culture','health','technology','general'\n"
        "- news_article_region: 'syria', 'arab', 'world'\n"
        "- news_article_title: Title of the article\n"
        "- news_article_content: Main text\n"
        "- news_article_keywords: Extracted keywords\n"
        "- news_article_published_at: Date published\n"
    )
}

query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database, table_description=table_desc
)


from sqlalchemy.exc import ProgrammingError


def run_nl_query(question: str):
    response = query_engine.query(question)
    sql_query = response.metadata.get("sql_query", "").strip()

    if "category" in sql_query.lower() or "interest" in sql_query.lower():
        return {
            "rejected": True,
            "sql": sql_query,
            "error": "الاستعلام يحتوي على category أو interest، وهذا غير مسموح.",
        }

    #  تحقق أن الاستعلام يحتوي فقط على عبارة SQL واحدة
    if ";" in sql_query.strip()[:-1]:
        return {
            "rejected": True,
            "sql": sql_query,
            "error": "حدث خطأ: الاستعلام يحتوي على أكثر من عبارة SQL.",
        }

    try:
        with engine.connect() as conn:
            result = conn.execute(sql_text(sql_query))
            rows = result.fetchall()
            keys = result.keys()
            row_dicts = [dict(zip(keys, row)) for row in rows]
        return {
            "rejected": False,
            "sql": sql_query,
            "rows": row_dicts,
        }

    except ProgrammingError as e:
        return {
            "rejected": True,
            "sql": sql_query,
            "error": f"حدث خطأ في SQL: {str(e)}",
        }

    except Exception as e:
        return {
            "rejected": True,
            "sql": sql_query,
            "error": f"حدث خطأ أثناء تنفيذ الاستعلام: {str(e)}",
        }
