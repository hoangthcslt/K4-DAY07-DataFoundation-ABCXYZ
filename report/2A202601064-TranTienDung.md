# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Tiến Dũng
**MSSV:** 2A202601064
**Nhóm:** ABCXYZ
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng hướng trong không gian nhiều chiều — tức hai đoạn văn bản mang cùng một ý nghĩa/ngữ cảnh, cho dù từ ngữ dùng để diễn đạt có khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sản phẩm được bảo hành 1 năm kể từ ngày mua."
- Câu B: "Apple hỗ trợ bảo hành 12 tháng tính từ thời điểm khách hàng nhận máy."
- Tại sao tương đồng: cả hai câu cùng nói về một sự kiện (thời hạn bảo hành 1 năm/12 tháng), chỉ khác cách diễn đạt và đơn vị thời gian.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Táo là loại trái cây giàu vitamin."
- Câu B: "iPhone là sản phẩm điện thoại của Apple."
- Tại sao khác: tuy có liên hệ về mặt từ vựng ("táo"/"Apple") nhưng một câu nói về thực phẩm, câu còn lại nói về thiết bị công nghệ — không chia sẻ ngữ cảnh ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo **hướng** của vector (ngữ nghĩa), bỏ qua **độ lớn** (magnitude) — vốn phụ thuộc vào độ dài văn bản. Euclidean distance lại nhạy với độ lớn này, nên hai đoạn văn cùng nghĩa nhưng độ dài khác nhau (một câu ngắn, một đoạn dài diễn giải cùng ý) có thể bị đánh giá sai là "xa nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: `số_chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11)`
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `số_chunk = làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks` — số chunk **tăng** vì bước trượt (`step = chunk_size - overlap`) nhỏ lại. Overlap lớn hơn giúp các câu/ý nằm vắt ngang ranh giới cắt vẫn xuất hiện trọn vẹn ở chunk kế tiếp, giảm nguy cơ mất ngữ cảnh — đánh đổi là nhiều chunk hơn, tốn thêm dung lượng lưu trữ/tính embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(\. |! |\? |\.\n)` với capture group để tách câu mà vẫn **giữ lại** dấu phân cách trong danh sách kết quả của `re.split`. Duyệt qua từng phần tử, cộng dồn vào buffer `current`; hễ gặp đúng dấu phân cách thì chốt câu, reset buffer. Sau đó gom `max_sentences_per_chunk` câu liên tiếp thành 1 chunk. Edge case: văn bản rỗng trả về `[]` ngay; câu cuối không có dấu kết thúc vẫn được giữ lại nhờ kiểm tra buffer còn dư sau vòng lặp.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Đệ quy thử lần lượt separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → `" "` → `""`). Base case: `len(current_text) <= chunk_size` thì trả về nguyên văn bản. Khi tách theo 1 separator, các mảnh nhỏ được **gộp dần** vào một buffer cho tới sát `chunk_size` để tránh sinh ra quá nhiều chunk vụn; mảnh nào một mình đã vượt `chunk_size` thì gọi đệ quy tiếp với separator còn lại. Khi hết separator hoặc separator là chuỗi rỗng, cắt cứng theo `chunk_size` ký tự làm phương án cuối (tránh lỗi `"abc".split("")`).

**`MarkdownHeaderChunker` (chiến lược tùy chỉnh cho chủ đề K4)** — hướng tiếp cận:
> Vì bộ tài liệu K4 là các trang chính sách `.md` có cấu trúc theo tiêu đề rõ ràng (mỗi file = 1 chính sách), mình viết thêm class này: tìm mọi dòng tiêu đề Markdown (`#`…`######`) bằng regex, cắt văn bản thành các "section" theo ranh giới tiêu đề, rồi cắt cứng thêm nếu 1 section vẫn dài hơn `chunk_size`. Ý tưởng là giữ mỗi chunk gắn liền với đúng 1 tiêu đề/điều khoản thay vì cắt theo ký tự cố định, để không bị đứt giữa 1 quy định — đáp ứng đúng yêu cầu K4_VARIANT.md về việc thử chunking theo tiêu đề/mục.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `_make_record` chuẩn hóa mỗi `Document` thành dict `{id, content, metadata, embedding}`, tự gắn `metadata["doc_id"] = doc.id` nếu tài liệu chưa có sẵn field này (đảm bảo `delete_document` luôn hoạt động nhất quán). `add_documents` gọi `_make_record` rồi `append` vào list `self._store` (in-memory) — có nhánh dùng `chromadb.collection.add(...)` nếu thư viện này có sẵn. `search` embed câu query, tính dot product với từng embedding đã lưu (hàm `_search_records`), sort giảm dần theo score, cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc trước, tìm kiếm sau**: `search_with_filter` giữ lại các record có `metadata[key] == value` khớp toàn bộ `metadata_filter`, rồi mới gọi `_search_records` trên tập đã lọc — nếu không có filter thì dùng nguyên store, hành vi giống hệt `search`. `delete_document` dùng list comprehension giữ lại các record có `metadata["doc_id"] != doc_id`, so sánh độ dài store trước/sau để trả về `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer(question, top_k, metadata_filter=None)`: nếu có `metadata_filter` thì gọi `store.search_with_filter`, không thì `store.search`. Ghép nội dung các chunk truy xuất được thành ngữ cảnh có đánh số `[1] ... [2] ...`, chèn vào prompt gồm 3 phần: hướng dẫn "chỉ trả lời dựa trên context, không có thì nói không biết" (hạn chế hallucination), Context, và Question — cuối cùng gọi `llm_fn(prompt)`. Tham số `metadata_filter` mình chủ động thêm vào (không có trong template `answer(question, top_k)` gốc) vì script benchmark cá nhân (`tests/benchmark/bench.py`) cần lọc theo `customer_role` cho 2/5 câu hỏi.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- .../envs/lab7/bin/python3.11
rootdir: /home/dungtt/Code/K4-DAY07-DataFoundation-ABCXYZ
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy `compute_similarity()` bằng `_mock_embed` (mặc định của môi trường lab, chưa cài local embedder).

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Chính sách cho phép trả hàng trong vòng 14 ngày kể từ ngày nhận sản phẩm." | "Bạn có thể hoàn trả sản phẩm trong 14 ngày sau khi nhận hàng." | cao | -0.140 | Sai |
| 2 | "Apple bảo hành phần cứng trong thời hạn một năm kể từ ngày mua." | "Thời hạn bảo hành tiêu chuẩn của Apple là 12 tháng." | cao | -0.268 | Sai |
| 3 | "Không nên cung cấp mật khẩu Apple ID qua email không rõ nguồn gốc." | "Hãy bật xác thực hai yếu tố để bảo vệ tài khoản Apple ID của bạn." | cao | 0.107 | Sai |
| 4 | "Táo là loại trái cây giàu vitamin C và chất xơ." | "iPhone là sản phẩm chủ lực của Apple trong mảng điện thoại." | thấp | 0.228 | Đúng |
| 5 | "Chính sách quyền riêng tư quy định cách Apple xử lý dữ liệu cá nhân." | "Hôm nay thời tiết rất đẹp, thích hợp để đi dạo." | thấp | -0.010 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là 3 cặp câu **đồng nghĩa rõ ràng** (cặp 1, 2, 3 — cùng nói về thời hạn đổi trả, thời hạn bảo hành, bảo mật tài khoản) lại cho điểm thấp hoặc âm, trong khi 2 cặp **không liên quan về nội dung** lại được dự đoán đúng là thấp một cách "tình cờ". Điều này cho thấy `_mock_embed` chỉ băm ký tự (hash) chứ không mã hóa ngữ nghĩa gì cả — điểm số gần như ngẫu nhiên. Muốn dự đoán có ý nghĩa thật, bắt buộc phải dùng embedder đã học ngữ nghĩa (local/OpenAI), đúng như README đã cảnh báo.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy 5 câu hỏi đánh giá chung của nhóm (`tests/benchmark/bench.py`) trên chiến lược cá nhân **`MarkdownHeaderChunker(chunk_size=400)`** + `_mock_embed` (chưa có local embedder trong môi trường).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store? | k4-apple-media-terms: "...giao dịch mua nội dung số trên App Store là giao dịch cuối cùng..." | 0.203 | Không (đúng đáp án nằm ở k4-apple-sales-refund nhưng không lọt top-3) | Dựa vào chunk sai, không nêu được "14 ngày" |
| 2 | Các lớp bảo vệ/pin bị chai theo thời gian có được Apple bảo hành không? | k4-apple-media-terms: "...giao dịch mua nội dung số..." | 0.261 | Có, nhưng ở rank 2 (k4-apple-warranty, score 0.168), không phải top-1 | Trả lời lạc đề vì context top-1 sai |
| 3 | Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không? | k4-apple-warranty: "Bảo Hành Có Giới Hạn 1 Năm..." | 0.104 | Có, nhưng ở rank 3 (k4-apple-media-terms, score 0.082), không phải top-1 | Trả lời sai chủ đề (bảo hành thay vì điều khoản tài khoản) |
| 4 | Tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không? (filter: `customer_role=buyer`) | k4-apple-media-terms: "...Tất cả giao dịch mua nội dung số trên App Store là giao dịch cuối cùng và không thể hoàn tiền..." | 0.183 | **Có, đúng top-1** | Trả lời đúng hướng: nêu được nguyên tắc "giao dịch cuối cùng, không hoàn tiền trừ ngoại lệ" |
| 5 | Tôi nhận được email yêu cầu số thẻ tín dụng từ Apple, có nên làm theo không? (filter: `customer_role=both`) | k4-apple-phishing: "...Kích hoạt xác thực hai yếu tố (2FA)..." | 0.204 | **Có, đúng top-1** | Trả lời đúng hướng: cảnh báo lừa đảo, gợi ý bật 2FA |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 (chỉ câu 1 hoàn toàn miss — doc đúng `k4-apple-sales-refund` không xuất hiện trong top-3). Tuy nhiên chỉ **2/5** có chunk liên quan đúng ở **top-1** (câu 4, 5 — cả hai đều có `metadata_filter`).

