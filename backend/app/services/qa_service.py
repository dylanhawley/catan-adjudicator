"""Question-answering service using retrieval-augmented generation."""
import re
from typing import Generator, List, Optional, Tuple

from openai import OpenAI

from app.config import settings
from app.models.response import QueryResponse, SourceReference
from app.services.vector_store import RetrievedChunk, VectorStoreService

OPEN_PREFIX = "[[CITE:"
CLOSE_MARKER = "[[/CITE]]"
CITATION_RE = re.compile(r"\[\[CITE:([^\]]+)\]\](.*?)\[\[/CITE\]\]", re.DOTALL)
MARKER_RE = re.compile(r"\[\[CITE:[^\]]*\]\]|\[\[/CITE\]\]")

SYSTEM_PROMPT = """You are the Catan Adjudicator: an expert referee for the board game CATAN. \
You answer rules questions using ONLY the provided rulebook excerpts.

Rules:
1. Lead with the ruling. Answer the question directly in the first sentence, then explain.
2. Base every factual claim on the excerpts. When you state a rule, cite it by wrapping a \
verbatim quote in markers: [[CITE:chunk_id]]exact text copied from that excerpt[[/CITE]]
   - chunk_id must be one of the chunk IDs shown in the excerpts.
   - The quoted text must appear word-for-word in that excerpt.
3. If the excerpts only partially cover the question, answer what you can and say clearly \
which part the rulebook excerpts do not cover.
4. If the excerpts contain nothing relevant, say you cannot answer from the available \
rulebook content. Never invent rules.
5. Keep answers concise and practical for players in the middle of a game."""

CONDENSE_PROMPT = """Rewrite the user's latest question as a single standalone question \
suitable for searching a Catan rulebook. Resolve pronouns and references using the \
conversation. Return only the rewritten question, nothing else."""


class CitationMarkerFilter:
    """Strips [[CITE:...]] and [[/CITE]] markers from a token stream.

    Markers can be split across tokens, so text that might be the start of a
    marker is held back until it either completes (and is dropped) or turns
    out to be ordinary text (and is emitted).
    """

    def __init__(self):
        self._buffer = ""

    def feed(self, delta: str) -> str:
        """Add a token to the filter and return the text safe to emit."""
        buf = self._buffer + delta
        out: List[str] = []
        pos = 0
        while True:
            idx = buf.find("[", pos)
            if idx == -1:
                out.append(buf[pos:])
                self._buffer = ""
                break
            out.append(buf[pos:idx])
            consumed = self._match_marker(buf[idx:])
            if consumed == -1:
                # Could still grow into a marker; hold it back
                self._buffer = buf[idx:]
                break
            if consumed == 0:
                # Just a literal '[' character
                out.append("[")
                pos = idx + 1
            else:
                pos = idx + consumed
        return "".join(out)

    def flush(self) -> str:
        """Return any held-back text that never completed a marker."""
        leftover = self._buffer
        self._buffer = ""
        # A lone '[' was held only because it might have started a marker
        return leftover if leftover == "[" else ""

    @staticmethod
    def _match_marker(s: str) -> int:
        """For text starting with '[': return the length of a complete marker,
        -1 if it could still grow into one, or 0 if it can never be one."""
        if s.startswith(CLOSE_MARKER):
            return len(CLOSE_MARKER)
        if CLOSE_MARKER.startswith(s):
            return -1
        if OPEN_PREFIX.startswith(s):
            return -1
        if s.startswith(OPEN_PREFIX):
            body = s[len(OPEN_PREFIX):]
            bracket = body.find("]")
            if bracket == -1:
                return -1  # still reading the chunk id
            after = body[bracket + 1:]
            if after.startswith("]"):
                return len(OPEN_PREFIX) + bracket + 2
            if after == "":
                return -1  # saw ']', waiting for the second ']'
        return 0


def strip_citation_markers(text: str) -> str:
    """Remove citation markers, keeping the quoted text."""
    return MARKER_RE.sub("", text)


