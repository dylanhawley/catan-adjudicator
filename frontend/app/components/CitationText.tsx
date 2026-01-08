'use client';

import { useMemo } from 'react';
import type { CitationRange } from '@/lib/types';

interface CitationTextProps {
  text: string;
  citationRanges: CitationRange[];
  onCitationClick: (range: CitationRange) => void;
  isStreaming?: boolean;
}

interface Segment {
  type: 'text' | 'citation';
  content: string;
  range?: CitationRange;
}

// Strip citation markers from text for display
function stripCitationMarkers(text: string): string {
  return text
    .replace(/\[\[CITE:[^\]]*\]\]/g, '')
    .replace(/\[\[\/CITE\]\]/g, '');
}

export default function CitationText({
  text,
  citationRanges,
  onCitationClick,
  isStreaming = false,
}: CitationTextProps) {
  // Strip markers for display
  const cleanText = useMemo(() => stripCitationMarkers(text), [text]);

  const segments = useMemo(() => {
    if (citationRanges.length === 0) {
      return [{ type: 'text' as const, content: cleanText }];
    }

    const result: Segment[] = [];
    let lastEnd = 0;

    for (const range of citationRanges) {
      // Add text before this citation
      if (range.answerStart > lastEnd) {
        result.push({
          type: 'text',
          content: cleanText.slice(lastEnd, range.answerStart),
        });
      }

      // Add the citation
      result.push({
        type: 'citation',
        content: cleanText.slice(range.answerStart, range.answerEnd),
        range,
      });

      lastEnd = range.answerEnd;
    }

    // Add remaining text
    if (lastEnd < cleanText.length) {
      result.push({
        type: 'text',
        content: cleanText.slice(lastEnd),
      });
    }

    return result;
  }, [cleanText, citationRanges]);

  return (
    <div className="text-warm-600 leading-relaxed whitespace-pre-wrap">
      {segments.map((segment, i) =>
        segment.type === 'citation' && segment.range ? (
          <button
            key={i}
            onClick={() => onCitationClick(segment.range!)}
            className="inline bg-citation-bg hover:bg-citation-hover rounded px-0.5 -mx-0.5 border-b border-citation-border cursor-pointer"
            title="Click to view source in PDF"
          >
            {segment.content}
            <sup className="text-xs text-accent ml-0.5 font-medium">
              [{segment.range.sourceIndex + 1}]
            </sup>
          </button>
        ) : (
          <span key={i}>{segment.content}</span>
        )
      )}
      {isStreaming && (
        <span className="inline-block w-0.5 h-5 ml-0.5 bg-warm-700 animate-pulse align-text-bottom" />
      )}
    </div>
  );
}