**Nhận xét:** điểm số ở trên đến từ `_mock_embed` nên không phản ánh chất lượng ngữ nghĩa thật — 2 câu có kết quả tốt nhất (4, 5) trùng với 2 câu có `metadata_filter`, gợi ý rằng **lọc metadata đang gánh phần lớn việc thu hẹp đúng tài liệu**, còn bản thân điểm similarity gần như ngẫu nhiên. Cần chạy lại với `EMBEDDING_PROVIDER=local` để đánh giá công bằng giữa các chiến lược chunking.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Khi so sánh code với 2 bạn cùng nhóm (Dương Văn Kiên, Lương Hoàng Minh) trên remote: bạn Minh tính `norm` trong `compute_similarity` bằng `sqrt(_dot(v, v))` thay vì viết lại tổng bình phương — tái dùng hàm có sẵn, gọn hơn. Bạn Minh cũng cho `KnowledgeBaseAgent.answer` trả lời thân thiện ("tôi không biết") khi store rỗng hoặc không có kết quả liên quan, thay vì để lỗi/prompt trống — một cải tiến nhỏ nhưng thực tế đáng học theo. Ngoài ra, mình là người duy nhất trong 3 người thử chunking theo tiêu đề Markdown (`MarkdownHeaderChunker`) — đúng yêu cầu K4_VARIANT.md về việc ít nhất 1 thành viên thử chia theo điều khoản/tiêu đề.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
