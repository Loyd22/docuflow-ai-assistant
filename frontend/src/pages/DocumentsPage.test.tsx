import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import type { AxiosProgressEvent } from "axios";
import * as api from "../api/documentApi";
import type { Document } from "../types/document";
import DocumentsPage from "./DocumentsPage";

vi.mock("../api/documentApi", () => ({
  getDocuments: vi.fn(), uploadDocument: vi.fn(), processDocument: vi.fn(),
  analyzeDocument: vi.fn(), indexDocument: vi.fn(), askDocumentQuestion: vi.fn(),
}));
const document: Document = {
  id: 1, uploaded_by: 1, original_file_name: "report.txt", mime_type: "text/plain",
  file_size: 100, document_type: "unknown", status: "uploaded", is_indexed: false,
  created_at: "2026-01-01", updated_at: "2026-01-01",
};
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
beforeEach(() => { vi.resetAllMocks(); vi.mocked(api.getDocuments).mockResolvedValue([document]); });

it("shows only reported upload progress and waits for server confirmation", async () => {
  const upload = deferred<Document>();
  vi.mocked(api.uploadDocument).mockReturnValue(upload.promise);
  render(<DocumentsPage />);
  await screen.findByText("report.txt");
  const input = screen.getByLabelText("Choose document to upload");
  fireEvent.change(input, { target: { files: [new File(["text"], "new.txt")] } });
  expect(screen.getByText("new.txt")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Upload" }));
  expect(input).toBeDisabled();
  expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  const progress = vi.mocked(api.uploadDocument).mock.calls[0][1]!;
  act(() => progress({ loaded: 50, total: 100 } as AxiosProgressEvent));
  expect(screen.getByRole("progressbar")).toHaveAttribute("value", "50");
  act(() => progress({ loaded: 100, total: 100 } as AxiosProgressEvent));
  expect(screen.getByText(/Waiting for server confirmation/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Uploading..." })).toBeDisabled();
  await act(async () => upload.resolve({ ...document, original_file_name: "new.txt" }));
  expect(screen.getByText("new.txt uploaded successfully.")).toBeInTheDocument();
  expect(input).toHaveValue("");
  expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
});

it.each([
  ["uploaded", "Process", "processDocument", "Processing..."],
  ["text_extracted", "Analyze", "analyzeDocument", "Analyzing..."],
  ["analyzed", "Index", "indexDocument", "Indexing..."],
] as const)("disables competing %s requests and restores controls on failure", async (status, label, method, busy) => {
  vi.mocked(api.getDocuments).mockResolvedValue([
    { ...document, status }, { ...document, id: 2, original_file_name: "other.txt", status },
  ]);
  const request = deferred<never>();
  vi.mocked(api[method]).mockReturnValue(request.promise);
  render(<DocumentsPage />);
  const buttons = await screen.findAllByRole("button", { name: label });
  fireEvent.click(buttons[0]);
  expect(screen.getByRole("button", { name: busy })).toBeDisabled();
  expect(buttons[1]).toBeDisabled();
  fireEvent.click(buttons[1]);
  expect(api[method]).toHaveBeenCalledTimes(1);
  await act(async () => request.reject(new Error("offline")));
  expect(await screen.findByRole("alert")).toHaveTextContent(/Unable to/);
  expect(buttons[0]).toBeEnabled();
  expect(buttons[1]).toBeEnabled();
});

it("shows Q&A pending feedback and clears the answer when switching documents", async () => {
  vi.mocked(api.getDocuments).mockResolvedValue([
    { ...document, is_indexed: true }, { ...document, id: 2, original_file_name: "other.txt", is_indexed: true },
  ]);
  const request = deferred<{ answer: string; sources: [] }>();
  vi.mocked(api.askDocumentQuestion).mockReturnValue(request.promise);
  render(<DocumentsPage />);
  const askButtons = await screen.findAllByRole("button", { name: "Ask" });
  fireEvent.click(askButtons[0]);
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: "What is this?" } });
  fireEvent.submit(screen.getByLabelText("Question").closest("form")!);
  expect(screen.getByLabelText("Question")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Generating answer..." })).toBeDisabled();
  expect(screen.getByText(/Searching document sources/)).toBeInTheDocument();
  await act(async () => request.resolve({ answer: "The first answer", sources: [] }));
  expect(screen.getByText("The first answer")).toBeInTheDocument();
  fireEvent.click(askButtons[1]);
  await waitFor(() => expect(screen.queryByText("The first answer")).not.toBeInTheDocument());
  expect(screen.getByLabelText("Question")).toHaveValue("");
});


it("keeps the selected file available for retry after an upload failure", async () => {
  vi.mocked(api.uploadDocument).mockRejectedValue(new Error("offline"));
  render(<DocumentsPage />);
  await screen.findByText("report.txt");
  const input = screen.getByLabelText("Choose document to upload");
  fireEvent.change(input, { target: { files: [new File(["text"], "retry.txt")] } });
  fireEvent.click(screen.getByRole("button", { name: "Upload" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Unable to upload document.");
  expect(screen.getByText("retry.txt")).toBeInTheDocument();
  expect(input).toBeEnabled();
  expect(screen.getByRole("button", { name: "Upload" })).toBeEnabled();
});

it("restores the question for retry when Q&A fails", async () => {
  vi.mocked(api.getDocuments).mockResolvedValue([{ ...document, is_indexed: true }]);
  vi.mocked(api.askDocumentQuestion).mockRejectedValue(new Error("offline"));
  render(<DocumentsPage />);
  fireEvent.click(await screen.findByRole("button", { name: "Ask" }));
  const input = screen.getByLabelText("Question");
  fireEvent.change(input, { target: { value: "Summarize this" } });
  fireEvent.submit(input.closest("form")!);
  expect(await screen.findByRole("alert")).toHaveTextContent("Unable to answer the question.");
  expect(input).toBeEnabled();
  expect(input).toHaveValue("Summarize this");
});
