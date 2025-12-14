/** TypeScript types matching backend models */

export interface BBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface Atom {
  text: string;
  page_num: number;
  bbox: BBox;
  char_start: number;
  char_end: number;
}

export interface Chunk {
  chunk_id: string;
  text: string;
  atoms: Atom[];
  pdf_id: string;
  page_start: number;
  page_end: number;
  section_title: string | null;
}

export interface SourceReference {
  chunk_id: string;
  quote_char_start: number;
  quote_char_end: number;
}

export interface QueryRequest {
  question: string;
  k?: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceReference[];
}

export interface IngestionResponse {
  pdf_id: string;
  filename: string;
  chunk_count: number;
  status: string;
}

export interface ChunkResponse {
  chunk_id: string;
  text: string;
  pdf_id: string;
  page_start: number;
  page_end: number;
  section_title: string | null;
  atoms: Atom[];
}

