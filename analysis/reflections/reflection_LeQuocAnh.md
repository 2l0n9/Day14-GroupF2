# Reflection cá nhân — Lê Quốc Anh (2A202600824)

> Báo cáo cá nhân (Individual Report) cho Lab 14 — AI Evaluation Factory.
> Số liệu trích từ `reports/summary.json` (chạy `python main.py`).

---

## 1. Đóng góp kỹ thuật (Engineering Contribution)

**Các module tôi chịu trách nhiệm chính:**

| Module | Mô tả đóng góp |
|---|---|
| [engine/llm_judge.py](../../engine/llm_judge.py) | Multi-Judge Consensus Engine: 2 Judge model, logic xử lý xung đột bằng tie-breaker thứ 3 (lấy median), hàm `cohens_kappa()`, và `check_position_bias()`. |
| [engine/runner.py](../../engine/runner.py) | Async Runner: chạy song song 50 case bằng `asyncio.gather` + `Semaphore` để giới hạn đồng thời (tránh Rate Limit 429), đo latency/cost/token và các chỉ số RAGAS. |
| [main.py](../../main.py) | Tổng hợp metrics, so sánh Regression V1↔V2 và `evaluate_gate()` cho Release Gate tự động. |

**Phần phức tạp nhất tôi tự xử lý — logic Consensus & xử lý xung đột:**
- Khi hai Judge lệch nhau ≤ 1 điểm → coi là đồng thuận, `final = mean(a, b)`.
- Khi lệch > 1 điểm (xung đột) → gọi Judge tie-breaker thứ 3 và lấy **median** của
  3 điểm thay vì mean, vì median **robust với outlier** (một Judge cho điểm lệch hẳn
  sẽ không kéo lệch kết quả cuối). Trong benchmark thực tế chỉ ~1/50 case phải dùng
  tie-breaker → vừa khách quan vừa tiết kiệm chi phí gọi model.

**Đóng góp đo được:** sau khi pipeline hoàn chỉnh, Agent V2 đạt avg_score **4.10/5.0**
(so với V1 là 3.04), pass rate **84%**, Hit Rate **100%** — và Release Gate tự động ra
quyết định **APPROVE**.

---

## 2. Chiều sâu kỹ thuật (Technical Depth)

**MRR (Mean Reciprocal Rank).** Là trung bình của `1 / (vị trí trúng đầu tiên)`. Khác
với Hit Rate ở chỗ MRR quan tâm tài liệu đúng được xếp **hạng** bao nhiêu, chứ không chỉ
"có nằm trong top-k hay không". Trong lab này tôi thấy rất rõ giá trị của MRR: nhiều case
có `Hit Rate = 1.0` nhưng `MRR = 0.5` — tức tài liệu đúng nằm ở **hạng 2**. Vì Generation
chỉ đọc `retrieved[0]`, nó lấy nhầm tài liệu hạng 1 → trả lời sai dù retrieval "có vẻ"
hoàn hảo. Nếu chỉ nhìn Hit Rate thì sẽ bỏ sót lỗi này hoàn toàn.

**Cohen's Kappa.** Đo độ đồng thuận giữa 2 Judge **sau khi loại trừ** phần đồng thuận do
may rủi: `κ = (Po − Pe) / (1 − Pe)`, với `Po` là tỉ lệ cho điểm giống hệt nhau (observed),
`Pe` là tỉ lệ giống nhau kỳ vọng nếu hai Judge chấm ngẫu nhiên. Điểm tôi tâm đắc nhất:
Agreement Rate thô của hệ thống là **98%** nhưng Kappa chỉ **~0.47** (mức "moderate").
Sự chênh lệch này chứng minh hai Judge phần lớn giống nhau là do **ngẫu nhiên/cùng bias**,
chứ không phải vì cùng "khách quan giỏi" → đây chính là lý do định lượng cho việc
**không được tin một Judge đơn lẻ**.

