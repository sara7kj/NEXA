import pytest

from nexa.rag.store import load_retriever

QUESTIONS = [
    ("كم يوم إجازة سنوية للموظف؟", "annual_leave_en"),
    ("متى تنتهي صلاحية رصيد الإجازة المرحّل؟", "annual_leave_en"),
    ("ما هي متطلبات كلمة المرور؟", "it_security_en"),
    ("ماذا أفعل إذا فقدت جهاز العمل؟", "it_security_en"),
    ("متى يجب تقديم مطالبة المصاريف؟", "expenses_en"),
    ("كم الحد الأقصى لسعر الفندق داخلياً؟", "business_travel_en"),
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