from sqlalchemy import create_engine, text
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llm_openrouter import OpenRouterLLM
from pathlib import Path

# ========================
# إعداد LLM والتضمين
# ========================
Settings.llm = OpenRouterLLM(
    # model="mistralai/devstral-small:free",
    # model="google/gemma-3-4b-it:free",
    # model="meta-llama/llama-4-maverick:free",
    # model="tngtech/deepseek-r1t-chimera:free",
    model="deepseek/deepseek-chat-v3-0324:free",
    # api_key="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",
    # api_key="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",
    api_key="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",
)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ✅ برومبت مخصص يمنع استخدام category أو Interest
Settings.system_prompt = (
    "You are a SQL assistant. Your job is to generate raw SQL queries only.\n"
    "Always include 'news_article_id' in your SELECT statement.\n"
    "Never use any table named TruNexApp_interest.\n"
    "Never use any column that includes the word 'category'.\n"
    "To determine the article type, use only the column 'news_article_type'.\n"
    "Use the exact article types: 'politic','sports','economy','culture','health','technology','general'. Never use 'sport'.\n"
    "Do not use country codes like 'SY' or 'ME'. Use only the full lowercase region values as defined: syria, arab, or world.\n"
    "replace 'إ', 'أ', 'آ' with 'ا'; 'ى' with 'ي'; 'ئ' with 'ي'; 'ة' with 'ه'.\n"
    "This helps to match user queries like 'ايران' with 'إيران'.\n"
    "Always apply normalization when using LIKE in WHERE conditions on Arabic text.\n"
    "User queries might contain semantically related or alternative keywords (like 'إيران' or 'إسرائيل').\n"
    "When such keywords appear together, use OR instead of AND to ensure broader matching.\n"
    "Never generate more than one SQL statement. Only return a single SELECT statement without any comments or explanations."
)


# ========================
# الاتصال بقاعدة البيانات
# ========================
db_path = Path(__file__).resolve().parent.parent.parent / "db.sqlite3"
engine = create_engine(f"sqlite:///{db_path}")
sql_database = SQLDatabase(engine, include_tables=["TruNexApp_newsarticle"])

# وصف الجدول (بدون category)
table_desc = {
    "TruNexApp_newsarticle": (
        "This table contains news articles with the following fields:\n"
        "- news_article_id: ID\n"
        "- news_article_url: URL of the article\n"
        "- news_article_type:'politic','sports','economy','culture','health','technology','general'\n"
        "- news_article_region: 'syria', 'arab', 'world'\n"
        "- news_article_title: Title of the article\n"
        "- news_article_content: Main text\n"
        "- news_article_keywords: Extracted keywords\n"
        "- news_article_published_at: Date published\n"
    )
}


# إنشاء محرك الأسئلة
query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database, table_description=table_desc
)

# تجربة سؤال طبيعي
question = "اخر اخبار الرياضة"
response = query_engine.query(question)

# تنظيف الاستعلام
clean_sql = response.metadata.get("sql_query", "").strip()

# منع تنفيذ أي SQL فيه category أو interest
if "category" in clean_sql.lower() or "interest" in clean_sql.lower():
    print("❌ الاستعلام مرفوض: يحتوي على category أو interest.")
else:
    try:
        with engine.connect() as conn:
            result = conn.execute(text(clean_sql))
            rows = result.fetchall()
            print("📦 النتائج:")
            for row in rows:
                print(row)
    except Exception as e:
        print("❌ خطأ أثناء تنفيذ SQL:", e)


# عرض الاستعلام الناتج
print("\n🔍 السؤال:", question)
print("📄 SQL المستخدم:\n", clean_sql)
print("📩 الجواب:\n", response)
