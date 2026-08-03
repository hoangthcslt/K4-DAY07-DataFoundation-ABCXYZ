# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Thị Hà Huyền

**Mã sinh viên:** 2A202601909

**Lớp/Nhóm:** K4 - E403 - ABCXYZ

**Ngày:** 03/08/2026

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

Độ tương tự cosine cao nghĩa là hai vector embedding hướng gần giống nhau, vì vậy hai văn bản thường có ý nghĩa hoặc ngữ cảnh gần nhau. Điểm gần `1` biểu thị rất tương đồng, gần `0` biểu thị ít liên quan và gần `-1` biểu thị hướng đối lập trong không gian vector.

**Ví dụ có độ tương tự cao:**

- Câu A: “Khách hàng có thể yêu cầu đổi trả sản phẩm bị lỗi.”
- Câu B: “Người mua được gửi yêu cầu trả hàng khi sản phẩm có lỗi.”
- Hai câu dùng từ khác nhau nhưng cùng nói về quyền đổi trả khi hàng lỗi.

**Ví dụ có độ tương tự thấp:**

- Câu A: “Sản phẩm bị cấm không được phép đăng bán.”
- Câu B: “Thời tiết Bangkok hôm nay có mưa.”
- Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau.

Cosine similarity thường phù hợp hơn Euclidean distance cho text embedding vì nó tập trung vào hướng của vector — tức mẫu ý nghĩa — thay vì bị ảnh hưởng nhiều bởi độ lớn vector. Điều này đặc biệt hữu ích khi độ dài văn bản khác nhau.

### Bài toán tính toán Chunking

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:

```text
ceil((10.000 - 50) / (500 - 50))
= ceil(9.950 / 450)
= ceil(22,111...)
= 23 chunks
```

Khi tăng `overlap` lên 100:

```text
ceil((10.000 - 100) / (500 - 100))
= ceil(9.900 / 400)
= ceil(24,75)
= 25 chunks
```

Số chunk tăng từ 23 lên 25 vì bước trượt giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ ngữ cảnh nằm sát ranh giới chunk, nhưng làm tăng dung lượng lưu trữ và chi phí embedding/truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`:** Tôi dùng regex `(?<=[.!?])\s+` để nhận diện khoảng trắng sau dấu kết thúc câu, đồng thời giữ lại dấu câu trong nội dung. Văn bản rỗng hoặc chỉ có khoảng trắng trả về danh sách rỗng; các câu được `strip`, loại phần rỗng rồi gom theo `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`:** Thuật toán thử lần lượt các separator theo độ ưu tiên `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là cắt cứng. Các phần nhỏ được ghép cho tới giới hạn `chunk_size`; phần còn quá dài được đệ quy bằng separator tiếp theo. Base case là nội dung đã không vượt giới hạn; nếu hết separator thì cắt theo đúng số ký tự để tránh vòng lặp vô hạn.

**`compute_similarity` và comparator:** Cosine similarity được tính bằng tích vô hướng chia cho tích độ lớn hai vector và trả `0.0` khi một vector có độ lớn bằng 0. Comparator chạy đủ ba chiến lược, sau đó trả số chunk, độ dài trung bình và danh sách chunk của từng chiến lược.

### Lớp EmbeddingStore

