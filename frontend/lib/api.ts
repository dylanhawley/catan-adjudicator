/** API client for backend communication */
import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  IngestionResponse,
  ChunkResponse,
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

