'use client';

import type { SourceReference, ChunkResponse } from '@/lib/types';

interface SourceListProps {
  sources: SourceReference[];
  chunks: ChunkResponse[];
  onSourceClick: (source: SourceReference, chunk: ChunkResponse) => void;
}

const SourceList = ({ sources, chunks, onSourceClick }: SourceListProps) => {
  if (sources.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Source Details</h3>
      <ul className="space-y-4">
        {sources.map((source, index) => {
          const chunk = chunks.find((c) => c.chunk_id === source.chunk_id);
          if (!chunk) return null;

          const quoteText = chunk.text.slice(
            source.quote_char_start,
            source.quote_char_end
          );

          return (
            <li key={index} className="border-b pb-4 last:border-b-0">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="text-sm text-gray-600">
                    Page {chunk.page_start + 1}
                    {chunk.section_title && ` • ${chunk.section_title}`}
                  </p>
                </div>
                <button
                  onClick={() => onSourceClick(source, chunk)}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  aria-label={`View source ${index + 1} in PDF`}
                >
                  View in PDF
                </button>
              </div>
              {quoteText && (
                <blockquote className="text-sm text-gray-700 italic border-l-4 border-blue-500 pl-3 mt-2">
                  "{quoteText}"
                </blockquote>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default SourceList;

