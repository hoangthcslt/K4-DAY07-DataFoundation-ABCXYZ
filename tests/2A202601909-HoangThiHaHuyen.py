"""Personal benchmark for Hoang Thi Ha Huyen (2A202601909)."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "k4_ecommerce"
PACKAGE_NAME = "src.2A202601909-HoangThiHaHuyen"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

solution = import_module(PACKAGE_NAME)
Document = solution.Document
EmbeddingStore = solution.EmbeddingStore
FixedSizeChunker = solution.FixedSizeChunker
KnowledgeBaseAgent = solution.KnowledgeBaseAgent
LexicalHashEmbedder = solution.LexicalHashEmbedder

CHUNK_SIZE = 500
OVERLAP = 50
BENCHMARK_QUERIES = (
    ("Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store?", None),
    ("Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không?", None),
    ("Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không?", None),
    (
        "Tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không?",
        {"customer_role": "buyer"},
    ),
    (
        "Tôi nhận được email yêu cầu cung cấp số thẻ tín dụng từ Apple, tôi có nên làm theo không?",
        {"customer_role": "both"},
    ),
)

STOP_WORDS = {
    "ai", "apple", "bao", "bạn", "bị", "các", "cho", "có", "của", "được",
    "gì", "khi", "không", "là", "làm", "mua", "như", "nhận", "nào", "nên",
    "sản", "theo", "thể", "tôi", "từ", "và", "với",
}


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing is None:
        return {}, text

    metadata = {}
    for line in lines[1:closing]:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    body = "\n".join(lines[closing + 1 :]).lstrip()
    return metadata, body


def build_store() -> EmbeddingStore:
    chunker = FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=OVERLAP)
    chunks = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        doc_id = str(metadata.get("doc_id") or path.stem)
        metadata.setdefault("doc_id", doc_id)
        metadata.setdefault("source", str(path))
        for index, content in enumerate(chunker.chunk(body)):
            chunk_metadata = dict(metadata)
            chunk_metadata["chunk_index"] = index
            chunks.append(
                Document(
                    id=f"{doc_id}::chunk_{index}",
                    content=content,
                    metadata=chunk_metadata,
                )
            )

    store = EmbeddingStore(
        collection_name="2A202601909_benchmark",
        embedding_fn=LexicalHashEmbedder(),
    )
    store.add_documents(chunks)
    return store


def content_terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"\w+", text.casefold(), flags=re.UNICODE)
        if len(token) > 1 and token not in STOP_WORDS
    }


def extractive_llm(prompt: str) -> str:
    context_marker = "Ngữ cảnh:\n"
    question_marker = "\n\nCâu hỏi:"
    if context_marker not in prompt or question_marker not in prompt:
        return "Chưa có đủ thông tin trong ngữ cảnh để trả lời."

    context = prompt.split(context_marker, 1)[1].split(question_marker, 1)[0]
    question = prompt.split(question_marker, 1)[1].split("\n", 1)[0]
    question_terms = content_terms(question)
    segments = [
        sentence.strip(" -")
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", context)
    ]
    candidates = []
    for order, sentence in enumerate(segments):
        if not sentence or "Nguồn:" in sentence:
            continue
        score = len(question_terms & content_terms(sentence))
        if score / max(1, len(question_terms)) >= 0.35:
            candidates.append((score, -order, sentence))
    if not candidates:
        return "Chưa có đủ thông tin trong ngữ cảnh để trả lời."

    selected = sorted(candidates, reverse=True)[:2]
    selected_sentences = [sentence for _, _, sentence in selected]
    if len(selected_sentences) == 1:
        best_order = -selected[0][1]
        if best_order + 1 < len(segments):
            adjacent = segments[best_order + 1]
            if (
                adjacent
                and "Nguồn:" not in adjacent
                and question_terms & content_terms(adjacent)
            ):
                selected_sentences.append(adjacent)
    return " ".join(selected_sentences)


def run_benchmark() -> int:
    store = build_store()
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
    print("=== BENCHMARK CÁ NHÂN 2A202601909 ===")
    print("Backend nhúng: lexical hash embeddings (offline)")
    print(f"Chiến lược: FixedSizeChunker(chunk_size={CHUNK_SIZE}, overlap={OVERLAP})")
    print(f"Số chunk: {store.get_collection_size()}")

    for index, (query, metadata_filter) in enumerate(BENCHMARK_QUERIES, start=1):
        results = store.search_with_filter(
            query,
            top_k=3,
            metadata_filter=metadata_filter,
        )
        print(f"\nQ{index}: {query}")
        if metadata_filter:
            print(f"Filter: {metadata_filter}")
        for rank, result in enumerate(results, start=1):
            doc_id = result["metadata"].get("doc_id", "unknown")
            print(f"  {rank}. score={result['score']:.4f} doc={doc_id}")
        print(f"Agent: {agent.answer(query, top_k=3, metadata_filter=metadata_filter)}")
    return 0


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(run_benchmark())
