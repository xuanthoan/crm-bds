# Trạng thái dự án

## 1. Baseline tài liệu

- Cập nhật sau Sprint 15 Professional Deal Workflow.
- Tài liệu này phản ánh trạng thái thực tế mới nhất trong repository tại thời điểm cập nhật, không mô tả roadmap chưa triển khai như một tính năng đã có.
- Không có migration mới cho cập nhật tài liệu này.
- Không reset DB, không đổi Docker volume và không dùng `docker compose down -v`.

## 2. Trạng thái sprint

| Sprint | Trạng thái | Phạm vi chính |
|---|---:|---|
| 1 | Done/Merged | Project bootstrap, cấu trúc backend/frontend/local stack nền tảng |
| 2 | Done/Merged | Authentication & RBAC foundation |
| 3 | Done/Merged | Admin operations cho user/role/permission |
| 4 | Done/Merged | Lead Management Foundation |
| 5 | Done/Merged | Organization Structure & real lead scope |
| 6 | Done/Merged | Lead care, tasks/appointments và sales dashboard nền |
| 7 | Done/Merged | Customer 360 và Lead → Customer conversion |
| 8 | Done/Merged | Deal Pipeline Foundation |
| 9 | Done/Merged | Customer profile advanced, financial profile & scoring |
| 10 | Done/Merged | Project/Property Inventory Foundation |
| 11 | Done/Merged | Booking / giữ chỗ / đặt cọc / refund lifecycle |
| 12 | Done/Merged | Deal Closing / Contract Foundation, Contract Payment, guard/rollback nghiệp vụ |
| 13 | Done/Merged | UI/UX polish + workflow hardening cho Booking/Deal/Contract/Payment |
| 14 | Done/Merged | Task & in-app Notification Engine |
| 15 | Completed; approved, pending merge/tag | Professional Deal Workflow: Deal là trung tâm Booking → Deal → Contract → Payment → Complete/Lost |
| 16 | Next / In Progress | Payment Management |

> Ghi chú release: Sprint 15 đã completed, manual QA pass và approved. Trong repository hiện tại chưa có bằng chứng merge/tag `release-v0.15`, nên trạng thái được ghi là **approved, pending merge/tag**.

## 3. Module hiện có

### Đang hoạt động

- Authentication, refresh token, RBAC.
- User, role, permission administration.
- Department, team, user organization membership.
- Lead management, assignment, activity timeline.
- Lead tasks, appointments, dashboard nền.
- Customer 360, conversion, related people, scoring.
- Deal pipeline chuyên nghiệp với stage/status, assignment, timeline, contract guard, auto task và notification.
- Project và Property inventory, price/status history.
- Booking, reservation, deposit, refund và booking timeline.
- Contract, Contract Payment, Contract Activity.
- Booking → Deal → Contract → Payment → Completed/Lost integration.
- CRM-wide manual/auto Task foundation.
- In-app Notification list, unread badge và task notification link.
- Audit log backend cho các thao tác chính.

### Có nền tảng một phần

- Reports/Dashboard: có UI/permission nền và một số summary, chưa có reporting/revenue dashboard nâng cao.
- Notification Router: notification có dữ liệu liên quan task/deal/booking/contract nhưng chưa có router điều hướng đầy đủ cho mọi entity/use case.
- Contract/Payment UI đã chạy được nhưng vẫn còn dư địa polish component hóa và UX nâng cao.
- Docker/local stack có compose và cấu hình local; vẫn cần smoke test đều đặn trên database sạch hoặc bản sao dữ liệu phù hợp.

## 4. Business rules hiện hành

### Booking

- Booking active giữ Property ở `reserved`/`deposited` tùy trạng thái.
- Booking `deposited` có thể tạo Deal liên kết Booking / Customer / Property / Project.
- Booking có Contract hiệu lực qua Deal (`signed`, `active`, `completed`) bị chặn status mutation/refund/delete trực tiếp.
- Booking `cancelled`, `refunded`, `expired` release Property về `available` khi không còn Booking/Deal/Contract hiệu lực khác giữ Property.
- Booking cancel/refund/expire có thể auto-cancel active Deal tạo từ Booking nếu không có Contract hiệu lực, để không chặn flow mới.

### Deal

