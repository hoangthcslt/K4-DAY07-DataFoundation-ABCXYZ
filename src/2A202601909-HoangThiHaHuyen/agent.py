from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        if metadata_filter:
            results = self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        else:
            results = self.store.search(question, top_k=top_k)
        results = self._merge_adjacent_chunks(results)
        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = (
                metadata.get("source_url")
                or metadata.get("source")
                or result.get("id", "không rõ")
            )
            context_parts.append(
                f"[{index}] Nguồn: {source}\n{result['content']}"
            )
        context = "\n\n".join(context_parts)
        if not context:
            context = "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức."

        prompt = (
            "Hãy trả lời câu hỏi chỉ dựa trên ngữ cảnh được cung cấp. "
            "Nếu ngữ cảnh không đủ, hãy nói rõ rằng bạn chưa có đủ thông tin.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)

    @staticmethod
    def _merge_adjacent_chunks(results: list[dict]) -> list[dict]:
        """Reconstruct overlapping chunks from the same source document."""
        grouped: list[list[dict]] = []
        group_index: dict[str, int] = {}
        for result in results:
            metadata = result.get("metadata", {})
            doc_id = metadata.get("doc_id")
            chunk_index = metadata.get("chunk_index")
            if doc_id is None or not isinstance(chunk_index, int):
                grouped.append([result])
                continue
            if doc_id not in group_index:
                group_index[doc_id] = len(grouped)
                grouped.append([])
            grouped[group_index[doc_id]].append(result)

        merged_results: list[dict] = []
        for group in grouped:
            if len(group) == 1 or "chunk_index" not in group[0].get("metadata", {}):
                merged_results.extend(group)
                continue

            ordered = sorted(group, key=lambda item: item["metadata"]["chunk_index"])
            content = ordered[0]["content"]
            previous_index = ordered[0]["metadata"]["chunk_index"]
            for item in ordered[1:]:
                current_index = item["metadata"]["chunk_index"]
                separator = "\n" if current_index != previous_index + 1 else ""
                content = KnowledgeBaseAgent._join_with_overlap(
                    content,
                    item["content"],
                    separator=separator,
                )
                previous_index = current_index

            merged = dict(group[0])
            merged["content"] = content
            merged["score"] = max(item.get("score", 0.0) for item in group)
            merged_results.append(merged)
        return merged_results

    @staticmethod
    def _join_with_overlap(left: str, right: str, separator: str = "") -> str:
        max_overlap = min(len(left), len(right))
        for size in range(max_overlap, 0, -1):
            if left[-size:] == right[:size]:
                return left + right[size:]
        return left + separator + right
