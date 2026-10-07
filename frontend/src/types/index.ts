export interface TokenSaliency {
  token: string;
  importance: number;
}

export interface SourceAttribution {
  chunk_id: string;
  source: string;
  confidence: number;
  reason: string;
  excerpt: string;
}

export interface Explanation {
  confidence_score: number;
  calibration: "high" | "medium" | "low";
  sources: SourceAttribution[];
  token_saliency: TokenSaliency[];
  alternate_paths: string[];
  explanation_latency_ms: number;
}

export interface RetrievalMetadata {
  num_docs_considered: number;
  num_docs_used: number;
  reranker_used: boolean;
  latency_ms: number;
  degradation_strategy: string | null;
}

export interface QueryResponse {
  response: string;
  confidence: number;
  tier_used: string;
  latency_ms: number;
  warnings: string[];
  explanation: Explanation | null;
  retrieval_metadata: RetrievalMetadata;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  queryResponse?: QueryResponse;
  timestamp: number;
}

export interface AuthState {
  token: string | null;
  username: string | null;
  role: string | null;
}

export interface DocumentRecord {
  id: string;
  filename: string;
  status: string;
  chunks_indexed: number;
  category: string;
  created_at: string;
}
