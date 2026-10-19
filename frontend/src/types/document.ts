export type DocumentType =
  | "invoice"
  | "contract"
  | "sop"
  | "hr_form"
  | "purchase_request"
  | "policy"
  | "business_report"
  | "support_ticket"
  | "digital_form"
  | "memo"
  | "unknown";

export type DocumentStatus =
  | "uploaded"
  | "processing"
  | "text_extracted"
  | "processing_failed"
  | "ai_processing"
  | "analyzed"
  | "ai_processing_failed";

export type Document = {
  id: number;
  uploaded_by: number;
  original_file_name: string;
  mime_type: string;
  file_size: number;
  document_type: DocumentType;
  status: DocumentStatus;
  is_indexed: boolean;
  created_at: string;
  updated_at: string;
};

export type DocumentDetail = Document & {
  extracted_text: string | null;
  summary: string | null;
  classification_confidence: number | null;
  extracted_data: Record<string, unknown> | null;
  business_rule_result: Record<string, unknown> | null;
};

export type DocumentIndexResponse = {
  document_id: number;
  chunks_indexed: number;
};

export type DocumentQuestionRequest = {
  question: string;
};

export type DocumentQuestionSource = {
  chunk_index: number;
  content: string;
};

export type DocumentQuestionResponse = {
  answer: string;
  sources: DocumentQuestionSource[];
};