
import { useState } from "react";
import "./DocumentTable.css";
import axios from "axios";

import {
  previewDocument,
  saveOriginalDocument,
} from "../../utils/documentFileActions";

type OriginalDocumentActionsProps = {
  documentId: number;
  originalFileName: string;
};

async function getErrorMessage(error: unknown): Promise<string> {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data;

    if (
      typeof responseData === "object" &&
      responseData instanceof Blob
    ) {
      try {
        const data: unknown = JSON.parse(
          await responseData.text(),
        );

        if (
          typeof data === "object" &&
          data !== null &&
          "detail" in data &&
          typeof data.detail === "string"
        ) {
          return data.detail;
        }
      } catch {
        // Use the default message if parsing fails.
      }
    }

    if (typeof responseData?.detail === "string") {
      return responseData.detail;
    }

    return "Unable to access the original document.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to access the original document.";
}

function OriginalDocumentActions({
  documentId,
  originalFileName,
}: OriginalDocumentActionsProps) {
  const [activeAction, setActiveAction] =
    useState<"view" | "download" | null>(null);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const canPreview = /\.(pdf|txt)$/i.test(
    originalFileName,
  );

  // Open the original file after backend authorization.
  async function handleView() {
    if (activeAction !== null) {
      return;
    }

    setActiveAction("view");
    setErrorMessage(null);

    try {
      await previewDocument(documentId);
    } catch (error) {
      setErrorMessage(await getErrorMessage(error));
    } finally {
      setActiveAction(null);
    }
  }

  // Download the original file after backend authorization.
  async function handleDownload() {
    if (activeAction !== null) {
      return;
    }

    setActiveAction("download");
    setErrorMessage(null);

    try {
      await saveOriginalDocument(
        documentId,
        originalFileName,
      );
    } catch (error) {
      setErrorMessage(await getErrorMessage(error));
    } finally {
      setActiveAction(null);
    }
  }

  return (
    <div className="workflow-document-section">
      <h4>Original Document</h4>

      <p>
        Open or download the original uploaded file
        to verify its contents before making a decision.
      </p>

      <div className="document-actions">
        {canPreview && (
          <button
            type="button"
            className="document-action-button"
            onClick={() => void handleView()}
            disabled={activeAction !== null}
          >
            {activeAction === "view"
              ? "Opening..."
              : "View Original"}
          </button>
        )}

        <button
          type="button"
          className="document-action-button"
          onClick={() => void handleDownload()}
          disabled={activeAction !== null}
        >
          {activeAction === "download"
            ? "Downloading..."
            : "Download Original"}
        </button>
      </div>

      {errorMessage && (
        <p
          className="workflow-decision-error"
          role="alert"
        >
          {errorMessage}
        </p>
      )}
    </div>
  );
}

export default OriginalDocumentActions;
