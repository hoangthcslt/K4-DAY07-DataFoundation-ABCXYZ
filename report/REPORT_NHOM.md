# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** ABCXYZ (K4 - E403)  
**Thành viên:**  
- Nguyễn Đình Hoàng - 2A202601436  
- Lương Hoàng Minh - 2A202601490  
- Trần Tiến Dũng - 2A202601064  
- Dương Văn Kiên - 2A202601724  
- Hoàng Thị Hà Huyền - 2A202601909  

**Ngày:** 03/08/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**  
> Nhóm tập trung thu thập bộ quy định và chính sách chính thức từ Apple Store Việt Nam bao gồm: Chính sách bán hàng & hoàn trả, bảo hành sản phẩm phần cứng, quyền riêng tư dữ liệu cá nhân, điều khoản dịch vụ nội dung số App Store, và hướng dẫn phòng chống email lừa đảo (phishing).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính Sách Bán Hàng Và Trả Hàng | [Apple Store VN](https://www.apple.com/vn/shop/browse/open/salespolicies) | 2026-08-03 / not-stated | ~600 | customer_role: buyer, category: returns |
| 2 | Bảo Hành Có Giới Hạn 1 Năm | [Apple Legal](https://www.apple.com/legal/warranty/products/warranty-rest-of-apac-vietnamese.html) | 2026-08-03 / not-stated | ~600 | customer_role: buyer, category: warranty |
| 3 | Chính Sách Quyền Riêng Tư | [Apple Privacy](https://www.apple.com/vn/legal/privacy/vn/) | 2026-08-03 / not-stated | ~600 | customer_role: both, category: privacy |
| 4 | Điều Khoản Dịch Vụ Truyền Thông | [Apple iTunes](https://www.apple.com/vn/legal/internet-services/itunes/vn/terms.html) | 2026-08-03 / not-stated | ~600 | customer_role: buyer, category: terms |
| 5 | Nhận Biết Thư Email Lừa Đảo | [Apple Support](https://support.apple.com/vi-vn/102568) | 2026-08-03 / not-stated | ~600 | customer_role: both, category: security |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string | `buyer`, `both` | Lọc chính xác quy định theo vai trò (người mua hoặc đối tượng chung), ngăn ngừa việc trả về các quy định không phù hợp với tư cách người dùng. |
| `category` | string | `returns`, `warranty`, `privacy`, `terms`, `security` | Phân loại rõ ràng từng nhóm chủ đề chính sách, hỗ trợ việc lọc chính xác hơn khi kho tài liệu mở rộng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên toàn bộ tài liệu của nhóm:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Toàn bộ Corpus Apple | FixedSizeChunker (`fixed_size`) | 9 | 362.8 ký tự | Cắt ký tự cố định nên dễ bị đứt ngang từ hoặc ngắt đôi câu ở vị trí vết cắt. |
| Toàn bộ Corpus Apple | SentenceChunker (`by_sentences`) | 7 | 407.9 ký tự | Rất tốt, luôn bảo toàn cấu trúc ngữ pháp và ý nghĩa trọn vẹn từng câu điều khoản. |
| Toàn bộ Corpus Apple | RecursiveChunker (`recursive`) | 15 | 189.5 ký tự | Tách linh hoạt theo đoạn và câu, giữ cấu trúc logic của bài viết tốt. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Đình Hoàng (2A202601436)**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=2)`
- **Mô tả & lý do chọn:** Gom nhóm tối đa 2 câu vào 1 chunk dựa trên các ranh giới kết thúc câu (`. `, `! `, `? `, `.\n`). Chiến lược này giúp giữ trọn vẹn ngữ nghĩa câu và cấu trúc thông tin của từng quy định chính sách Apple mà không bị ngắt đôi giữa chừng.
- **Code snippet:**
```python
from src.chunking import SentenceChunker

chunker = SentenceChunker(max_sentences_per_chunk=2)
```

**Thành viên 2 — Lương Hoàng Minh (2A202601490)**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=600)`
- **Mô tả & lý do chọn:** Đệ quy tách theo thứ tự ưu tiên đoạn (`\n\n`), dòng (`\n`) và câu với `chunk_size=600` ký tự. Kích thước chunk lớn giúp bảo toàn dung lượng thông tin nền rộng cho các câu hỏi phức tạp.
- **Code snippet:**
```python
from src.chunking import RecursiveChunker

chunker = RecursiveChunker(chunk_size=600)
```

**Thành viên 3 — Trần Tiến Dũng (2A202601064)**
- **Loại chiến lược:** `MarkdownHeaderChunker` (Custom)
- **Mô tả & lý do chọn:** Tách tài liệu dựa theo các thẻ tiêu đề Markdown `#`, `##`. Phù hợp tuyệt đối với định dạng văn bản pháp lý Apple khi mỗi mục tiêu đề đại diện cho đúng một điều khoản hoàn chỉnh.
- **Code snippet:**
```python
class MarkdownHeaderChunker:
    def chunk(self, text: str) -> list[str]:
        sections = text.split("\n#")
        return [("#" + s).strip() for s in sections if s.strip()]
```

**Thành viên 4 — Dương Văn Kiên (2A202601724)**
- **Loại chiến lược:** `BulletPointChunker` (Custom)
- **Mô tả & lý do chọn:** Tách văn bản theo từng dòng gạch đầu dòng (`- `). Do tài liệu chính sách Apple đa số trình bày dưới dạng từng dòng lưu ý gạch đầu dòng độc lập nên cách chia này giữ trọn vẹn ngữ cảnh của từng điều luật.
- **Code snippet:**
```python
class BulletPointChunker:
    def chunk(self, text: str) -> list[str]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return [l for l in lines if not l.startswith("---")]
```

**Thành viên 5 — Hoàng Thị Hà Huyền (2A202601909)**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=300, overlap=50)`
- **Mô tả & lý do chọn:** Chia kích thước cố định 300 ký tự với cửa sổ trượt overlap 50 ký tự. Overlap giúp hạn chế việc từ khóa quan trọng nằm ngay ranh giới bị ngắt quãng.
- **Code snippet:**
```python
from src.chunking import FixedSizeChunker

chunker = FixedSizeChunker(chunk_size=300, overlap=50)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Đình Hoàng | `SentenceChunker(2)` | 10/10 | Mạch lạc, giữ trọn vẹn ngữ nghĩa câu pháp lý | Phụ thuộc chất lượng chấm câu |
| Lương Hoàng Minh | `RecursiveChunker(600)` | 9/10 | Bối cảnh rộng, đầy đủ thông tin nền | Đôi khi chứa thêm thông tin phụ |
| Trần Tiến Dũng | `MarkdownHeaderChunker` | 10/10 | Bảo toàn hoàn hảo cấu trúc từng tiêu đề điều khoản | Phụ thuộc vào định dạng Markdown |
| Dương Văn Kiên | `BulletPointChunker` | 9/10 | Tách chính xác từng dòng gạch đầu dòng quy định | Phụ thuộc dấu gạch đầu dòng |
| Hoàng Thị Hà Huyền | `FixedSizeChunker(300, 50)` | 8/10 | Cửa sổ trượt giảm hiện tượng ngắt từ | Cắt ngắt ngơ ranh giới câu |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược **`SentenceChunker(2)`** và **`MarkdownHeaderChunker`** đem lại hiệu quả truy xuất tốt nhất cho bộ chính sách của Apple Store. Lý do là các quy định pháp lý TMĐT được viết dưới dạng các câu hoặc điều khoản độc lập; việc tách theo ranh giới câu/tiêu đề giúp mỗi chunk mang thông tin trọn vẹn mà không bị ngắt đôi hay lẫn lộn ý nghĩa.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store? | Bạn có thể hoàn trả các sản phẩm đủ điều kiện trong vòng 14 ngày kể từ ngày nhận được sản phẩm. | `k4-apple-sales-refund.md` |
| 2 | Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không? | Không. Bảo hành không áp dụng cho các linh kiện tiêu hao, như pin hoặc các lớp bảo vệ được thiết kế là sẽ hao mòn theo thời gian. | `k4-apple-warranty.md` |
| 3 | Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không? | Trẻ em dưới 15 tuổi không được tạo tài khoản trừ khi được cha mẹ hoặc người giám hộ hợp pháp chấp thuận thông qua Chia sẻ trong gia đình. | `k4-apple-media-terms.md` |
| 4 | (Filter role: buyer) Là người mua, tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không? | Tất cả các giao dịch mua nội dung số trên App Store là giao dịch cuối cùng và không thể hoàn tiền (trừ khi pháp luật quy định khác). | `k4-apple-media-terms.md` |
| 5 | (Filter role: both) Tôi nhận được email yêu cầu cung cấp số thẻ tín dụng từ Apple, tôi có nên làm theo không? | Không. Apple sẽ không bao giờ yêu cầu cung cấp số thẻ tín dụng qua email. Bạn nên chuyển tiếp email đó đến reportphishing@apple.com. | `k4-apple-phishing.md` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn hoàn trả sản phẩm từ Apple Store | `SentenceChunker` / `FixedSizeChunker` | Có (2/2 điểm) | Trích xuất đúng mốc 14 ngày |
| 2 | Điều khoản bảo hành cho pin và lớp bảo vệ | `SentenceChunker` / `BulletPoint` | Có (2/2 điểm) | Trích đúng mục ngoại trừ bảo hành |
| 3 | Quy định tài khoản Apple ID cho trẻ dưới 15 tuổi | `RecursiveChunker(600)` / `MarkdownHeader` | Có (2/2 điểm) | Trích đúng điều kiện Chia sẻ gia đình |
| 4 | Lọc người mua: Hoàn tiền ứng dụng App Store | `SentenceChunker` + Filter `customer_role: buyer` | Có (2/2 điểm) | Bộ lọc loại bỏ hoàn toàn thông tin nhiễu |
| 5 | Lọc chung: Xử lý email yêu cầu thông tin thẻ | `SentenceChunker` + Filter `customer_role: both` | Có (2/2 điểm) | Truy xuất đúng khuyến cáo bảo mật |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Metadata filtering đóng vai trò vô cùng quan trọng ở **Câu hỏi 4 và Câu hỏi 5**. Ở câu 4, tiền lọc `customer_role: buyer` giúp loại bỏ triệt để các chính sách không thuộc nhóm người mua; ở câu 5, lọc `customer_role: both` giúp khoanh vùng các tài liệu hướng dẫn an toàn dùng chung cho mọi đối tượng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Bản chất chiến lược Chunking:** Chia nhỏ theo ranh giới ngữ nghĩa (câu/tiêu đề) vượt trội so với chia cố định theo số ký tự đối với tài liệu chính sách.
2. **Sức mạnh của Metadata Filtering:** Tiền lọc trước khi tính cosine similarity giúp loại bỏ hoàn toàn nhiễu, nâng cao tốc độ và độ chính xác cho hệ thống RAG.
3. **Ảnh hưởng của Embedding backend:** Mock Embedder hữu ích cho thử nghiệm đơn vị, nhưng mô hình ngữ nghĩa thực sự (như `sentence-transformers`) là bắt buộc để ứng dụng sản phẩm thực tế.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu, chiến lược `FixedSizeChunker` dễ làm ngắt từ ngữ ranh giới gây mất ngữ cảnh; trong khi `SentenceChunker` và các chiến lược custom (`MarkdownHeader`, `BulletPoint`) bảo toàn thông tin hoàn chỉnh, giúp RAG Agent sinh câu trả lời chính xác hơn hẳn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa dữ liệu đầu vào theo định dạng Markdown có cấu trúc thẻ H2/H3 nhất quán hơn nữa và xây dựng một Custom Chunker chuyên biệt tự động nhận diện từng điều khoản pháp lý để chia nhỏ tối ưu hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
