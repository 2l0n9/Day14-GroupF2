# Báo cáo Cá nhân: Nguyễn Đức Mạnh - 2A202600945

## 1. Đóng góp kỹ thuật (Engineering Contribution)
- **Module Retrieval Evaluation:** Tôi phụ trách nghiên cứu và lập trình các hàm tính toán chỉ số chất lượng tìm kiếm cho Agent (bao gồm Hit Rate và MRR) trong file `retrieval_eval.py`.
- **Tối ưu Pipeline & Async:** Tham gia thiết kế luồng chạy Benchmark song song/tuần tự cho hệ thống. Đặc biệt, tôi xử lý bài toán Rate Limit của các API Free bằng cách bổ sung cơ chế sleep và chia batch nhỏ (tuần tự) để đảm bảo hệ thống không bị crash khi quét 50 test cases.
- **Multi-Judge Consensus:** Cùng nhóm phát triển cơ chế đánh giá độc lập sử dụng 2 mô hình Judge, code logic so sánh điểm (Agreement) và gọi mô hình thứ 3 làm Trọng tài nếu có sự chênh lệch lớn.

## 2. Chiều sâu kỹ thuật (Technical Depth)
- **MRR (Mean Reciprocal Rank):** Đây là một độ đo đánh giá chất lượng của hệ thống tìm kiếm (Retriever). Nó quan tâm đến thứ hạng đầu tiên mà kết quả đúng xuất hiện. Ví dụ: Nếu chunk đúng chứa câu trả lời nằm ở vị trí top 1, điểm là 1. Nếu nằm ở top 2, điểm là 0.5. Chỉ số này rất quan trọng để đảm bảo context đúng được đưa vào prompt càng sớm càng tốt.
- **Position Bias:** Khi sử dụng mô hình LLM làm giám khảo (LLM-as-a-Judge) để so sánh 2 câu trả lời A và B, mô hình thường có thiên kiến ưu tiên câu trả lời xuất hiện trước (A). Để khắc phục, trong thực tế có thể dùng kỹ thuật đảo vị trí (swap positions) để chấm 2 lần rồi lấy trung bình.
- **Trade-off (Chi phí và Chất lượng):** Các mô hình như GPT-4o chấm điểm rất chuẩn nhưng tốn kém tài nguyên và dễ chạm ngưỡng giới hạn (Rate limit). Nhóm em đã quyết định thiết kế hệ thống sử dụng model nhẹ (như gpt-4o-mini) làm giám khảo vòng ngoài, và chỉ gọi các model nặng làm "Trọng tài" ở những câu có độ xung đột điểm số cao, giúp giảm hơn 50% chi phí.

## 3. Khó khăn và Cách giải quyết (Problem Solving)
- **Khó khăn:** Trong quá trình chạy thử pipeline 100 lần (cho 2 version), hệ thống liên tục trả về lỗi `HTTP 429 Too Many Requests` do bị giới hạn Rate Limit của API miễn phí, khiến bài kiểm tra bị ngắt quãng giữa chừng và mất toàn bộ số liệu.
- **Cách giải quyết:** Em đã thiết kế lại kiến trúc `runner.py`, chuyển từ `asyncio.gather` (gọi ồ ạt đồng thời) sang xử lý tuần tự kết hợp với hàm chờ `asyncio.sleep(3)` giữa mỗi request và `asyncio.sleep(20)` sau mỗi batch sinh dữ liệu. Phương pháp này đánh đổi bằng việc pipeline chạy lâu hơn khoảng 15 phút, nhưng bù lại đạt được độ ổn định 100%, tự động chạy xuyên đêm mà không cần người can thiệp.
