# AI Agent Guide

## 1. Mục đích

Hướng dẫn AI tiếp quản repository mà không dựa vào giả định hoặc tài liệu roadmap lỗi thời.

## 2. Quy trình bắt buộc trước khi sửa

1. Xác nhận `pwd`, branch, HEAD và dirty state.
2. Tìm và đọc toàn bộ `AGENTS.md` áp dụng cho file sẽ sửa.
3. Đọc request, xác định phạm vi được phép.
4. Đọc migration head và model/service/API/frontend tương ứng.
5. Đọc tests hiện có của sprint/module.
6. Lập kế hoạch nhỏ, tránh refactor ngoài yêu cầu.

## 3. Nguồn sự thật theo thứ tự

1. Migration cho schema đã triển khai.
2. SQLAlchemy model cho ORM/relationships.
3. Service cho business rule và transaction.
4. Schema cho request validation.
5. API router cho endpoint/permission dependency.
6. Frontend API/types/pages cho UX.
7. Tests cho regression contract.
8. Tài liệu trạng thái trong bộ docs này.
9. PRD/plan cũ chỉ dùng tham khảo, không dùng để khẳng định code có tính năng.

## 4. Bản đồ code

- `backend/app/api/v1/`: routes.
- `backend/app/services/`: business logic.
- `backend/app/schemas/`: Pydantic.
- `backend/app/models/`: ORM.
- `backend/app/*/constants.py`: enum labels.
- `backend/app/permissions/constants.py`: vocabulary và default role map.
- `backend/alembic/versions/`: schema history.
- `backend/tests/`: unittest/regression.
- `frontend/src/features/`: module UI.
- `frontend/src/routes/AppRoutes.tsx`: route guards.
- `frontend/src/layouts/AppLayout.tsx`: navigation.
- `docker-compose.yml`: local runtime.

## 5. Nguyên tắc thay đổi backend

- Không tin dữ liệu dẫn xuất từ frontend; tải entity và derive server-side.
- Mọi query aggregate phải cân nhắc `deleted_at`.
- Giữ scope `own/team/department/all`.
- Dùng HTTP status/message theo pattern module hiện có.
- Ghi audit cho create/update/status/delete quan trọng.
- Ghi activity/history khi UX timeline phụ thuộc vào sự kiện.
- Với inventory, kiểm tra Booking/Deal/Contract liên quan trước khi giải phóng status.
- Với lifecycle, cập nhật constants + schema + service + serializer + frontend labels + tests đồng bộ.
- Không bọc import trong `try/except`.

## 6. Nguyên tắc migration

- Không sửa migration đã phát hành nếu task cần migration mới.
- Revision/down_revision phải nối đúng head.
- Không destructive change nếu chưa được yêu cầu rõ.
- Tạo index/FK/unique constraint phù hợp.
- Đảm bảo downgrade hợp lệ.
- Import model trong model registry khi cần để metadata đầy đủ.

## 7. Nguyên tắc frontend

- Không thêm UI library nếu chưa được yêu cầu.
- Backend vẫn là nơi enforce rule.
- Route/menu phải theo permission.
- Không hiển thị raw enum khi đã có Vietnamese labels.
- Giữ responsive layout và empty/loading/error states.
- Khi edit legacy data, không làm mất trường cũ không thể map.
- `frontend/package.json` hiện không có test runner; ít nhất phải chạy production build.

## 8. Những bẫy hiện có

- Permission code tồn tại không có nghĩa module đã được triển khai.
- Deal final status có cả `won` và `completed`.
- Code generation max+1 không concurrency-safe.
- Redis được cấu hình nhưng chưa sử dụng.
- Contract feature có nhiều placeholder files.
- Booking và Deal có thể trỏ lẫn nhau qua source/link fields; phải phân biệt Deal nguồn và Deal tạo từ Booking.

## 9. Test matrix tối thiểu

```bash
python -m compileall backend/app backend/alembic backend/tests
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
(cd frontend && npm run build)
git diff --check
```

Nếu full discovery bị giới hạn dependency/environment, chạy các suite liên quan và ghi rõ suite nào chưa chạy cùng lý do.

## 10. Kỷ luật Git/PR

- Không đổi branch nền, merge hoặc tag ngoài yêu cầu.
- Xem `git diff --stat` và `git diff --name-only` trước commit.
- Commit chỉ chứa phạm vi task.
- Commit message mô tả mục tiêu, không phóng đại.
- PR body liệt kê thay đổi, tests và limitations.
- Không tuyên bố manual/browser/Docker pass nếu chưa thực sự chạy.

## 11. Cách cập nhật tài liệu

Khi code thay đổi:

- Schema: cập nhật `DATABASE_SCHEMA.md`.
- Module/sprint: cập nhật `PROJECT_STATUS.md`.
- Lifecycle/rule: cập nhật `WORKFLOWS.md` và `BUSINESS_RULES.md`.
- Debt/limitation: cập nhật `KNOWN_ISSUES.md`.
- Bàn giao: cập nhật `NEXT_SESSION_HANDOFF.md`.

Luôn trích từ code sau thay đổi, không sao chép nguyên yêu cầu rồi coi đó là implementation.
