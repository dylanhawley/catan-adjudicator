'use client';

import { useState } from 'react';
import QueryForm from './components/QueryForm';
import AnswerDisplay from './components/AnswerDisplay';
import SourceList from './components/SourceList';
import PDFViewer from './components/PDFViewer';
import { queryQuestion, getChunk } from '@/lib/api';
import type {
  QueryResponse,
  SourceReference,
  ChunkResponse,
} from '@/lib/types';

export default function Home() {
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(
    null
  );
  const [chunks, setChunks] = useState<ChunkResponse[]>([]);
  const [selectedPage, setSelectedPage] = useState(1);
  const [selectedPdfUrl, setSelectedPdfUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async (question: string) => {
    setIsLoading(true);
    setError(null);
    setQueryResponse(null);
    setChunks([]);

    try {
      const response = await queryQuestion(question);
      setQueryResponse(response);

      // Fetch full chunk details for all sources
      const chunkPromises = response.sources.map((source) =>
        getChunk(source.chunk_id)
      );
      const fetchedChunks = await Promise.all(chunkPromises);
      setChunks(fetchedChunks);

      // Set PDF URL from the first chunk's PDF ID
      if (fetchedChunks.length > 0) {
        const pdfId = fetchedChunks[0].pdf_id;
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        setSelectedPdfUrl(`${apiUrl}/api/pdf/${pdfId}`);
        setSelectedPage(fetchedChunks[0].page_start + 1);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'An error occurred while querying'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSourceClick = (source: SourceReference, chunk: ChunkResponse) => {
    setSelectedPage(chunk.page_start + 1);
    // Scroll to highlighted section would be handled by PDFViewer
  };

  const handleSourceClickFromAnswer = (source: SourceReference) => {
    const chunk = chunks.find((c) => c.chunk_id === source.chunk_id);
    if (chunk) {
      handleSourceClick(source, chunk);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Catan Rules Q&A
          </h1>
          <p className="text-gray-600">
            Ask questions about Catan board game rules with verified citations
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Query and Results */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <QueryForm onSubmit={handleQuery} isLoading={isLoading} />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{error}</p>
              </div>
            )}

            {queryResponse && (
              <>
                <AnswerDisplay
                  response={queryResponse}
                  onSourceClick={handleSourceClickFromAnswer}
                />
                {chunks.length > 0 && (
                  <SourceList
                    sources={queryResponse.sources}
                    chunks={chunks}
                    onSourceClick={handleSourceClick}
                  />
                )}
              </>
            )}
          </div>

          {/* Right Column: PDF Viewer */}
          <div className="lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)]">
            <PDFViewer
              pdfUrl={selectedPdfUrl}
              pageNumber={selectedPage}
              onPageChange={setSelectedPage}
            />
          </div>
        </div>
      </div>
    </main>
  );
}

