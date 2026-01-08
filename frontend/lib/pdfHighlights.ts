import type { SourceReference, ChunkResponse, PDFHighlight, BBox } from './types';

function mergeBboxes(bboxes: BBox[]): BBox[] {
  if (bboxes.length === 0) return [];

  // Sort by y0 (top), then x0 (left)
  const sorted = [...bboxes].sort((a, b) => {
    const yDiff = a.y0 - b.y0;
    return Math.abs(yDiff) < 5 ? a.x0 - b.x0 : yDiff;
  });

  const merged: BBox[] = [];
  let current = { ...sorted[0] };

  for (let i = 1; i < sorted.length; i++) {
    const next = sorted[i];
    // Same line (y0 within 5 units) and horizontally adjacent (within 10 units)
    const sameLine = Math.abs(next.y0 - current.y0) < 5;
    const adjacent = next.x0 - current.x1 < 10;

    if (sameLine && adjacent) {
      current.x1 = Math.max(current.x1, next.x1);
      current.y1 = Math.max(current.y1, next.y1);
    } else {
      merged.push(current);
      current = { ...next };
    }
  }
  merged.push(current);

  return merged;
}

export function computePDFHighlights(
  source: SourceReference,
  chunk: ChunkResponse
): PDFHighlight[] {
  const highlightsByPage = new Map<number, BBox[]>();

  // Find atoms that overlap with the quote range
  for (const atom of chunk.atoms) {
    if (
      atom.char_end > source.quote_char_start &&
      atom.char_start < source.quote_char_end
    ) {
      const pageHighlights = highlightsByPage.get(atom.page_num) || [];
      pageHighlights.push(atom.bbox);
      highlightsByPage.set(atom.page_num, pageHighlights);
    }
  }

  // Convert to array and merge adjacent bboxes
  return Array.from(highlightsByPage.entries()).map(([pageNum, bboxes]) => ({
    pageNum,
    bboxes: mergeBboxes(bboxes),
  }));
}
