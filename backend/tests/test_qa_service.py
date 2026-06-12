"""Tests for citation marker filtering and parsing (no API key needed)."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("CHROMA_PERSIST_DIR", tempfile.mkdtemp())

from app.services.qa_service import (  # noqa: E402
    CitationMarkerFilter,
    QAService,
    strip_citation_markers,
)
from app.services.vector_store import RetrievedChunk  # noqa: E402


def stream_through_filter(tokens):
    """Feed tokens through the filter and return the emitted text."""
    f = CitationMarkerFilter()
    out = "".join(f.feed(t) for t in tokens)
    return out + f.flush()


def test_filter_passes_plain_text():
    assert stream_through_filter(["Hello ", "world"]) == "Hello world"


def test_filter_strips_complete_marker_in_one_token():
    text = "Yes. [[CITE:abc-123]]Roll the dice.[[/CITE]] That is the rule."
    assert stream_through_filter([text]) == "Yes. Roll the dice. That is the rule."


def test_filter_strips_marker_split_across_tokens():
    tokens = ["Yes. [[CI", "TE:abc-1", "23]]Roll the d", "ice.[[/CI", "TE]] Done."]
    assert stream_through_filter(tokens) == "Yes. Roll the dice. Done."


def test_filter_never_emits_partial_markers():
    tokens = ["Answer [[", "CITE:xyz]]quote here[[", "/CITE]]."]
    f = CitationMarkerFilter()
    emitted = []
    for t in tokens:
        chunk = f.feed(t)
        assert "[[CITE" not in chunk and "[[/CITE" not in chunk
        emitted.append(chunk)
    assert "".join(emitted) + f.flush() == "Answer quote here."


def test_filter_keeps_literal_brackets():
    assert stream_through_filter(["score [3] and [x]"]) == "score [3] and [x]"
    assert stream_through_filter(["a [", "b] c"]) == "a [b] c"


def test_filter_keeps_text_that_almost_looks_like_marker():
    # '[[CITE:abc]x' can never complete into a marker, so it must be emitted
    assert stream_through_filter(["[[CITE:abc]x done"]) == "[[CITE:abc]x done"


def test_filter_drops_unterminated_marker_at_end_of_stream():
    assert stream_through_filter(["Done. [[CITE:abc"]) == "Done. "


def test_filter_emits_trailing_lone_bracket():
    assert stream_through_filter(["list: ["]) == "list: ["


def test_strip_citation_markers():
    text = "A [[CITE:id-1]]quoted rule[[/CITE]] B"
    assert strip_citation_markers(text) == "A quoted rule B"


def make_chunk(chunk_id, text):
    return RetrievedChunk(text=text, metadata={"chunk_id": chunk_id})


def parse(text, chunks):
    # _parse_citations doesn't touch instance state, so skip __init__
    service = QAService.__new__(QAService)
    return service._parse_citations(text, chunks)


def test_parse_citations_finds_quote_position():
    chunk = make_chunk("id-1", "When you roll a 7, the robber moves immediately.")
    sources = parse("[[CITE:id-1]]the robber moves immediately[[/CITE]]", [chunk])
    assert len(sources) == 1
    src = sources[0]
    assert src.chunk_id == "id-1"
    assert chunk.text[src.quote_char_start:src.quote_char_end] == "the robber moves immediately"


def test_parse_citations_handles_quote_with_brackets():
    chunk = make_chunk("id-1", "Resources [wood, brick] are gained on the roll.")
    sources = parse("[[CITE:id-1]]Resources [wood, brick] are gained[[/CITE]]", [chunk])
    assert len(sources) == 1
    assert sources[0].quote_char_start == 0


def test_parse_citations_falls_back_when_quote_missing():
    chunk = make_chunk("id-1", "Some chunk text that is long enough to highlight.")
    sources = parse("[[CITE:id-1]]totally fabricated quote[[/CITE]]", [chunk])
    assert len(sources) == 1
    assert sources[0].quote_char_start == 0
    assert sources[0].quote_char_end > 0


def test_parse_citations_ignores_unknown_chunk_ids():
    chunk = make_chunk("id-1", "text")
    assert parse("[[CITE:nope]]quote[[/CITE]]", [chunk]) == []


def test_parse_citations_dedupes_repeated_citations():
    chunk = make_chunk("id-1", "the robber moves immediately")
    text = (
        "[[CITE:id-1]]the robber moves immediately[[/CITE]] and again "
        "[[CITE:id-1]]the robber moves immediately[[/CITE]]"
    )
    assert len(parse(text, [chunk])) == 1


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
