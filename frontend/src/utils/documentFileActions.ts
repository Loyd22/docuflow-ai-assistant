
import {
  downloadOriginalDocument,
  viewOriginalDocument,
} from "../api/documentApi";

// Open a PDF or TXT document in a new browser tab.
export async function previewDocument(
  documentId: number,
): Promise<void> {
  // Open the tab immediately to avoid popup blocking.
  const previewTab = window.open("about:blank", "_blank");

  if (!previewTab) {
    throw new Error(
      "The browser blocked the document preview. Please allow popups.",
    );
  }

  // Prevent the preview tab from accessing the app window.
  previewTab.opener = null;

  try {
    previewTab.document.body.textContent =
      "Loading document preview...";

    // Retrieve the file using the authenticated API.
    const fileBlob = await viewOriginalDocument(documentId);

    const fileUrl = URL.createObjectURL(fileBlob);

    if (previewTab.closed) {
      URL.revokeObjectURL(fileUrl);
      return;
    }

    // Display the downloaded file in the preview tab.
    previewTab.location.replace(fileUrl);

    // Keep the URL available while the browser loads the file.
    window.setTimeout(() => {
      URL.revokeObjectURL(fileUrl);
    }, 5 * 60 * 1000);
  } catch (error) {
    if (!previewTab.closed) {
      previewTab.close();
    }

    throw error;
  }
}

// Download the original document using its original filename.
export async function saveOriginalDocument(
  documentId: number,
  originalFileName: string,
): Promise<void> {
  // Retrieve the original file using the user's JWT.
  const fileBlob = await downloadOriginalDocument(documentId);

  const fileUrl = URL.createObjectURL(fileBlob);
  const link = document.createElement("a");

  try {
    link.href = fileUrl;
    link.download = originalFileName;

    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();

    // Release the temporary file URL.
    window.setTimeout(() => {
      URL.revokeObjectURL(fileUrl);
    }, 1000);
  }
}
