import { apiClient } from "./client";

import type {
  Document,
  DocumentDetail,
  DocumentIndexResponse,
  DocumentQuestionRequest,
  DocumentQuestionResponse,
} from "../types/document";

export async function getDocuments(): Promise<Document[]> {
  const response =
    await apiClient.get<Document[]>("/documents");

  return response.data;
}

export async function getDocumentDetails(
  documentId: number,
): Promise<DocumentDetail> {
  const response =
    await apiClient.get<DocumentDetail>(
      `/documents/${documentId}`,
    );

  return response.data;
}

export async function uploadDocument(
  file: File,
): Promise<Document> {
  const formData = new FormData();

  // Must match the FastAPI parameter name.
  formData.append("uploaded_file", file);

  const response = await apiClient.post<Document>(
    "/documents",
    formData,
  );

  return response.data;
}

export async function processDocument(
  documentId: number,
): Promise<Document> {
  const response = await apiClient.post<Document>(
    `/documents/${documentId}/process`,
  );

  return response.data;
}

export async function analyzeDocument(
  documentId: number,
): Promise<Document> {
  const response = await apiClient.post<Document>(
    `/documents/${documentId}/analyze`,
  );

  return response.data;
}

export async function indexDocument(
  documentId: number,
): Promise<DocumentIndexResponse> {
  const response =
    await apiClient.post<DocumentIndexResponse>(
      `/documents/${documentId}/index`,
    );

  return response.data;
}

export async function askDocumentQuestion(
  documentId: number,
  request: DocumentQuestionRequest,
): Promise<DocumentQuestionResponse> {
  const response =
    await apiClient.post<DocumentQuestionResponse>(
      `/documents/${documentId}/ask`,
      request,
    );

  return response.data;
}