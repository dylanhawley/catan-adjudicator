import type { SourceReference, ChunkResponse, CitationRange } from './types';

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[""]/g, '"')
    .replace(/['']/g, "'")
    .trim();
}

function findInAnswer(
  normalizedAnswer: string,
  originalAnswer: string,
  normalizedQuote: string
): { start: number; end: number } | null {
  const index = normalizedAnswer.indexOf(normalizedQuote);
  if (index === -1) return null;

  // Map normalized position back to original string
  let normalizedPos = 0;
  let originalStart = -1;
  let originalEnd = -1;

  for (let i = 0; i < originalAnswer.length && originalEnd === -1; i++) {
    const normalizedChar = normalizeText(originalAnswer[i]);
    if (normalizedChar.length > 0) {
      if (normalizedPos === index) {
        originalStart = i;
      }
      if (normalizedPos === index + normalizedQuote.length - 1) {
        originalEnd = i + 1;
      }
      normalizedPos++;
    } else if (originalStart !== -1 && originalEnd === -1) {
      // Include whitespace within the quote
    }
  }

  if (originalStart !== -1 && originalEnd === -1) {
    originalEnd = originalAnswer.length;
  }

  return originalStart !== -1 ? { start: originalStart, end: originalEnd } : null;
}

export function findCitationRanges(
  answer: string,
  sources: SourceReference[],
  chunks: ChunkResponse[]
): CitationRange[] {
  const ranges: CitationRange[] = [];
  const normalizedAnswer = normalizeText(answer);

  sources.forEach((source, index) => {
    const chunk = chunks.find((c) => c.chunk_id === source.chunk_id);
    if (!chunk) return;

    const quoteText = chunk.text.slice(
      source.quote_char_start,
      source.quote_char_end
    );

    if (!quoteText.trim()) return;

    const normalizedQuote = normalizeText(quoteText);
    const position = findInAnswer(normalizedAnswer, answer, normalizedQuote);

    if (position) {
      ranges.push({
        sourceIndex: index,
        source,
        answerStart: position.start,
        answerEnd: position.end,
        quoteText,
      });
    }
  });

  // Sort by position and remove overlaps (keep earlier citation)
  ranges.sort((a, b) => a.answerStart - b.answerStart);

  const nonOverlapping: CitationRange[] = [];
  for (const range of ranges) {
    const lastRange = nonOverlapping[nonOverlapping.length - 1];
    if (!lastRange || range.answerStart >= lastRange.answerEnd) {
      nonOverlapping.push(range);
    }
  }

  return nonOverlapping;
}
