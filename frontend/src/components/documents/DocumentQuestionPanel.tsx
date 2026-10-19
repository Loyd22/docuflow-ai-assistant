import {
  type FormEvent,
  useState,
} from "react";
import axios from "axios";

import { askDocumentQuestion } from "../../api/documentApi";
import type {
  Document,
  DocumentQuestionResponse,
} from "../../types/document";

import "./DocumentQuestionPanel.css";

type DocumentQuestionPanelProps = {
  document: Document;
  onClose: () => void;
};

function DocumentQuestionPanel({
  document,
  onClose,
}: DocumentQuestionPanelProps) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] =
    useState<DocumentQuestionResponse | null>(null);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setErrorMessage("Please enter a question.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setResponse(null);

    try {
      const questionResponse =
        await askDocumentQuestion(
          document.id,
          {
            question: trimmedQuestion,
          },
        );

      setResponse(questionResponse);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
          setErrorMessage(detail);
        } else {
          setErrorMessage(
            "Unable to answer the question.",
          );
        }
      } else {
        setErrorMessage(
          "Unable to answer the question.",
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="question-panel">
      <div className="question-panel-header">
        <div>
          <h3>Ask Document</h3>

          <p>
            {document.original_file_name}
          </p>
        </div>

        <button
          type="button"
          className="question-close-button"
          onClick={onClose}
        >
          Close
        </button>
      </div>

      <form
        className="question-form"
        onSubmit={handleSubmit}
      >
        <label htmlFor="document-question">
          Question
        </label>

        <textarea
          id="document-question"
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Ask something about this document..."
          rows={4}
          disabled={isSubmitting}
        />

        <button
          type="submit"
          disabled={
            isSubmitting || !question.trim()
          }
        >
          {isSubmitting
            ? "Generating answer..."
            : "Ask"}
        </button>
      </form>

      {errorMessage && (
        <p
          className="question-error"
          role="alert"
        >
          {errorMessage}
        </p>
      )}

      {response && (
        <div className="question-response">
          <section className="answer-card">
            <h4>Answer</h4>

            <p>{response.answer}</p>
          </section>

          <section className="sources-section">
            <h4>Sources</h4>

            {response.sources.length === 0 ? (
              <p>No supporting sources returned.</p>
            ) : (
              <div className="source-list">
                {response.sources.map((source) => (
                  <article
                    className="source-card"
                    key={source.chunk_index}
                  >
                    <strong>
                      Chunk {source.chunk_index}
                    </strong>

                    <p>
                      {source.content}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </section>
  );
}

export default DocumentQuestionPanel;