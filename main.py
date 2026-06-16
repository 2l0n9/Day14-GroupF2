import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge

from engine.retrieval_eval import RetrievalEvaluator

# Sử dụng RAGAS/Retrieval Evaluator thật
class ExpertEvaluator:
    def __init__(self):
        self.retrieval_eval = RetrievalEvaluator()

    async def score(self, case, resp): 
        # Lấy Ground Truth ID từ test case
        expected_id = case.get("ground_truth_id", "")
        # Lấy retrieved IDs từ Agent (giả lập trả về sources)
        retrieved_ids = resp.get("metadata", {}).get("sources", [])
        
        hit_rate = self.retrieval_eval.calculate_hit_rate([expected_id], retrieved_ids)
        mrr = self.retrieval_eval.calculate_mrr([expected_id], retrieved_ids)
        
        return {
            "faithfulness": 0.9, # RAGAS generation metrics can be integrated here
            "relevancy": 0.8,
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr}
        }

async def run_benchmark_with_results(agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    # Sử dụng LLMJudge thật (Multi-Judge API)
    runner = BenchmarkRunner(MainAgent(), ExpertEvaluator(), LLMJudge())
    
    # Để tiết kiệm token và thời gian trong Lab, lấy 5 samples đầu tiên thay vì toàn bộ
    # (Nếu muốn chạy thật, đổi thành: results = await runner.run_all(dataset))
    test_data = dataset[:5]
    print(f"Đang chạy đánh giá trên {len(test_data)} test cases...")
    results = await runner.run_all(test_data)

    total = len(results)
    summary = {
        "metadata": {"version": agent_version, "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "avg_latency": sum(r["latency"] for r in results) / total,
            "avg_tokens": sum(r["tokens"] for r in results) / total,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total
        }
    }
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    print("--- CHẠY BENCHMARK V1 ---")
    v1_summary = await run_benchmark("Agent_V1_Base")
    
    # Giả lập một chút thay đổi cho V2 (thường thì bạn sẽ gọi một Agent class khác)
    print("\n--- CHẠY BENCHMARK V2 ---")
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    
    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    
    m1 = v1_summary["metrics"]
    m2 = v2_summary["metrics"]
    
    delta_score = m2["avg_score"] - m1["avg_score"]
    delta_latency = m2["avg_latency"] - m1["avg_latency"]
    delta_tokens = m2["avg_tokens"] - m1["avg_tokens"]
    
    print(f"⭐ Quality (Score) : V1 = {m1['avg_score']:.2f} | V2 = {m2['avg_score']:.2f} | Delta: {delta_score:+.2f}")
    print(f"⏱️ Performance (s)  : V1 = {m1['avg_latency']:.2f}s | V2 = {m2['avg_latency']:.2f}s | Delta: {delta_latency:+.2f}s")
    print(f"💰 Cost (Tokens)   : V1 = {m1['avg_tokens']:.0f} | V2 = {m2['avg_tokens']:.0f} | Delta: {delta_tokens:+.0f}")
    
    # Tính chi phí ($) giả lập cho gpt-4o-mini (khoảng $0.0003 / 1k tokens)
    cost_v2_usd = (m2['avg_tokens'] * total) * 0.0003 / 1000
    print(f"💵 Total Eval Cost : ${cost_v2_usd:.5f} (for {total} cases)")
    print("\n💡 [EXPERT TIP] Đề xuất giảm 30% chi phí Eval:")
    print("   1. Áp dụng Prompt Caching của Anthropic/OpenAI cho phần Rubric của Judge.")
    print("   2. Chuyển sang LLM-as-a-Judge nhỏ hơn (vd: Llama-3-8B local) cho các câu hỏi dễ (Fact-check).")
    print("   3. Chỉ dùng GPT-4o cho các ca xung đột (Conflict Resolution).")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    # AUTO-GATE LOGIC (Quy định Release)
    print("\n🚪 --- KIỂM TRA ĐIỀU KIỆN PHÁT HÀNH (AUTO-GATE) ---")
    reasons = []
    
    # Điều kiện 1: Quality không được giảm quá 0.5 điểm
    if delta_score < -0.5:
        reasons.append(f"❌ Chất lượng giảm quá mức cho phép ({delta_score:+.2f} < -0.5).")
    else:
        print(f"✅ Quality Test Passed.")
        
    # Điều kiện 2: Performance (Latency) không được vượt quá 2.0 giây
    if m2["avg_latency"] > 2.0:
        reasons.append(f"❌ Tốc độ V2 quá chậm ({m2['avg_latency']:.2f}s > 2.0s).")
    else:
        print(f"✅ Performance Test Passed.")
        
    # Điều kiện 3: Cost không được tăng quá 10%
    if m1["avg_tokens"] > 0 and m2["avg_tokens"] > (m1["avg_tokens"] * 1.10):
        reasons.append(f"❌ Chi phí token tăng vượt mức 10%.")
    else:
        print(f"✅ Cost Test Passed.")

    if not reasons:
        print("\n🚀 QUYẾT ĐỊNH CUỐI CÙNG: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE RELEASE)")
    else:
        print("\n⛔ QUYẾT ĐỊNH CUỐI CÙNG: TỪ CHỐI (BLOCK RELEASE)")
        for r in reasons:
            print(f"   {r}")

if __name__ == "__main__":
    asyncio.run(main())
