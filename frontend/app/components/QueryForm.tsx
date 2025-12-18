'use client';

import { useState } from 'react';

interface QueryFormProps {
  onSubmit: (question: string) => void;
  isLoading?: boolean;
}

const QueryForm = ({ onSubmit, isLoading = false }: QueryFormProps) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSubmit(question.trim());
      setQuestion('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (question.trim() && !isLoading) {
        onSubmit(question.trim());
        setQuestion('');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col gap-2">
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g., How many resource cards can I hold?"
          disabled={isLoading}
          rows={3}
          className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          aria-label="Question input"
        />
        <div className="flex justify-between items-center">
          <p className="text-xs text-gray-500">
            Press Enter to submit, Shift + Enter for new line
          </p>
          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            aria-label="Submit question"
          >
            {isLoading ? 'Searching...' : 'Ask'}
          </button>
        </div>
      </div>
    </form>
  );
};

export default QueryForm;