- Deal có hai khái niệm: `pipeline_stage` là giai đoạn pipeline; `status` là trạng thái xử lý/kết quả.
- Stage/status hiển thị bằng label tiếng Việt và badge màu, không hiển thị raw enum trong UI chính.
- Deal có Contract `signed`/`active` không được chuyển sang lost/cancelled hoặc downgrade về giai đoạn không hợp lệ; muốn hủy/thất bại Deal phải xử lý Contract trước.
- Deal có Contract `completed` bị khóa ở stage `completed` và status `completed`/`won`; API direct mutation ra khỏi trạng thái hoàn tất bị chặn.
- Contract `completed` tự chuyển Deal sang completed/won tương ứng và ghi timeline tiếng Việt: “Hợp đồng HD-xxxxx đã hoàn tất nên giao dịch được chốt thành công.”
- Deal lost/cancelled thủ công bắt buộc nhập lý do và ghi timeline; nếu không còn Booking/Contract hiệu lực giữ Property thì release Property an toàn theo logic hiện có.
- Cancelled Contract không khóa Deal; Deal có thể tiếp tục xử lý và tạo Contract mới nếu không còn active Contract.

### Contract / Payment

- Contract tạo từ Deal tự dẫn xuất Booking / Customer / Property / Project từ Deal.
- Mỗi Deal chỉ có một active Contract tại một thời điểm; Contract cancelled là terminal và không được ký/kích hoạt lại.
- Contract `signed`/`active` chuyển Deal sang đã ký hợp đồng và Property sang `sold`.
- Contract `completed` chuyển Deal sang hoàn tất, đặt `closed_at`, Property vẫn/được `sold`.
- Contract cancelled rollback Deal/Property về trạng thái phù hợp nếu không còn Contract hiệu lực khác.
- Contract Payment ghi timeline/audit, tính `total_paid`, `total_planned`, `remaining_amount`; Sprint 16 sẽ tiếp tục Payment Management chuyên sâu.

### Task / Notification

- Task có thể tạo thủ công hoặc tự động từ Booking/Contract/Deal event.
- Booking auto task: created/deposited và auto cancel khi Booking cancel/refund/expire.
- Contract auto task: payment follow-up và auto complete task thanh toán khi Contract completed.
- Deal auto task: `consulting`, `deposited/deposit`, `contract_pending/contract` tạo follow-up/chuẩn bị hợp đồng; chống trùng active task theo Deal/source event.
- Khi Deal đổi người phụ trách, active auto task liên quan Deal đổi assignee; task done/cancelled không bị reopen hoặc đổi assignee.
- In-app notification gửi đúng người nhận cho task assignment/auto task, Deal assignment và stage/status quan trọng. Không realtime/websocket, không email/SMS/Zalo.

## 5. Workflow mục tiêu hiện hành

```text
Lead
  -> Customer
  -> Booking reserved/deposited
  -> Deal deposited/contract_pending
  -> Contract draft/signed/active
  -> Contract Payment planned/paid/overdue/cancelled
  -> Contract completed
  -> Deal completed/won
```

Luồng Deal trực tiếp từ Customer/Property vẫn tồn tại khi Property `available`, sau đó có thể đi tiếp sang Contract và Payment.

## 6. Sprint 15 manual QA checklist đã pass

- Deal workflow basic: tạo Booking, đặt cọc, tạo Deal, chuyển stage hợp lệ, kiểm tra timeline.
- Contract lock: tạo Contract từ Deal, chuyển signed/active, thử hủy/thất bại Deal và bị chặn bằng thông báo tiếng Việt.
- Completed contract: chuyển Contract completed, Deal auto hoàn tất/thành công, thử chuyển ngược Deal và bị chặn.
- Cancelled contract: hủy Contract, Deal không bị khóa và có thể tạo Contract mới khi đủ điều kiện.
- Deal auto task: chuyển Deal sang consulting/contract_pending/deposited, task liên quan Deal xuất hiện ở `/tasks`, không tạo trùng.
- Deal reassignment: active auto task đổi assignee theo owner mới; task done/cancelled không đổi.
- Notification: Deal assignment/auto task tạo notification đúng user; badge header và `/notifications` không lỗi.
- Search: search theo deal_code, booking_code, contract_code, customer phone, property_code không lỗi 500.

## 7. Sprint 16 — Next / In Progress

Sprint 16 là **Payment Management**: hoàn thiện quản lý thanh toán sau Contract Payment foundation, bao gồm UX/quy trình payment sâu hơn, kiểm soát trạng thái thanh toán và các báo cáo/payment views cần thiết. Không mặc định bao gồm invoice/commission/revenue dashboard lớn nếu chưa được scope riêng.
