from app.services.ai_service import ai_service

# Test Retrieval
# We ask a question that would be in a financial report
context = ai_service.search_risks("What are the primary market risks and liquidity concerns?")

print("\n--- AI RETRIEVED CONTEXT ---")
for i, doc in enumerate(context):
    print(f"\nChunk {i+1}:")
    print(doc.page_content[:500] + "...") 