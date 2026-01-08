'use client';

import { useState, useRef, useCallback } from 'react';
import QueryForm from './components/QueryForm';
import ChatMessage from './components/ChatMessage';
import CatanLogo from './components/CatanLogo';
import PDFModal from './components/PDFModal';
import Card from './components/ui/Card';
import { queryQuestionStream, getChunk, ConversationMessage } from '@/lib/api';
import { computePDFHighlights } from '@/lib/pdfHighlights';
import type {
  SourceReference,
  ChunkResponse,
  CitationRange,
  BBox,
  Message,
} from '@/lib/types';

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // PDF Modal state
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfPage, setPdfPage] = useState(1);
  const [pdfHighlights, setPdfHighlights] = useState<BBox[]>([]);

  const answerRef = useRef<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleQuery = async (question: string) => {
    const messageId = Date.now().toString();

    // Build conversation history from previous messages
    const conversationHistory: ConversationMessage[] = messages.flatMap((msg) => [
      { role: 'user' as const, content: msg.question },
      { role: 'assistant' as const, content: msg.answer },
    ]);

    // Create new message
    const newMessage: Message = {
      id: messageId,
      question,
      answer: '',
      sources: [],
      chunks: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, newMessage]);
    setIsLoading(true);
    setError(null);
    answerRef.current = '';

    setTimeout(scrollToBottom, 100);

    try {
      await queryQuestionStream(
        question,
        {
          onSources: async (receivedSources: SourceReference[]) => {
            // Fetch chunks for sources
            if (receivedSources.length > 0) {
              try {
                const chunkPromises = receivedSources.map((source) =>
                  getChunk(source.chunk_id)
                );
                const fetchedChunks = await Promise.all(chunkPromises);

                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === messageId
                      ? { ...msg, sources: receivedSources, chunks: fetchedChunks }
                      : msg
                  )
                );
              } catch (err) {
                console.error('Error fetching chunks:', err);
              }
            }
          },
          onToken: (token: string) => {
            answerRef.current += token;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId
                  ? { ...msg, answer: answerRef.current }
                  : msg
              )
            );
          },
          onDone: () => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            );
            setIsLoading(false);
          },
          onError: (errorMsg: string) => {
            setError(errorMsg);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === messageId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            );
            setIsLoading(false);
          },
        },
        5,
        conversationHistory
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'An error occurred while querying'
      );
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, isStreaming: false }
            : msg
        )
      );
      setIsLoading(false);
    }
  };

  const handleCitationClick = useCallback(
    (range: CitationRange) => {
      // Find the message containing this source
      for (const message of messages) {
        const chunk = message.chunks.find((c) => c.chunk_id === range.source.chunk_id);
        if (chunk) {
          const highlights = computePDFHighlights(range.source, chunk);
          const pageHighlight = highlights.find((h) => h.pageNum === chunk.page_start);

          setPdfUrl(`${apiUrl}/api/pdf/${chunk.pdf_id}`);
          setPdfPage(chunk.page_start + 1);
          setPdfHighlights(pageHighlight?.bboxes || []);
          setPdfModalOpen(true);
          break;
        }
      }
    },
    [messages]
  );

  const handlePdfPageChange = useCallback((newPage: number) => {
    setPdfPage(newPage);
    setPdfHighlights([]);
  }, []);

  return (
    <main className="min-h-screen bg-warm-50 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-warm-50 border-b border-warm-200 px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <CatanLogo size={32} />
          <div>
            <h1 className="text-lg font-semibold text-warm-700">
              Catan Rules Q&A
            </h1>
          </div>
        </div>
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-auto px-4 py-6">
        <div className="max-w-2xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <CatanLogo size={64} className="mx-auto mb-4 opacity-50" />
              <p className="text-warm-400 text-lg mb-2">
                Ask a question about Catan rules
              </p>
              <p className="text-warm-300 text-sm">
                Get answers with verified citations from the rulebook
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onCitationClick={handleCitationClick}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}

          {error && (
            <Card className="mb-4 bg-red-50 border-red-200">
              <p className="text-red-700">{error}</p>
            </Card>
          )}
        </div>
      </div>

      {/* Sticky input */}
      <div className="sticky bottom-0 bg-warm-50 border-t border-warm-200 px-4 py-4">
        <div className="max-w-2xl mx-auto">
          <Card>
            <QueryForm onSubmit={handleQuery} isLoading={isLoading} />
          </Card>
        </div>
      </div>

      <PDFModal
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
        pdfUrl={pdfUrl}
        pageNumber={pdfPage}
        highlights={pdfHighlights}
        onPageChange={handlePdfPageChange}
      />
    </main>
  );
}
