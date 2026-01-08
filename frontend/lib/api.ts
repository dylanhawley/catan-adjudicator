/** API client for backend communication */
import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  IngestionResponse,
  ChunkResponse,
  SourceReference,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryQuestion = async (
  question: string,
  k: number = 5
): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>('/api/query', {
    question,
    k,
  } as QueryRequest);
  return response.data;
};

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface StreamCallbacks {
  onSources: (sources: SourceReference[]) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export const queryQuestionStream = async (
  question: string,
  callbacks: StreamCallbacks,
  k: number = 5,
  conversationHistory: ConversationMessage[] = []
): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/query/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      k,
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('Response body is null');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      
      // Process complete SSE events from the buffer
      const lines = buffer.split('\n');
      buffer = '';

      let currentEvent = '';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          currentData = line.slice(6);
        } else if (line === '' && currentEvent && currentData !== '') {
          // Empty line signals end of event
          handleSSEEvent(currentEvent, currentData, callbacks);
          currentEvent = '';
          currentData = '';
        } else if (line !== '') {
          // Incomplete event, keep in buffer
          buffer = line;
        }
      }

      // Keep any incomplete event in the buffer
      if (currentEvent || currentData) {
        if (currentEvent) buffer = `event: ${currentEvent}\n`;
        if (currentData) buffer += `data: ${currentData}\n`;
      }
    }
  } finally {
    reader.releaseLock();
  }
};

const handleSSEEvent = (
  event: string,
  data: string,
  callbacks: StreamCallbacks
): void => {
  switch (event) {
    case 'sources':
      try {
        const sources = JSON.parse(data) as SourceReference[];
        callbacks.onSources(sources);
      } catch (e) {
        console.error('Failed to parse sources:', e);
      }
      break;
    case 'token':
      // Unescape newlines that were escaped for SSE transport
      const unescapedToken = data.replace(/\\n/g, '\n');
      callbacks.onToken(unescapedToken);
      break;
    case 'done':
      callbacks.onDone();
      break;
    case 'error':
      try {
        const errorData = JSON.parse(data);
        callbacks.onError(errorData.error || 'Unknown error');
      } catch {
        callbacks.onError(data);
      }
      break;
  }
};

export const getChunk = async (chunkId: string): Promise<ChunkResponse> => {
  const response = await apiClient.get<ChunkResponse>(`/api/chunks/${chunkId}`);
  return response.data;
};

export const ingestPDF = async (file: File): Promise<IngestionResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<IngestionResponse>(
    '/api/ingest',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

