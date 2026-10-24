
import type { Document } from "../../types/document";

import "./DocumentTable.css";

type DocumentTableProps = {
  documents: Document[];

  processingDocumentId: number | null;
  analyzingDocumentId: number | null;
  indexingDocumentId: number | null;
  viewingDocumentId: number | null;
  downloadingDocumentId: number | null;

  onProcess: (documentId: number) => void;
  onAnalyze: (documentId: number) => void;
  onIndex: (documentId: number) => void;
  onAsk: (documentId: number) => void;
  onViewOriginal: (documentId: number) => void;
  onDownloadOriginal: (documentId: number) => void;
};

// Display file sizes in readable units.
function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Convert database values into readable labels.
function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

// Convert timestamps into readable dates.
function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function DocumentTable({
  documents,
  processingDocumentId,
  analyzingDocumentId,
  indexingDocumentId,
  viewingDocumentId,
  downloadingDocumentId,
  onProcess,
  onAnalyze,
  onIndex,
  onAsk,
  onViewOriginal,
  onDownloadOriginal,
}: DocumentTableProps) {
  return (
    <div className="document-table-wrapper" role="region" aria-label="Documents table" tabIndex={0}>
      <table className="document-table">
        <thead>
          <tr>
            <th scope="col">File</th>
            <th scope="col">Type</th>
            <th scope="col">Status</th>
            <th scope="col">RAG</th>
            <th scope="col">Size</th>
            <th scope="col">Uploaded</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>

        <tbody>
          {documents.map((document) => {
            const isProcessing =
              processingDocumentId === document.id;

            const isAnalyzing =
              analyzingDocumentId === document.id;

            const isIndexing =
              indexingDocumentId === document.id;

            const isViewing =
              viewingDocumentId === document.id;

            const isDownloading =
              downloadingDocumentId === document.id;

            const canProcess =
              document.status === "uploaded";

            const canAnalyze =
              document.status === "text_extracted";

            const canIndex =
              document.status === "analyzed" &&
              !document.is_indexed;

            const canAsk = document.is_indexed;

            // The backend supports inline PDF and TXT previews.
            const canViewOriginal = /\.(pdf|txt)$/i.test(
              document.original_file_name,
            );

            return (
              <tr key={document.id}>
                <td className="document-file-name">{document.original_file_name}</td>

                <td>
                  {formatLabel(document.document_type)}
                </td>

                <td>
                  <span className={`status-badge status-badge-${document.status}`}>
                    {formatLabel(document.status)}
                  </span>
                </td>

                <td>
                  <span className={`status-badge ${document.is_indexed ? "status-badge-indexed" : "status-badge-neutral"}`}>
                    {document.is_indexed
                      ? "Indexed"
                      : "Not Indexed"}
                  </span>
                </td>

                <td>
                  {formatFileSize(document.file_size)}
                </td>

                <td>
                  {formatDate(document.created_at)}
                </td>

                <td>
                  <div className="document-actions">
                    {canProcess && (
                      <button
                        type="button"
                        className="document-action-button document-action-primary"
                        onClick={() =>
                          onProcess(document.id)
                        }
                        disabled={isProcessing}
                      >
                        {isProcessing
                          ? "Processing..."
                          : "Process"}
                      </button>
                    )}

                    {canAnalyze && (
                      <button
                        type="button"
                        className="document-action-button document-action-primary"
                        onClick={() =>
                          onAnalyze(document.id)
                        }
                        disabled={isAnalyzing}
                      >
                        {isAnalyzing
                          ? "Analyzing..."
                          : "Analyze"}
                      </button>
                    )}

                    {canIndex && (
                      <button
                        type="button"
                        className="document-action-button document-action-primary"
                        onClick={() =>
                          onIndex(document.id)
                        }
                        disabled={isIndexing}
                      >
                        {isIndexing
                          ? "Indexing..."
                          : "Index"}
                      </button>
                    )}

                    {canAsk && (
                      <button
                        type="button"
                        className="document-action-button document-action-primary"
                        onClick={() =>
                          onAsk(document.id)
                        }
                      >
                        Ask
                      </button>
                    )}

                    {canViewOriginal && (
                      <button
                        type="button"
                        className="document-action-button"
                        onClick={() =>
                          onViewOriginal(document.id)
                        }
                        disabled={isViewing}
                      >
                        {isViewing
                          ? "Opening..."
                          : "View Original"}
                      </button>
                    )}

                    <button
                      type="button"
                      className="document-action-button"
                      onClick={() =>
                        onDownloadOriginal(document.id)
                      }
                      disabled={isDownloading}
                    >
                      {isDownloading
                        ? "Downloading..."
                        : "Download Original"}
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default DocumentTable;
