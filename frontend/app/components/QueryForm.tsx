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
      <div className="flex flex-col gap-3">
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about Catan rules..."
          disabled={isLoading}
          rows={3}
          className="w-full px-4 py-3 bg-warm-50 border border-warm-200 rounded-xl text-warm-700 placeholder:text-warm-400 focus:bg-white focus:border-warm-300 focus:ring-2 focus:ring-accent/20 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
          aria-label="Question input"
        />
        <div className="flex justify-between items-center">
          <p className="text-xs text-warm-400">
            Enter to submit, Shift + Enter for new line
          </p>
          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="px-5 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed font-medium text-sm"
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
