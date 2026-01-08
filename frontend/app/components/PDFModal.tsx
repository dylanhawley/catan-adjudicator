'use client';

import { useCallback } from 'react';
import Modal from './ui/Modal';
import PDFViewer from './PDFViewer';
import type { BBox } from '@/lib/types';

interface PDFModalProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string | null;
  pageNumber: number;
  highlights: BBox[];
  onPageChange: (page: number) => void;
  title?: string;
}

export default function PDFModal({
  isOpen,
  onClose,
  pdfUrl,
  pageNumber,
  highlights,
  onPageChange,
  title,
}: PDFModalProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        onPageChange(pageNumber - 1);
      } else if (e.key === 'ArrowRight') {
        onPageChange(pageNumber + 1);
      }
    },
    [pageNumber, onPageChange]
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div
        className="flex flex-col h-full"
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-warm-200">
          <h2 className="text-lg font-medium text-warm-700">
            {title || 'Source Document'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-warm-400 hover:text-warm-600 hover:bg-warm-100 rounded-lg"
            aria-label="Close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-hidden">
          <PDFViewer
            pdfUrl={pdfUrl}
            pageNumber={pageNumber}
            highlights={highlights}
            onPageChange={onPageChange}
            compact
          />
        </div>
      </div>
    </Modal>
  );
}
