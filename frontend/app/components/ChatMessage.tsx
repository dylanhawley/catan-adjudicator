'use client';

import { useMemo } from 'react';
import Card from './ui/Card';
import CitationText from './CitationText';
import { findCitationRanges } from '@/lib/citationMatcher';
import type { Message, CitationRange } from '@/lib/types';

interface ChatMessageProps {
  message: Message;
  onCitationClick: (range: CitationRange) => void;
}

// Strip citation markers from text
function stripCitationMarkers(text: string): string {
  return text
    .replace(/\[\[CITE:[^\]]*\]\]/g, '')
    .replace(/\[\[\/CITE\]\]/g, '');
}

export default function ChatMessage({ message, onCitationClick }: ChatMessageProps) {
  // Clean answer text (without markers) for citation matching
  const cleanAnswer = useMemo(() => stripCitationMarkers(message.answer), [message.answer]);

  const citationRanges = useMemo(() => {
    if (!cleanAnswer || message.sources.length === 0 || message.chunks.length === 0) {
      return [];
    }
    return findCitationRanges(cleanAnswer, message.sources, message.chunks);
  }, [cleanAnswer, message.sources, message.chunks]);

  return (
    <Card className="mb-4">
      <div className="mb-4 pb-4 border-b border-warm-200">
        <p className="text-xs text-warm-400 uppercase tracking-wide mb-1">
          Question
        </p>
        <p className="text-warm-700">{message.question}</p>
      </div>
      <div>
        <p className="text-xs text-warm-400 uppercase tracking-wide mb-2">
          Answer
        </p>
        <CitationText
          text={cleanAnswer}
          citationRanges={citationRanges}
          onCitationClick={onCitationClick}
          isStreaming={message.isStreaming}
        />
        {citationRanges.length > 0 && !message.isStreaming && (
          <p className="mt-4 text-xs text-warm-400">
            Click highlighted text to view source in PDF
          </p>
        )}
      </div>
    </Card>
  );
}
