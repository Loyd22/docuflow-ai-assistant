import {
  type ChangeEvent,
  type FormEvent,
  useEffect,
  useState,
} from "react";
import axios from "axios";

import {
  analyzeDocument,
  getDocuments,
  indexDocument,
  processDocument,
  uploadDocument,
} from "../api/documentApi";
import DocumentQuestionPanel from "../components/documents/DocumentQuestionPanel";
import DocumentTable from "../components/documents/DocumentTable";
import type { Document } from "../types/document";

import "./DocumentsPage.css";

function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  const [
    processingDocumentId,
    setProcessingDocumentId,
  ] = useState<number | null>(null);

  const [
    analyzingDocumentId,
    setAnalyzingDocumentId,
  ] = useState<number | null>(null);

  const [
    indexingDocumentId,
    setIndexingDocumentId,
  ] = useState<number | null>(null);

  const [
    questionDocumentId,
    setQuestionDocumentId,
  ] = useState<number | null>(null);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  const questionDocument =
    documents.find(
      (document) =>
        document.id === questionDocumentId,
    ) ?? null;

  async function loadDocuments() {
    try {
      setErrorMessage(null);

      const documentList = await getDocuments();

      setDocuments(documentList);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to load documents.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to load documents.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(file);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  async function handleUpload(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!selectedFile) {
      setErrorMessage(
        "Please select a file first.",
      );

      return;
    }

    setIsUploading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const uploadedDocument =
        await uploadDocument(selectedFile);

      setSuccessMessage(
        `${uploadedDocument.original_file_name} uploaded successfully.`,
      );

      setSelectedFile(null);

      await loadDocuments();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to upload document.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to upload document.",
        );
      }
    } finally {
      setIsUploading(false);
    }
  }

  async function handleProcessDocument(
    documentId: number,
  ) {
    setProcessingDocumentId(documentId);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const processedDocument =
        await processDocument(documentId);

      setDocuments((currentDocuments) =>
        currentDocuments.map((document) =>
          document.id === processedDocument.id
            ? processedDocument
            : document,
        ),
      );

      setSuccessMessage(
        `${processedDocument.original_file_name} processed successfully.`,
      );
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to process document.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to process document.",
        );
      }
    } finally {
      setProcessingDocumentId(null);
    }
  }

  async function handleAnalyzeDocument(
    documentId: number,
  ) {
    setAnalyzingDocumentId(documentId);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const analyzedDocument =
        await analyzeDocument(documentId);

      setDocuments((currentDocuments) =>
        currentDocuments.map((document) =>
          document.id === analyzedDocument.id
            ? analyzedDocument
            : document,
        ),
      );

      setSuccessMessage(
        `${analyzedDocument.original_file_name} analyzed successfully.`,
      );
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to analyze document.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to analyze document.",
        );
      }
    } finally {
      setAnalyzingDocumentId(null);
    }
  }

  async function handleIndexDocument(
    documentId: number,
  ) {
    setIndexingDocumentId(documentId);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const indexResult =
        await indexDocument(documentId);

      // Reload so is_indexed comes from the backend.
      await loadDocuments();

      setSuccessMessage(
        `Document indexed successfully. ${indexResult.chunks_indexed} chunk${
          indexResult.chunks_indexed === 1 ? "" : "s"
        } indexed.`,
      );
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to index document.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to index document.",
        );
      }
    } finally {
      setIndexingDocumentId(null);
    }
  }

  function handleAskDocument(
    documentId: number,
  ) {
    setQuestionDocumentId(documentId);
    setErrorMessage(null);
    setSuccessMessage(null);
  }

  return (
    <section className="documents-page">
      <div className="documents-heading">
        <div>
          <h2>Documents</h2>

          <p>
            Upload and manage your DocuFlow documents.
          </p>
        </div>
      </div>

      <section className="upload-panel">
        <div>
          <h3>Upload Document</h3>

          <p>
            Supported files: PDF, DOCX, and TXT.
            Maximum size: 10 MB.
          </p>
        </div>

        <form
          className="upload-form"
          onSubmit={handleUpload}
        >
          <input
            key={selectedFile?.name ?? "empty"}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            disabled={isUploading}
          />

          <button
            type="submit"
            disabled={
              !selectedFile || isUploading
            }
          >
            {isUploading
              ? "Uploading..."
              : "Upload"}
          </button>
        </form>

        {errorMessage && (
          <p
            className="message error-message"
            role="alert"
          >
            {errorMessage}
          </p>
        )}

        {successMessage && (
          <p
            className="message success-message"
            role="status"
          >
            {successMessage}
          </p>
        )}
      </section>

      <section className="documents-list">
        <div className="documents-list-heading">
          <h3>Your Documents</h3>

          <span>
            {documents.length} document
            {documents.length === 1 ? "" : "s"}
          </span>
        </div>

        {isLoading ? (
          <p>Loading documents...</p>
        ) : documents.length === 0 ? (
          <div className="empty-documents">
            <h3>No documents yet</h3>

            <p>
              Upload your first document to begin
              processing it with DocuFlow.
            </p>
          </div>
        ) : (
          <>
            <DocumentTable
              documents={documents}
              processingDocumentId={
                processingDocumentId
              }
              analyzingDocumentId={
                analyzingDocumentId
              }
              indexingDocumentId={
                indexingDocumentId
              }
              onProcess={handleProcessDocument}
              onAnalyze={handleAnalyzeDocument}
              onIndex={handleIndexDocument}
              onAsk={handleAskDocument}
            />

            {questionDocument && (
              <DocumentQuestionPanel
                document={questionDocument}
                onClose={() =>
                  setQuestionDocumentId(null)
                }
              />
            )}
          </>
        )}
      </section>
    </section>
  );
}

export default DocumentsPage;