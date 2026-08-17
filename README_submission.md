# Báo Cáo Đánh Giá Multi-Memory Agent (Lab 17)

## 1. Phân Tích Kết Quả Benchmark
- **Layer có hit rate thấp nhất**: Trong baseline `no-memory`, cả 3 layer bền vững (`long_term`, `episodic`, `semantic`) đều đạt **0% hit rate** do không lưu trữ xuyên session. Khi kích hoạt `StudentMemory`, toàn bộ 4 layer đạt **100% (11/11 PASS)**. `long_term` có độ trễ cao nhất (trung bình ~2.9s, E02 đạt ~5.8s) do tổng hợp context block và graph edges.
- **Query retrieve nhiều token nhất**: E03 (*Minh còn open loop hay deadline nào*) và E02 chiếm nhiều token nhất (**1710** và **1702 tokens**) ở layer `long_term` do chứa toàn bộ tóm tắt người dùng và danh sách facts lịch sử.
- **Case mixed (E07)**: Cần kết hợp **Long-term** (sở thích cá nhân: `Python`) và **Semantic** (quy tắc retry API: `Idempotency-Key`). Bắt buộc có cả hai evidence này để pass.
- **Token reduction**: Layer `semantic` giảm 67.8% - 74.2% token so với nạp toàn bộ KB. `no-memory` có token reduction cao (81.8%) vì không nạp gì (0 token cho durable layer) — tiết kiệm chi phí nhưng làm mất toàn bộ ngữ cảnh, dẫn đến hit rate chỉ đạt 18.2%.

## 2. Câu Hỏi Thực Hành & Kiến Trúc
- **Layer quan trọng nhất**: **Long-term Memory** (chiếm 5/11 test case: E02, E03, E08, E09 và E07). Đây là xương sống giúp Agent ghi nhớ profile, user preferences, open loops và đảm bảo cô lập dữ liệu người dùng (E09 User Isolation).
- **Trade-off Zep vs Redis + Qdrant**:
  - *Zep*: Tự động trích xuất entities/relations/facts, quản lý temporal validity (recency), tích hợp sẵn Context Block và User Isolation. Nhược điểm: phụ thuộc SaaS/API ngoài, latency mạng cao hơn.
  - *Redis + Qdrant*: Tốc độ cực nhanh tại local, chi phí cố định, toàn quyền kiểm soát hạ tầng; nhưng phải tự lập trình toàn bộ logic embedding, chunking, reranking, temporal resolution và schema validation.
- **Guardrail chống Memory Poisoning**:
  - Gắn tag *Provenance & Role* (chỉ ghi nhận facts từ system/verified tools).
  - Áp dụng *Policy-protected Trimming & Consent Gate* (lọc PII và kiểm duyệt nội dung trước khi ingest).
  - *Confidence Scoring & Conflict Validation* (phát hiện mâu thuẫn và gán trọng số độ tin cậy).

## 3. Cơ Chế Bổ Sung
- **Recency (E08)**: Khi Minh đổi stack BLUEBIRD-42 sang TypeScript/NestJS, Zep cập nhật `valid_at`/`invalid_at` trên graph edges, giúp ưu tiên quyết định mới nhất mà không xoá lịch sử cũ.
- **Compaction (E10)**: Khi vượt ngưỡng context, sliding window nén các turn cũ vào `SESSION_SUMMARY` nhưng giữ nguyên `DURABLE_NOTES` (`REVIEW-DEADLINE-1600`) để không mất ràng buộc quan trọng.
