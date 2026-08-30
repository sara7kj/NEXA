import pytest

pytestmark = pytest.mark.slow

from nexa.rag.store import load_retriever

QUESTIONS = [
    ("ÙƒÙ… ÙŠÙˆÙ… Ø¥Ø¬Ø§Ø²Ø© Ø³Ù†ÙˆÙŠØ© Ù„Ù„Ù…ÙˆØ¸ÙØŸ", "annual_leave_en"),
    ("Ù…ØªÙ‰ ØªÙ†ØªÙ‡ÙŠ ØµÙ„Ø§Ø­ÙŠØ© Ø±ØµÙŠØ¯ Ø§Ù„Ø¥Ø¬Ø§Ø²Ø© Ø§Ù„Ù…Ø±Ø­Ù‘Ù„ØŸ", "annual_leave_en"),
    ("Ù…Ø§ Ù‡ÙŠ Ù…ØªØ·Ù„Ø¨Ø§Øª ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±ØŸ", "it_security_en"),
    ("Ù…Ø§Ø°Ø§ Ø£ÙØ¹Ù„ Ø¥Ø°Ø§ ÙÙ‚Ø¯Øª Ø¬Ù‡Ø§Ø² Ø§Ù„Ø¹Ù…Ù„ØŸ", "it_security_en"),
    ("Ù…ØªÙ‰ ÙŠØ¬Ø¨ ØªÙ‚Ø¯ÙŠÙ… Ù…Ø·Ø§Ù„Ø¨Ø© Ø§Ù„Ù…ØµØ§Ø±ÙŠÙØŸ", "expenses_en"),
    ("ÙƒÙ… Ø§Ù„Ø­Ø¯ Ø§Ù„Ø£Ù‚ØµÙ‰ Ù„Ø³Ø¹Ø± Ø§Ù„ÙÙ†Ø¯Ù‚ Ø¯Ø§Ø®Ù„ÙŠØ§Ù‹ØŸ", "business_travel_en"),
    ("How many days can I work remotely?", "remote_work_ar"),
    ("Can I use public wifi for company systems?", "remote_work_ar"),
    ("How is end of service pay calculated?", "end_of_service_ar"),
    ("When is end of service pay released?", "end_of_service_ar"),
]


@pytest.fixture(scope="module")
def retriever():
    return load_retriever()


def test_corpus_recall_at_1(retriever) -> None:
    hits = 0
    misses = []
    for question, expected_doc in QUESTIONS:
        top = retriever.search(question)[0]
        if top.doc_id.split("#")[0] == expected_doc:
            hits += 1
        else:
            misses.append((question, expected_doc, top.doc_id))

    recall = hits / len(QUESTIONS)
    assert recall >= 0.80, f"Recall@1 = {recall:.2f}, misses: {misses}"