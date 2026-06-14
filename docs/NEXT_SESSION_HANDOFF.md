# Next session handoff

## 1. Trạng thái hiện tại

- Baseline tài liệu: commit `554caab`.
- Sprint 11 Booking đã nằm trong lịch sử qua merge `5015c62`.
- Sprint 12 Contract foundation đã có trong working branch tại baseline.
- Migration head: `20260613_0010`.
- Stack: FastAPI + SQLAlchemy + Alembic + PostgreSQL; React + TypeScript + Vite.
- Bộ tài liệu trong thư mục này phản ánh code hiện tại, không phải roadmap mục tiêu.

## 2. Chức năng cần bảo toàn

- Lead → Customer conversion một lần.
- Scoped permissions own/team/department/all.
- Deal linked inventory validation.
- Booking active uniqueness và row locking.
- Chỉ Booking deposited được tạo Deal.
- Contract dẫn xuất quan hệ từ Deal.
- Contract signed/active đồng bộ Deal/Property.
- Contract/payment timeline và payment totals.
- Soft-delete rules.

## 3. Việc nên làm tiếp theo dựa trên code debt

Ưu tiên kỹ thuật có bằng chứng trong code:

1. Chạy toàn bộ backend tests và frontend build trong môi trường đủ dependency.
2. Chạy Docker smoke test và migration trên database sạch.
3. Bổ sung integration tests với PostgreSQL cho Booking/Deal/Contract concurrency.
4. Thay application code generation bằng database sequences.
5. Hoàn thiện hoặc xóa các Contract UI placeholder.
6. Thêm frontend test framework và các regression tests cho combobox/contract flows.
7. Quyết định chuẩn hóa Deal final status `won` so với `completed`.
8. Làm rõ chiến lược `remaining_value` lưu trữ so với total tính động.

Product expansion chỉ nên bắt đầu sau khi xác nhận yêu cầu; code hiện chưa có commission/KPI/invoice/tax.

## 4. Cảnh báo cho phiên AI tiếp theo

- Đọc mọi `AGENTS.md` trước khi sửa file.
- Kiểm tra branch/HEAD và `git status`; không giả định prompt cũ khớp checkout hiện tại.
- Đọc migration và service, không dùng tài liệu roadmap cũ làm nguồn sự thật.
- Không đổi enum/status nếu chưa rà constants, schema, service, serializer, badge và tests.
- Không bỏ backend validation chỉ vì UI đã lọc.
- Giữ compatibility với legacy Deal text fields khi sửa inventory linkage.
- Khi sửa Contract lifecycle, kiểm tra cả Contract activity, Deal activity và Property status history.
- Không tạo migration nếu thay đổi không cần schema.
- Chạy `git diff --check` và xác nhận phạm vi diff trước commit.

## 5. Commands khởi động phiên

```bash
git status --short --branch
git log --oneline -10
find .. -name AGENTS.md -print
find backend/app -maxdepth 3 -type f | sort
find frontend/src -maxdepth 4 -type f | sort
find backend/alembic/versions -type f | sort
find backend/tests -maxdepth 1 -type f | sort
```

## 6. Definition of done tối thiểu cho thay đổi code

- Rule mới có validation backend.
- Permission/scope được kiểm tra.
- Audit/timeline được cập nhật nếu là thao tác nghiệp vụ.
- Migration có upgrade/downgrade nếu schema đổi.
- Unit/regression tests được bổ sung.
- Frontend build thành công.
- Docker/manual limitations được báo cáo rõ.
- Không merge/tag nếu task không yêu cầu.
