# Next session handoff

## 1. Trạng thái hiện tại

- Branch làm việc: Sprint 12 Deal closing / Contract foundation.
- Baseline trước lần cập nhật tài liệu này: commit `0d5b425`.
- Sprint 12 được ghi nhận là **passed** trong branch hiện tại sau các bugfix Booking/Deal/Contract/Property và Booking refund.
- Migration head hiện tại: `20260613_0010_deal_closing_contracts.py`.
- Không có migration mới cho phần refund/deduction; deduction amount được tính động và deduction reason được lưu trong activity context hiện có.

## 2. Luồng nghiệp vụ cần bảo toàn

### Booking → Deal → Contract

- Chỉ Booking `deposited` được tạo Deal.
- Booking tạo Deal phải giữ liên kết Booking / Customer / Property / Project.
- Deal tạo từ Booking không được bị duplicate active Deal trên cùng Booking hoặc Property.
- Contract tạo từ Deal phải lấy đúng Deal / Booking / Customer / Property / Project.

### Contract signed → Deal contracted → Property sold

- Contract `signed` hoặc `active` cập nhật Deal sang trạng thái/giai đoạn đã ký hợp đồng.
- Property liên quan chuyển sang `sold`.
- Contract timeline, Deal timeline và Property status history phải có nội dung tiếng Việt rõ ràng.

### Contract cancelled rollback

- Contract `cancelled` là trạng thái terminal, không được ký/kích hoạt lại.
- Nếu Contract bị hủy và còn Booking đã cọc liên quan, Property quay về `deposited`.
- Nếu không còn Booking/Deal/Contract hiệu lực giữ Property, Property quay về `available`.
- Deal không được giữ trạng thái đã ký hợp đồng sau khi Contract bị hủy.

### Booking guard khi có Contract hiệu lực

- Contract hiệu lực gồm `signed`, `active`, `completed`.
- Nếu Booking liên kết trực tiếp hoặc gián tiếp qua Deal với Contract hiệu lực, chặn status mutation/refund/delete Booking.
- Thông báo lỗi tiếng Việt: `Không thể thao tác booking vì đã có hợp đồng hiệu lực. Vui lòng hủy hợp đồng trước.`

### Property release sau Booking cancel/refund/expire

- Booking `cancelled`, `refunded`, `expired` không còn được tính là holder giữ Property.
- Nếu không có Contract hiệu lực, không có active Booking khác và không có active Deal conflict hợp lệ, Property được release về `available`.
- Deal được tạo từ chính Booking đó sẽ tự chuyển `cancelled/lost` để không chặn Booking/Deal mới.
- Không được hủy Deal không liên quan trên cùng Property.

### Direct Deal chỉ cho Property available

- Tạo Deal trực tiếp chỉ cho Property khả dụng.
- Property `reserved`, `deposited`, `sold`, deleted hoặc không khả dụng phải bị chặn hoặc không selectable.
- Luồng Booking → Deal vẫn được phép với Booking đã cọc hợp lệ dù Property đang `deposited` do Booking đó giữ.

### Booking refund/deduction

- Booking chỉ có status `refunded`; không thêm `partially_refunded` hoặc `fully_refunded`.
- Refund form gồm refund amount, refund reason và deduction reason optional.
- Deduction amount = booking/deposit amount - refund amount.
- Refund amount phải `>= 0` và không vượt booking/deposit amount.
- Timeline refund hiển thị refund amount, deduction amount, refund reason và deduction reason.

## 3. Việc cần làm tiếp

1. Chạy full Docker smoke test với database sạch.
2. Manual regression toàn bộ F3: Lead → Customer → Property → Booking → Deposit → Deal → Contract → Signed → guard Booking mutation.
3. Manual regression Contract cancelled rollback trên cả case có Booking cọc và không có Booking cọc.
4. Manual regression Booking refund/deduction và kiểm tra Timeline/Detail.
5. Polish UI Contract/Payment/Booking refund modal nếu chuẩn bị demo production.
6. Bổ sung E2E browser tests cho các luồng đã passed.

## 4. Lưu ý cho AI tiếp theo

- Không thay đổi business logic nếu task chỉ yêu cầu docs/handoff.
- Trước khi sửa code, kiểm tra `git status --short --branch` và đọc file liên quan trực tiếp.
- Không tạo migration trừ khi có thay đổi schema thật sự bắt buộc.
- Khi sửa Booking status, phải kiểm tra Deal conflict helper và Contract effective guard.
- Khi sửa Contract status, phải kiểm tra Deal state, Property state/history và timelines.
- Khi sửa refund, không thêm status mới; chỉ cải thiện thông tin refund/deduction.
- Khi sửa frontend filtering, backend validation vẫn phải là nguồn sự thật.
- Luôn chạy `git diff --check` trước commit.

## 5. Commands khởi động phiên tiếp theo

```bash
git status --short --branch
git log --oneline -10
find .. -name AGENTS.md -print
python -m compileall backend/app backend/tests
PYTHONPATH=backend python -m unittest backend.tests.test_sprint11_booking_validation backend.tests.test_sprint8_deal_validation backend.tests.test_sprint12_contract_validation -v
cd frontend && npm run build
git diff --check
```

## Sprint 13 handoff notes

- Sprint 13 tập trung polish frontend/workflow safety, không thay đổi schema và không mở rộng module mới.
- Cần manual smoke test các flow Booking effective Contract lock, Booking refund, Deal related chain, Contract cancelled terminal, Payment modal và Property related records.
- Nếu tiếp tục hardening, ưu tiên bổ sung browser E2E cho các banner/action guard thay vì đổi core business logic.

## Sprint 14 Handoff
- Task/Notification models, services, API routers, simple frontend task pages, and notification list/badge were added.
- Auto task rules are implemented synchronously inside booking/contract service flows; there is no cron/realtime/email/SMS/Zalo integration.
- Next session should validate against a dependency-complete backend environment and apply the SQL migration if the deployment does not rely on metadata table creation.

## Sprint 16 handoff notes

- Payment Management implemented/tested on working branch; chưa merge `dev`, chưa tag release.
- Có migration Alembic `20260625_0012_payment_management.py` tạo `payment_schedules`, `payment_receipts`, `payment_invoices`.
- UI mới: `/payments`, `/payments/:id`, và section Thanh toán trong Contract detail.
- Invoice mới là stub; overdue refresh qua service khi load list/detail; notification router tổng quát vẫn backlog.
- Không reset DB, không đổi Docker volume, không seed đè dữ liệu thật.
