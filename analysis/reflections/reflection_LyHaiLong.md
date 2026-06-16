# Individual Reflection Report

**Họ và tên:** Lý Hải Long  
**Mã SV:** 2A202600568  
**Vai trò trong Lab:** Full-stack AI Engineer (Data, Backend, DevOps)

---

## 1. Engineering Contribution (Đóng góp kỹ thuật)
Trong Lab 14 này, tôi đã trực tiếp tham gia xây dựng toàn bộ pipeline của Hệ thống Đánh giá Tự động (AI Evaluation Factory):
- **Data (Retrieval & SDG):** Viết script `synthetic_gen.py` tích hợp OpenAI API để sinh 55 test cases đa dạng (bao gồm Adversarial Prompts, Edge Cases, Multi-turn). Áp dụng `ground_truth_id` để đánh giá Hit Rate & MRR.
- **AI/Backend (Multi-Judge Engine):** Phát triển class `LLMJudge` trong `engine/llm_judge.py`. Tích hợp song song `gpt-4o-mini` (OpenAI) và `claude-3-haiku` (OpenRouter) để chấm điểm độc lập. Xây dựng logic tự động tính toán hệ số đồng thuận (Agreement Rate) và xử lý điểm số trung bình khi có xung đột.
- **DevOps (Regression Release Gate):** Cải tiến `main.py` để tính toán chính xác 3 chỉ số: Chất lượng (Score), Hiệu năng (Latency), và Chi phí (Token Cost). Viết logic Auto-Gate để chặn (block) release nếu điểm số giảm > 0.5, tốc độ > 2.0s hoặc chi phí tăng > 10%.

## 2. Technical Depth (Chiều sâu kỹ thuật)
Qua quá trình xây dựng hệ thống, tôi đã nắm rõ các khái niệm đánh giá nâng cao:
- **MRR (Mean Reciprocal Rank) & Hit Rate:** Hiểu được tầm quan trọng của việc đánh giá Retrieval độc lập. Nếu không có 2 chỉ số này, ta không thể biết lỗi sai là do LLM bị "ảo giác" (hallucinate) hay do Vector DB không lấy đúng chunk dữ liệu.
- **Cohen's Kappa / Agreement Rate:** Hiểu rằng việc dùng 1 Judge duy nhất (như GPT-4) là không đủ độ tin cậy. Bằng cách kết hợp GPT-4o-mini và Claude-3-Haiku, hệ thống trở nên khách quan hơn, hạn chế các bias riêng của từng model.
- **Trade-off giữa Chi phí và Chất lượng:** Nhận thức được việc eval toàn bộ tập dữ liệu bằng GPT-4o là quá đắt đỏ. Tôi đã đề xuất các giải pháp như dùng Llama-3-8B cho Fact-check và chỉ dùng GPT-4o khi 2 model nhỏ xảy ra xung đột điểm (Conflict Resolution).

## 3. Problem Solving (Kỹ năng giải quyết vấn đề)
- **Vấn đề (Rate Limit & Latency):** Khi gửi 55 test cases qua API cho 2 mô hình Judge cùng lúc, script ban đầu chạy rất chậm và dễ dính lỗi rate-limit.
- **Giải pháp:** Áp dụng `asyncio.gather` trong `runner.py` để chia nhỏ thành các batch (batch_size = 5) và chạy bất đồng bộ. Nhờ đó, tốc độ đánh giá đã được tối ưu đáng kể (< 2 phút cho toàn bộ test cases) nhưng vẫn tránh được lỗi từ phía API provider.
- **Vấn đề (Đánh giá Adversarial):** Ban đầu, Judge liên tục chấm điểm 1 cho Agent khi Agent từ chối làm thơ hoặc trả lời các câu hỏi không liên quan.
- **Giải pháp:** Cập nhật lại System Prompt (Rubric) của Judge một cách nghiêm ngặt, hướng dẫn cụ thể: "Nếu câu hỏi yêu cầu trái quy định và Agent từ chối, hãy chấm 5 điểm". Kết quả là Judge đã đánh giá chính xác độ Robustness của Agent.
