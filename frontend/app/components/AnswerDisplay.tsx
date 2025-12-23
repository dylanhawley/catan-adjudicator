'use client';

import type { SourceReference } from '@/lib/types';

interface AnswerDisplayProps {
  question: string;
  answer: string;
  sources: SourceReference[];
  isStreaming?: boolean;
  onSourceClick: (source: SourceReference) => void;
}

const AnswerDisplay = ({
  question,
  answer,
  sources,
  isStreaming = false,
  onSourceClick,
}: AnswerDisplayProps) => {
  if (!answer && sources.length === 0) {
    return null;
  }

  return (
    <div className="w-full space-y-4">
      <div className="bg-white rounded-lg shadow p-6">
        {question && (
          <div className="mb-4 pb-4 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Question</h3>
            <p className="text-gray-900 text-lg">{question}</p>
          </div>
        )}
        <h2 className="text-xl font-semibold mb-4">Answer</h2>
        <div className="text-gray-800 whitespace-pre-wrap">
          {answer}
          {isStreaming && (
            <span
              className="inline-block w-0.5 h-5 ml-0.5 bg-black animate-pulse"
              aria-label="Loading more content"
            />
          )}
        </div>
      </div>

      {sources.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-3">Sources</h3>
          <ul className="space-y-2">
            {sources.map((source, index) => (
              <li key={source.chunk_id || index}>
                <button
                  onClick={() => onSourceClick(source)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      onSourceClick(source);
                    }
                  }}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                  tabIndex={0}
                  aria-label={`View source ${index + 1}`}
                >
                  Source {index + 1} (Chunk: {source.chunk_id.slice(0, 8)}...)
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AnswerDisplay;

