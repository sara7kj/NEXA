import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    section: str
    content: str
    index: int


HEADING = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def chunk_by_heading(text: str, default_section: str = "General") -> list[TextChunk]:
    matches = list(HEADING.finditer(text))

    if not matches:
        body = text.strip()
        return [TextChunk(default_section, body, 0)] if body else []

    chunks: list[TextChunk] = []

    preamble = text[: matches[0].start()].strip()
    if preamble:
        chunks.append(TextChunk(default_section, preamble, 0))

    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if body:
            section = match.group(1).strip()
            chunks.append(TextChunk(section, f"{section}\n{body}", len(chunks)))

    return chunks
