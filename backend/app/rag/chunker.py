"""Text chunking utilities for document retrieval."""

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


class TextChunker:
    """Split document text into overlapping retrieval chunks."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("Chunk size must be greater than zero.")

        if chunk_overlap < 0:
            raise ValueError("Chunk overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        """Split text while preferring paragraph boundaries."""

        cleaned_text = text.strip()

        if not cleaned_text:
            return []

        paragraphs = [
            paragraph.strip()
            for paragraph in cleaned_text.split("\n\n")
            if paragraph.strip()
        ]

        if len(paragraphs) <= 1:
            return self._split_by_characters(cleaned_text)

        return self._split_by_paragraphs(paragraphs)

    def _split_by_paragraphs(
        self,
        paragraphs: list[str],
    ) -> list[str]:
        """Build chunks from complete paragraphs when possible."""

        chunks: list[str] = []
        current_paragraphs: list[str] = []

        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                if current_paragraphs:
                    chunks.append(self._join_paragraphs(current_paragraphs))
                    current_paragraphs = []

                chunks.extend(self._split_by_characters(paragraph))
                continue

            candidate_paragraphs = [
                *current_paragraphs,
                paragraph,
            ]

            candidate_text = self._join_paragraphs(candidate_paragraphs)

            if len(candidate_text) <= self.chunk_size:
                current_paragraphs.append(paragraph)
                continue

            if current_paragraphs:
                chunks.append(self._join_paragraphs(current_paragraphs))

            overlap_paragraphs = self._get_overlap_paragraphs(current_paragraphs)

            current_paragraphs = [
                *overlap_paragraphs,
                paragraph,
            ]

            current_text = self._join_paragraphs(current_paragraphs)

            if len(current_text) > self.chunk_size:
                current_paragraphs = [paragraph]

        if current_paragraphs:
            chunks.append(self._join_paragraphs(current_paragraphs))

        return chunks

    def _get_overlap_paragraphs(
        self,
        paragraphs: list[str],
    ) -> list[str]:
        """Return trailing paragraphs that fit inside the overlap target."""

        if self.chunk_overlap == 0:
            return []

        overlap_paragraphs: list[str] = []

        for paragraph in reversed(paragraphs):
            candidate = [
                paragraph,
                *overlap_paragraphs,
            ]

            candidate_text = self._join_paragraphs(candidate)

            if len(candidate_text) > self.chunk_overlap:
                break

            overlap_paragraphs.insert(
                0,
                paragraph,
            )

        return overlap_paragraphs

    def _split_by_characters(
        self,
        text: str,
    ) -> list[str]:
        """Fallback to character-based overlapping chunks."""

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start += self.chunk_size - self.chunk_overlap

        return chunks

    @staticmethod
    def _join_paragraphs(
        paragraphs: list[str],
    ) -> str:
        """Join paragraphs using a blank line."""

        return "\n\n".join(paragraphs)
