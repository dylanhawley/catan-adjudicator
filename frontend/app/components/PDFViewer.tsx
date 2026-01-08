'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import type { BBox } from '@/lib/types';

if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
}

interface PDFViewerProps {
  pdfUrl: string | null;
  pageNumber: number;
  highlights?: BBox[];
  onPageChange?: (page: number) => void;
  compact?: boolean;
}

const PDFViewer = ({
  pdfUrl,
  pageNumber,
  highlights = [],
  onPageChange,
  compact = false,
}: PDFViewerProps) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [page, setPage] = useState(pageNumber);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pageSize, setPageSize] = useState<{ width: number; height: number } | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setPage(pageNumber);
  }, [pageNumber]);

  const handleDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  };

  const handleDocumentLoadError = (error: Error) => {
    setError(`Failed to load PDF: ${error.message}`);
    setLoading(false);
  };

  const handlePageRenderSuccess = useCallback(() => {
    // Get the rendered page dimensions from the canvas
    const pageCanvas = containerRef.current?.querySelector('.react-pdf__Page__canvas') as HTMLCanvasElement;
    if (pageCanvas) {
      setPageSize({
        width: pageCanvas.width,
        height: pageCanvas.height,
      });
    }
  }, []);

  // Draw highlights on canvas overlay
  useEffect(() => {
    if (!canvasRef.current || !pageSize || highlights.length === 0) {
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        ctx?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match page
    canvas.width = pageSize.width;
    canvas.height = pageSize.height;

    // Clear previous highlights
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw yellow highlights
    ctx.fillStyle = 'rgba(255, 248, 220, 0.6)';
    ctx.strokeStyle = 'rgba(230, 217, 168, 0.8)';
    ctx.lineWidth = 1;

    // PDF coordinates: origin at bottom-left, y increases upward
    // Canvas coordinates: origin at top-left, y increases downward
    // The bbox values are in PDF points (typically 72 points per inch)
    // We need to scale them to the rendered canvas size

    // Assuming PDF page is 612x792 points (letter size)
    const pdfWidth = 612;
    const pdfHeight = 792;
    const scaleX = pageSize.width / pdfWidth;
    const scaleY = pageSize.height / pdfHeight;

    for (const bbox of highlights) {
      const x = bbox.x0 * scaleX;
      const y = (pdfHeight - bbox.y1) * scaleY; // Flip y coordinate
      const width = (bbox.x1 - bbox.x0) * scaleX;
      const height = (bbox.y1 - bbox.y0) * scaleY;

      ctx.fillRect(x, y, width, height);
      ctx.strokeRect(x, y, width, height);
    }
  }, [highlights, pageSize]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= (numPages || 1)) {
      setPage(newPage);
      onPageChange?.(newPage);
    }
  };

  if (!pdfUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-warm-100 rounded-xl">
        <p className="text-warm-400">No PDF selected</p>
      </div>
    );
  }

  return (
    <div className={`w-full h-full flex flex-col bg-white ${compact ? '' : 'rounded-xl border border-warm-200 shadow-soft'}`}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-warm-200">
        <div className="flex items-center gap-3">
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 text-sm bg-warm-100 text-warm-600 rounded-lg hover:bg-warm-200 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Previous page"
          >
            Prev
          </button>
          <span className="text-sm text-warm-500">
            {page} / {numPages || '?'}
          </span>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= (numPages || 1)}
            className="px-3 py-1.5 text-sm bg-warm-100 text-warm-600 rounded-lg hover:bg-warm-200 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Next page"
          >
            Next
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 flex justify-center bg-warm-50" ref={containerRef}>
        {loading && (
          <div className="flex items-center justify-center h-full">
            <p className="text-warm-400">Loading PDF...</p>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-full">
            <p className="text-red-500">{error}</p>
          </div>
        )}

        <div className="relative">
          <Document
            file={pdfUrl}
            onLoadSuccess={handleDocumentLoadSuccess}
            onLoadError={handleDocumentLoadError}
            loading={
              <div className="flex items-center justify-center h-96">
                <p className="text-warm-400">Loading PDF...</p>
              </div>
            }
          >
            <Page
              pageNumber={page}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="shadow-soft-lg rounded-lg overflow-hidden"
              onRenderSuccess={handlePageRenderSuccess}
            />
          </Document>
          {pageSize && (
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 pointer-events-none"
              style={{
                width: pageSize.width / 2,
                height: pageSize.height / 2,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;