class QAService:
    """Service for question-answering using RAG."""

    def __init__(self, vector_store_service: VectorStoreService):
        """
        Initialize the QA service.

        Args:
            vector_store_service: Vector store service instance
        """
        self.vector_store_service = vector_store_service
        self.client = OpenAI(api_key=settings.openai_api_key)

    def _condense_question(self, question: str, history: List[dict]) -> str:
        """Rewrite a follow-up question into a standalone search query.

        Follow-ups like "what about cities?" retrieve poorly as-is because the
        vector search has no conversation context.
        """
        if not history:
            return question
        try:
            convo_lines = []
            for msg in history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = strip_citation_markers(msg.get("content", "")).strip()
                if content:
                    convo_lines.append(f"{role}: {content}")
            convo_lines.append(f"User: {question}")
            response = self.client.chat.completions.create(
                model=settings.condense_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": CONDENSE_PROMPT},
                    {"role": "user", "content": "\n".join(convo_lines)},
                ],
            )
            rewritten = (response.choices[0].message.content or "").strip()
            return rewritten or question
        except Exception:
            # Retrieval with the raw question is better than failing outright
            return question

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks into the excerpt block shown to the model."""
        parts = []
        for chunk in chunks:
            chunk_id = chunk.metadata.get("chunk_id", "")
            header = f"[Chunk {chunk_id}, Page {chunk.metadata.get('page_start', '?')}"
            section = chunk.metadata.get("section_title", "")
            if section:
                header += f", Section: {section}"
            header += "]"
            parts.append(f"{header}\n{chunk.text}")
        return "\n\n---\n\n".join(parts)

    def _build_messages(
        self,
        question: str,
        context: str,
        history: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Build the chat messages for the answer model."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in (history or [])[-12:]:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = strip_citation_markers(msg.get("content", "")).strip()
            if content:
                messages.append({"role": role, "content": content})
        messages.append({
            "role": "user",
            "content": f"Rulebook excerpts:\n\n{context}\n\nQuestion: {question}",
        })
        return messages

    def _parse_citations(
        self, text: str, chunks: List[RetrievedChunk]
    ) -> List[SourceReference]:
        """Extract source references from [[CITE:...]] markers in the response."""
        sources: List[SourceReference] = []
        seen = set()

        for match in CITATION_RE.finditer(text):
            cited_id = match.group(1).strip()
            quote = match.group(2).strip()

            for chunk in chunks:
                chunk_id = chunk.metadata.get("chunk_id", "")
                if chunk_id != cited_id and cited_id not in chunk_id:
                    continue

                chunk_text = chunk.text
                needle = quote.lower()[:50] if len(quote) > 50 else quote.lower()
                start = chunk_text.lower().find(needle) if needle else -1
                if start >= 0:
                    end = min(start + len(quote), len(chunk_text))
                else:
                    # Quote not found verbatim; highlight the start of the chunk
                    start = 0
                    end = min(100, len(chunk_text))

                key = (chunk_id, start, end)
                if key not in seen:
                    seen.add(key)
                    sources.append(SourceReference(
                        chunk_id=chunk_id,
                        quote_char_start=start,
                        quote_char_end=end,
                    ))
                break

        return sources

    def _fallback_sources(self, chunks: List[RetrievedChunk]) -> List[SourceReference]:
        """Source references covering retrieved chunks when no citations parsed."""
        return [
            SourceReference(
                chunk_id=chunk.metadata.get("chunk_id", ""),
                quote_char_start=0,
                quote_char_end=0,
            )
            for chunk in chunks
        ]

    def answer_question(self, question: str, k: Optional[int] = None) -> QueryResponse:
        """
        Answer a question using RAG (non-streaming).

        Args:
            question: User's question
            k: Number of chunks to retrieve

        Returns:
            QueryResponse with answer and sources
        """
        k = k or settings.retrieval_k
        chunks = self.vector_store_service.search(question, k=k)

        if not chunks:
            return QueryResponse(
                answer="I cannot answer this question as no relevant information was found in the rulebooks.",
                sources=[],
            )

        messages = self._build_messages(question, self._format_context(chunks))

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                temperature=0,
                messages=messages,
            )
            raw_answer = response.choices[0].message.content or ""
            sources = self._parse_citations(raw_answer, chunks)
            return QueryResponse(
                answer=strip_citation_markers(raw_answer).strip(),
                sources=sources or self._fallback_sources(chunks),
            )
        except Exception as e:
            return QueryResponse(
                answer=f"I encountered an error while processing your question: {str(e)}. Please try again.",
                sources=[],
            )

    def stream_answer_question(
        self,
        question: str,
        k: Optional[int] = None,
        conversation_history: Optional[List[dict]] = None,
    ) -> Generator[Tuple[str, any], None, None]:
        """
        Stream an answer to a question using RAG.

        Yields tuples of (event_type, data):
        - ("token", str): Chunk of the answer (citation markers already stripped)
        - ("sources", List[SourceReference]): Sources (sent after answer completes)
        - ("done", None): Streaming complete
        - ("error", str): Error message

        Args:
            question: User's question
            k: Number of chunks to retrieve
            conversation_history: Previous conversation messages

        Yields:
            Tuples of (event_type, data)
        """
        k = k or settings.retrieval_k
        history = conversation_history or []

        try:
            search_query = self._condense_question(question, history)
            chunks = self.vector_store_service.search(search_query, k=k)
        except Exception as e:
            yield ("error", f"Error retrieving rulebook content: {str(e)}")
            return

        if not chunks:
            yield ("sources", [])
            yield ("token", "I cannot answer this question as no relevant information was found in the rulebooks.")
            yield ("done", None)
            return

        messages = self._build_messages(question, self._format_context(chunks), history)
        marker_filter = CitationMarkerFilter()
        full_response = ""

        try:
            stream = self.client.chat.completions.create(
                model=settings.openai_model,
                temperature=0,
                messages=messages,
                stream=True,
            )
            for event in stream:
                if not event.choices:
                    continue
                delta = event.choices[0].delta.content
                if not delta:
                    continue
                full_response += delta
                clean = marker_filter.feed(delta)
                if clean:
                    yield ("token", clean)

            leftover = marker_filter.flush()
            if leftover:
                yield ("token", leftover)

            sources = self._parse_citations(full_response, chunks)
            yield ("sources", sources or self._fallback_sources(chunks))
            yield ("done", None)

        except Exception as e:
            yield ("error", f"Error generating response: {str(e)}")
