'use client';

import type { QueryResponse, SourceReference } from '@/lib/types';

interface AnswerDisplayProps {
  response: QueryResponse | null;
  onSourceClick: (source: SourceReference) => void;
}

const AnswerDisplay = ({ response, onSourceClick }: AnswerDisplayProps) => {
  if (!response) {
    return null;
  }

  return (
    <div className="w-full space-y-4">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Answer</h2>
        <p className="text-gray-800 whitespace-pre-wrap">{response.answer}</p>
      </div>

      {response.sources.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-3">Sources</h3>
          <ul className="space-y-2">
            {response.sources.map((source, index) => (
              <li key={index}>
                <button
                  onClick={() => onSourceClick(source)}
                  className="text-blue-600 hover:text-blue-800 hover:underline text-sm"
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

