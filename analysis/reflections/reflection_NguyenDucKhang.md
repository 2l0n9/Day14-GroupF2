# Reflection - Nguyễn Đức Khang

**Họ và tên:** Nguyễn Đức Khang  
**Mã sinh viên:** 2A202600588

## Đóng góp kỹ thuật
- Hoàn thiện evaluation pipeline offline có thể chạy tự động bằng `python main.py`.
- Xây dựng golden dataset 50 cases với `expected_retrieval_ids`, gồm 10 hard/red-team cases.
- Triển khai RAG agent deterministic có retrieval IDs, Unicode normalization cho tiếng Việt, title boost và keyword reranking.
- Triển khai RetrievalEvaluator với Hit Rate, MRR, faithfulness và relevancy.
- Triển khai Multi-Judge consensus gồm 2 judge profiles, agreement rate, conflict handling và kappa-style metric.
- Thêm regression release gate so sánh V1/V2 theo score, retrieval, latency và estimated cost.

## Hiểu biết kỹ thuật
- **MRR:** đo vị trí của tài liệu đúng đầu tiên trong danh sách truy xuất. Nếu tài liệu đúng đứng hạng 1 thì MRR = 1, đứng hạng 2 thì MRR = 0.5.
- **Hit Rate:** đo việc có ít nhất một tài liệu ground-truth xuất hiện trong top-k retrieval hay không.
- **Cohen's Kappa:** dùng để ước lượng mức độ đồng thuận giữa các judge sau khi loại trừ phần đồng thuận ngẫu nhiên. Trong repo, metric này được mô phỏng bằng biến thể bucketed/weighted.
- **Position Bias:** judge có thể thiên vị câu trả lời xuất hiện trước, vì vậy cần kiểm tra bằng cách đổi thứ tự response A/B.
- **Cost vs Quality:** câu trả lời ngắn gọn giúp giảm token/cost và tăng precision của judge, nhưng vẫn cần đủ bằng chứng để đảm bảo faithfulness.

## Bài học và hướng cải tiến
- Với tiếng Việt, tokenizer ASCII có thể làm retrieval sai nghiêm trọng; Unicode normalization là bước bắt buộc.
- Không nên chỉ đo chất lượng câu trả lời. Retrieval metrics giúp phát hiện lỗi trước khi generation che lấp nguyên nhân.
- Hard cases giúp tìm ra lỗi thực tế: prompt injection, out-of-context và deadline edge đều cần logic xử lý riêng.
- Nếu triển khai production, cần thay heuristic judge bằng multi-model LLM thật, lưu raw judge output và audit các conflict cases thủ công.
