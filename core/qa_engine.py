"""
qa_engine.py — Question & Answer logic over extracted content.
Currently a placeholder. Wire in an LLM or RAG pipeline here.
"""

from __future__ import annotations


class QAEngine:
    """Answers questions about the loaded document content."""

    def __init__(self) -> None:
        self._context: str = ""

    def set_context(self, text: str) -> None:
        """Provide the extracted document text as context for Q&A."""
        self._context = text

    def ask(self, question: str) -> str:
        """
        Answer a question based on the loaded context.

        TODO: Integrate an LLM (e.g. OpenAI chat completion, local LLaMA,
              or a retrieval-augmented generation pipeline).

        Args:
            question: The user's natural language question.

        Returns:
            The answer as a string.
        """
        # ── Placeholder ───────────────────────────────────────────────────────
        if not self._context.strip():
            return "No content loaded. Please upload a document first."
        if not question.strip():
            return "Please enter a question."
        return (
            f"[Q&A placeholder]\n\n"
            f"Question: {question}\n\n"
            f"Context preview: {self._context[:200]}...\n\n"
            f"Wire in an LLM to get real answers."
        )
