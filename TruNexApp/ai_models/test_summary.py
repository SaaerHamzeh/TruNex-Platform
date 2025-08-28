from llm_utils import (
    summarize_text_with_openrouter,
    detect_fake_news_score_with_openrouter,
    detect_article_region_with_openrouter,
)

# 📝 مقالك المكتوب يدويًا
text = """
1. أحيت خشبة مسرح القباني في دمشق الذكرى السنوية الأولى لرحيل الكاتب السوري فؤاد حميرة عبر عرض سوق الأسئلة المستلهم من روايته الأخيرة رصاصة.  
2. اختزل الكاتب غزوان البلح الرواية الفلسفية المعقدة إلى خطوط درامية مبسطة مع الحفاظ على جوهر الصراع الداخلي ودمج سيرة الراحل بالعمل.  
3. واجه الفريق تحديات كبيرة مثل نقص التمويل وضعف الدعم اللوجستي مما أثر على جودة العروض وفقاً لما أكده المخرج محمد حميرة.
"""

# summary = summarize_text_with_openrouter(text)
# print("\n📄 التلخيص الناتج:\n", summary)


# score = detect_fake_news_score_with_openrouter(text)
# score_percent = int(round(score * 100))  # ⬅️ نحوله لنسبة مئوية
# is_fake = score_percent >= 50  # نعتبره مزيف إذا ≥ 80%

# print(f"this the text:{text}")
# print(f"is it fake? ", "Fake" if is_fake else "Real")
# print(f"fake score  : {score_percent}%")


region = detect_article_region_with_openrouter(text)
print(f"the region is: ", {region})
