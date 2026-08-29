from nexa.rag.chunker import chunk_by_heading


def test_no_headings_returns_single_chunk() -> None:
    chunks = chunk_by_heading("Just one paragraph.")
    assert len(chunks) == 1
    assert chunks[0].section == "General"


def test_empty_text_returns_nothing() -> None:
    assert chunk_by_heading("   ") == []


def test_splits_on_headings() -> None:
    text = "## Annual Leave\n21 days.\n\n## Sick Leave\n30 days."
    chunks = chunk_by_heading(text)
    assert len(chunks) == 2
    assert chunks[0].section == "Annual Leave"
    assert chunks[1].section == "Sick Leave"


def test_heading_is_included_in_content() -> None:
    chunks = chunk_by_heading("## Annual Leave\n21 days.")
    assert "Annual Leave" in chunks[0].content


def test_preamble_before_first_heading_is_kept() -> None:
    text = "Effective 2026.\n\n## Annual Leave\n21 days."
    chunks = chunk_by_heading(text)
    assert len(chunks) == 2
    assert "Effective 2026" in chunks[0].content


def test_arabic_headings() -> None:
    text = "## الإجازة السنوية\nواحد وعشرون يوماً.\n\n## الإجازة المرضية\nثلاثون يوماً."
    chunks = chunk_by_heading(text)
    assert len(chunks) == 2
    assert chunks[0].section == "الإجازة السنوية"


def test_front_matter_is_parsed_and_removed() -> None:
    from nexa.rag.chunker import parse_front_matter

    text = "---\ntitle: Leave Policy\nlanguage: en\n---\n## Section\nBody."
    meta, body = parse_front_matter(text)

    assert meta["title"] == "Leave Policy"
    assert meta["language"] == "en"
    assert not body.startswith("---")


def test_text_without_front_matter_is_unchanged() -> None:
    from nexa.rag.chunker import parse_front_matter

    meta, body = parse_front_matter("## Section\nBody.")
    assert meta == {}
    assert body.startswith("## Section")
