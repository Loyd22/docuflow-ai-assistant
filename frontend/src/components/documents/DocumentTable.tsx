import type { Document } from "../../types/document";

import "./DocumentTable.css";

type DocumentTableProps = {
  documents: Document[];

  processingDocumentId: number | null;
  analyzingDocumentId: number | null;
  indexingDocumentId: number | null;

  onProcess: (documentId: number) => void;
  onAnalyze: (documentId: number) => void;
  onIndex: (documentId: number) => void;
  onAsk: (documentId: number) => void;
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function DocumentTable({
  documents,
  processingDocumentId,
  analyzingDocumentId,
  indexingDocumentId,
  onProcess,
  onAnalyze,
  onIndex,
  onAsk,
}: DocumentTableProps) {
  return (
    <div className="document-table-wrapper">
      <table className="document-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Type</th>
            <th>Status</th>
            <th>RAG</th>
            <th>Size</th>
            <th>Uploaded</th>
            <th>Actions</th>
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

            const canProcess =
              document.status === "uploaded";

            const canAnalyze =
              document.status === "text_extracted";

            const canIndex =
              document.status === "analyzed" &&
              !document.is_indexed;

            const canAsk =
              document.is_indexed;

            return (
              <tr key={document.id}>
                <td>
                  {document.original_file_name}
                </td>

                <td>
                  {formatLabel(document.document_type)}
                </td>

                <td>
                  <span className="status-badge">
                    {formatLabel(document.status)}
                  </span>
                </td>

                <td>
                  <span className="status-badge">
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
                        className="document-action-button"
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
                        className="document-action-button"
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
                        className="document-action-button"
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
                        className="document-action-button"
                        onClick={() =>
                            onAsk(document.id)
                        }
                        >
                        Ask
                        </button>
                    )}

                    {!canProcess &&
                        !canAnalyze &&
                        !canIndex &&
                        !canAsk && (
                        <span className="action-unavailable">
                            —
                        </span>
                        )}
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