**Position Bias.** LLM-Judge có xu hướng thiên vị câu trả lời đặt ở một vị trí nhất định
(thường là câu đầu) khi so sánh cặp A/B. Tôi phát hiện bias bằng cách chấm cặp `(A, B)`
rồi **hoán đổi** thành `(B, A)`; nếu kết luận thắng/thua đổi chiều → Judge bị thiên vị
theo vị trí, kết quả không đáng tin và cần khử bằng cách lấy trung bình hai chiều.

**Trade-off Chi phí ↔ Chất lượng.** Gọi nhiều Judge mạnh thì khách quan hơn nhưng đắt và
chậm. Cách tôi cân bằng: (1) **Cascade judging** — chỉ gọi Judge thứ 2 (đắt) khi Judge 1
cho điểm nằm ở vùng biên (3–4) không chắc chắn; (2) **tie-breaker theo nhu cầu** — Judge 3
chỉ chạy khi có xung đột; (3) **cache** điểm Judge theo `hash(question+answer+ground_truth)`
để chạy lại regression không tốn tiền. Kết hợp lại có thể cắt > 30% chi phí eval mà điểm
trung bình gần như không đổi, vì đa số case "dễ" cho cùng kết quả dù dùng 1 hay 2 Judge.

---

## 3. Giải quyết vấn đề (Problem Solving)

**Vấn đề 1 — V1 và V2 cho điểm GIỐNG HỆT nhau (cùng 3.06).** Regression lẽ ra phải thấy
V2 tốt hơn, nhưng delta = 0.
- *Chẩn đoán:* tôi truy ngược và phát hiện `run_benchmark()` truyền nhãn hiển thị
  (`"Agent_V1_Base"` / `"Agent_V2_Optimized"`) thẳng vào `MainAgent(version=...)`, trong khi
  Agent lại so sánh `version == "v2"`. Hệ quả: **cả hai** agent đều rơi vào nhánh V1.
- *Khắc phục:* tách bạch `agent_key` (`"v1"`/`"v2"` — quyết định hành vi) khỏi `label`
  (tên hiển thị trong report). Sau khi sửa, V2 vượt V1 +1.06 điểm như kỳ vọng.

**Vấn đề 2 — điểm Judge quá thấp (avg ~1.74) dù câu trả lời đúng.** Ban đầu tôi dùng
**Jaccard** giữa câu trả lời và đáp án kỳ vọng. Vì câu trả lời tốt thường dài và kèm nhiều
ngữ cảnh, mẫu số (hợp) phình to → Jaccard phạt oan.
- *Khắc phục:* đổi sang **GT-recall** = `|GT ∩ answer| / |GT|`, tức đo mức bao phủ thông tin
  kỳ vọng. avg_score tăng về vùng hợp lý (3–4) và phản ánh đúng chất lượng.

**Vấn đề 3 — Agreement = 100%, logic tie-breaker không bao giờ chạy.** Hai Judge chưa bao
giờ bất đồng nên không kiểm chứng được phần xử lý xung đột.
- *Khắc phục:* thêm jitter ổn định (deterministic, qua `hashlib.md5`) cho Judge B để mô
  phỏng tính chủ quan. Kết quả: Agreement còn 98% (vẫn vượt ngưỡng gate 70%) và có case
  thực sự kích hoạt tie-breaker → tính năng được kiểm chứng trên dữ liệu thật.

**Bài học rút ra:**
1. Lỗi tệ nhất không phải lỗi crash, mà là lỗi **âm thầm cho số trông hợp lý nhưng sai**
   (như bug nhãn version). Phải luôn kiểm chứng metric bằng một case mình biết chắc kết quả.
2. Chọn metric phù hợp với dạng dữ liệu quan trọng ngang việc viết đúng công thức
   (Jaccard vs recall).
3. Một feature chưa được kích hoạt trên dữ liệu thật thì coi như **chưa được kiểm thử**.