**`add_documents` + `search`:** Mỗi `Document` được chuẩn hóa thành record gồm ID nội bộ duy nhất, content, bản sao metadata có `doc_id`, và embedding. Khi tìm kiếm, query chỉ được embed một lần; store tính dot product với các record, sắp xếp điểm giảm dần và lấy tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`:** Metadata được lọc trước khi tính similarity để vừa đúng ngữ nghĩa của bộ lọc vừa giảm tập ứng viên. Khi xóa, store tìm toàn bộ record có `metadata["doc_id"]` tương ứng và xóa tất cả chunk; hàm trả `False` nếu không tìm thấy. Implementation hỗ trợ ChromaDB khi có sẵn và tự dùng in-memory store khi môi trường không cài ChromaDB.

### Tác tử KnowledgeBaseAgent

**`answer`:** Agent lấy top-k chunk bằng `search` hoặc `search_with_filter` nếu có bộ lọc metadata. Prompt đánh số từng chunk, kèm nguồn, câu hỏi và chỉ dẫn chỉ trả lời dựa trên ngữ cảnh; khi không có kết quả, prompt nói rõ thiếu dữ liệu để giảm nguy cơ bịa thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Lệnh kiểm thử chạy bằng Python 3.11.9:

```text
$ pytest tests -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 42 items
...
FAILED tests/test_solution.py::TestProjectStructure::test_src_package_exists
========================= 1 failed, 41 passed in 0.12s =========================
```

**Số lượng bài test vượt qua:** 41 / 42 khi đặt `LAB_SOLUTION_PACKAGE=src.2A202601909-HoangThiHaHuyen`. Toàn bộ test API/chức năng cá nhân đều pass; test duy nhất thất bại kiểm tra `src/__init__.py`, trong khi commit nhóm `8753ae1` đã chuyển sang cấu trúc package theo MSSV và không còn file `src/__init__.py` ở root.

Ngoài pytest, package cá nhân và benchmark đã vượt qua `python -m compileall -q src/2A202601909-HoangThiHaHuyen tests/2A202601909-HoangThiHaHuyen.py` và `git diff --check`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm dưới đây được tạo bằng `LexicalHashEmbedder` rồi đưa vào `compute_similarity()`. Backend này chuẩn hóa vector đếm token đã băm, nên phản ánh tốt mức độ trùng từ khóa và chạy hoàn toàn offline; nó không thay thế được mô hình semantic đa ngữ khi hai câu dùng từ đồng nghĩa khác nhau.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---:|---|---|---|---:|---|
| 1 | Khách hàng có thể yêu cầu đổi trả sản phẩm bị lỗi. | Người mua được gửi yêu cầu trả hàng khi sản phẩm có lỗi. | Cao | 0,7500 | Có |
| 2 | Người bán phải mô tả chính xác sản phẩm. | Thông tin sản phẩm đăng bán cần đầy đủ và chính xác. | Cao | 0,4472 | Có |
| 3 | Sản phẩm bị cấm không được phép đăng bán. | Thời tiết Bangkok hôm nay có mưa. | Thấp | 0,0000 | Có |
| 4 | Yêu cầu đổi trả cần kèm bằng chứng phù hợp. | Học máy sử dụng thuật toán để học từ dữ liệu. | Thấp | 0,0000 | Có |
| 5 | Người bán phải phản hồi yêu cầu đổi trả. | Người mua gửi yêu cầu trả hàng theo quy trình của sàn. | Cao | 0,4444 | Có |

Kết quả phân tách rõ các cặp có từ khóa chung và các cặp không liên quan. Hạn chế quan trọng là lexical hashing không hiểu sâu từ đồng nghĩa; khi môi trường tải model ổn định, nên chạy đối chiếu thêm bằng `paraphrase-multilingual-MiniLM-L12-v2`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Cấu hình thử nghiệm

- Corpus: 5 tài liệu Apple VN trong `data/k4_ecommerce/`, tạo thành 9 chunks.
- Chunker: `FixedSizeChunker(chunk_size=500, overlap=50)`, chạy độc lập trong file benchmark cá nhân.
- Embedder: `LexicalHashEmbedder` 4096 chiều, chạy offline và chuẩn hóa cosine.
- Query 4 dùng `customer_role=buyer`; query 5 dùng `customer_role=both` để kiểm tra metadata pre-filtering.
- Agent: ghép lại các chunk liên tiếp cùng `doc_id` bằng phần overlap trước khi tạo prompt, sau đó chọn câu có độ phủ từ khóa đủ cao và giữ câu hướng dẫn liền kề khi gold answer trải qua hai câu.

| # | Câu hỏi (Query) | Top-1 chunk truy xuất được (tóm tắt) | Score | Relevant? | Câu trả lời của Agent (tóm tắt) |
|---:|---|---|---:|---|---|
| 1 | Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store? | `k4-apple-sales-refund`: điều kiện hoàn trả trong 14 ngày. | 0,5524 | Có — top-1 | Được hoàn trả sản phẩm đủ điều kiện trong vòng 14 ngày kể từ ngày nhận. |
| 2 | Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không? | `k4-apple-warranty`: ngoại lệ linh kiện tiêu hao. | 0,4795 | Có — top-1 | Không; pin và lớp bảo vệ hao mòn theo thời gian không thuộc phạm vi bảo hành. |
| 3 | Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không? | `k4-apple-media-terms`: điều kiện tuổi và Family Sharing. | 0,3593 | Có — top-1 | Không, trừ khi được cha mẹ/người giám hộ chấp thuận qua Chia sẻ trong gia đình. |
| 4 | Tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không? | `k4-apple-media-terms`: giao dịch nội dung số là cuối cùng. | 0,2593 | Có — top-1 | Không thể hoàn tiền, trừ ngoại lệ của chính sách dịch vụ hoặc pháp luật địa phương. |
| 5 | Tôi nhận được email yêu cầu cung cấp số thẻ tín dụng từ Apple, tôi có nên làm theo không? | `k4-apple-phishing`: cảnh báo và địa chỉ báo cáo. | 0,4683 | Có — top-1 | Không; chuyển tiếp email đáng ngờ đến `reportphishing@apple.com`. |

**Số câu hỏi có gold chunk trong top-3:** 5 / 5. **Số gold chunk ở top-1:** 5 / 5.

Failure case đối chứng là cùng `FixedSizeChunker(500, overlap=50)` nhưng dùng `MockEmbedder`: agent chỉ trả lời đúng 3/5 câu, trong khi lexical hashing đưa cả 5 gold chunks lên top-1. Fixed-size còn có thể cắt giữa từ/câu; phần overlap 50 ký tự và bước ghép chunk liên tiếp trong agent giúp tái tạo đầy đủ điều khoản ở câu 2 và 4. Kết quả lexical vẫn cần được đối chiếu bằng model đa ngữ cho các truy vấn dùng từ đồng nghĩa.

**Điều học được từ việc đối chiếu kết quả:** Metadata filter ở câu 4 và 5 loại đúng các tài liệu sai vai trò trước khi xếp hạng. Tuy nhiên, filter không thay thế embedding: với mock, kết quả vẫn sai trong tập ứng viên đã lọc; với lexical backend, tài liệu đúng mới lên top-1.

Kết quả có thể tái lập bằng `python tests/2A202601909-HoangThiHaHuyen.py`; script chỉ import package MSSV tương ứng và không phụ thuộc code của thành viên khác.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 29 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |

Corpus đạt yêu cầu tối thiểu 5 tài liệu, đủ metadata bắt buộc, benchmark dùng đúng 5 query chung và kết quả được tái lập bằng CLI. Lexical backend là phương án offline có giới hạn đã được nêu rõ; model đa ngữ vẫn là bước đối chiếu nâng cao khi dependency tải được.
