# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đình Hoàng  
**Mã sinh viên:** 2A202601436  
**Nhóm:** Nhóm 1 (Lớp K4)  
**Ngày:** 03/08/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1.0) thể hiện hai góc biểu diễn vector của hai đoạn văn bản trong không gian vector trùng hoặc gần trùng nhau. Điều này đồng nghĩa với việc hai văn bản có sự tương đồng rất cao về mặt ngữ nghĩa hoặc chủ đề, không phụ thuộc vào độ dài ngắn của văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách đổi trả hàng trong vòng 7 ngày kể từ khi nhận sản phẩm."
- Câu B: "Thời hạn người mua có thể hoàn trả hàng là một tuần sau khi nhận."
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một thông tin về thời gian và quyền lợi hoàn trả hàng của khách hàng dù dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Quy trình vận chuyển hàng hóa qua đường hàng không."
- Câu B: "Món ăn này sử dụng nguyên liệu tươi ngon và gia vị truyền thống."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập (logistics vận chuyển vs ẩm thực), vector của chúng hướng theo hai phía khác nhau trong không gian biểu diễn.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo độ dài tuyệt đối giữa hai điểm vector nên dễ bị ảnh hưởng bởi độ dài của văn bản (văn bản dài hơn có độ dài vector lớn hơn). Trong khi đó, độ tương tự cosine chỉ đo góc giữa hai vector (hướng của vector chính là ngữ nghĩa), giúp so sánh chính xác độ tương đồng nội dung mà không bị sai lệch do văn bản ngắn hay dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Công thức: `Số chunks = ceil((Độ_dài - Overlap) / (Chunk_size - Overlap))`  
> Thế số: `(10000 - 50) / (500 - 50) = 9950 / 450 = 22.111...`  
> Làm tròn lên: `ceil(22.111) = 23`  
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế meo? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Phép tính mới:* `(10000 - 100) / (500 - 100) = 9900 / 400 = 24.75` -> `ceil(24.75) = 25 chunks`.  
> *Thay đổi:* Số lượng chunk tăng từ 23 lên **25 chunks**.  
> *Lý do tăng overlap:* Giúp giữ lại bối cảnh (context) liền mạch ở vị trí cắt giữa các chunk kề nhau, tránh việc các câu hoặc ý quan trọng bị ngắt đôi ở ranh giới chunk khiến mô hình mất thông tin khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng biểu thức chính quy (regex) `re.split(r'(?<=[.!?])(?:\s|\n)', text)` với kỹ thuật lookbehind để tách câu tại các ranh giới kết thúc câu như `. `, `! `, `? ` hoặc `.\n`. Xử lý ngoại lệ bằng cách loại bỏ khoảng trắng thừa (`strip()`), lọc bỏ chuỗi rỗng và gom nhóm các câu thành từng chunk theo tham số `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Sử dụng giải thuật đệ quy duyệt qua danh sách các dấu phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base case là khi đoạn văn bản có độ dài `<= chunk_size`. Nếu vượt quá, hàm tiến hành tách theo separator hiện tại, ghép các đoạn nhỏ lại cho tới khi chạm ngưỡng `chunk_size`; nếu một phần tách ra vẫn quá lớn, hàm đệ quy gọi `_split` với danh sách separator còn lại.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ văn bản dưới dạng danh sách dict (`self._store`) gồm `id`, `content`, `embedding` (tạo ra từ hàm nhúng `_embedding_fn`) và `metadata`. Khi thực hiện `search`, hàm tính tích vô hướng (dot product) giữa vector truy vấn và từng vector lưu trong store, sắp xếp kết quả theo điểm score giảm dần và lấy ra `top_k` kết quả cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` áp dụng chiến lược pre-filtering: lọc danh sách bản ghi có `metadata` thỏa mãn tất cả cặp key-value trong `metadata_filter` trước, sau đó mới gọi `_search_records` để tìm kiếm tương đồng trên tập đã lọc. `delete_document` xóa tất cả chunk có `metadata['doc_id'] == doc_id` bằng list comprehension và trả về `True` nếu có bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đầu tiên gọi `self.store.search(question, top_k)` để truy xuất top-k chunk liên quan nhất. Sau đó nối nội dung các chunk này thành đoạn `context` và đóng gói vào cấu trúc prompt chuẩn RAG dạng: `"Based on the following context, answer the question. Context: ... Question: ... Answer:"`. Cuối cùng truyền prompt này vào hàm `self.llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Users\User\Desktop\Lab7_038\DAY07-2A202601436-NguyenDinhHoang
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng trong 7 ngày | Thời hạn hoàn trả sản phẩm là một tuần | cao | 0.1145 | Không |
| 2 | Khách hàng có thể thanh toán qua thẻ VISA | Phương thức thanh toán bằng thẻ quốc tế | cao | -0.0101 | Không |
| 3 | Quy định giao hàng hỏa tốc trong 24h | Hướng dẫn đăng ký tài khoản người bán | thấp | 0.3012 | Không |
| 4 | Bảo mật thông tin cá nhân của người dùng | Chính sách bảo vệ dữ liệu khách hàng | cao | 0.0220 | Không |
| 5 | Phương thức vận chuyển đường hàng không | Món ăn này rất ngon và hấp dẫn | thấp | 0.1412 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp câu 3 có chủ đề hoàn toàn khác nhau lại nhận điểm số cao nhất (0.3012), trong khi cặp 2 có cùng ngữ nghĩa thanh toán lại nhận điểm âm (-0.0101). Điều này xảy ra do mô hình `MockEmbedder` tạo ngẫu nhiên dựa trên MD5 hash của chuỗi ký tự mà không qua huấn luyện ngữ nghĩa. Điều này khẳng định rằng để hệ thống RAG thực tế hoạt động hiệu quả, bắt buộc phải dùng các mô hình embedding ngữ nghĩa thực sự (như `sentence-transformers` hoặc OpenAI).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` với bộ dữ liệu `data/k4_ecommerce`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn và điều kiện đổi trả hàng là gì? | Quy định phản hồi đổi trả và trách nhiệm người bán khi hàng bị lỗi... | 0.0952 | Có | Trích xuất điều khoản đổi trả từ ngữ cảnh... |
| 2 | Các phương thức thanh toán nào được chấp nhận? | Template chính sách thanh toán qua thẻ, ví điện tử và COD... | 0.0881 | Có | Liệt kê các phương thức thanh toán trong tài liệu... |
| 3 | Điều kiện để đăng ký làm người bán (seller) là gì? | Điều kiện đăng ký tài khoản seller và xác minh thông tin... | 0.1340 | Có | Cung cấp điều kiện và hồ sơ người bán... |
| 4 | Chính sách bảo mật thông tin cá nhân quy định như thế nào? | Cam kết bảo vệ dữ liệu người dùng và không chia sẻ bên thứ 3... | 0.0613 | Có | Tóm tắt các điều khoản bảo mật dữ liệu... |
| 5 | Thời gian giao hàng tiêu chuẩn và giao hàng nhanh mất bao lâu? | Thời gian vận chuyển tiêu chuẩn (2-3 ngày) và hỏa tốc (24h)... | 0.0071 | Có | Trả lời khung thời gian giao hàng... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc tổ chức cấu trúc siêu dữ liệu (metadata schema) chuẩn xác như `customer_role` (buyer/seller) và áp dụng pre-filtering trước khi tính toán tương đồng giúp loại bỏ nhiễu cực kỳ hiệu quả, tăng tốc độ truy xuất và độ chính xác của câu trả lời từ tác tử RAG.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
