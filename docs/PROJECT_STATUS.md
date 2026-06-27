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

## Sprint 16 implementation note (2026-06-25)

- Sprint 16 Payment Management đã được triển khai trên branch làm việc, chưa merge `dev` và chưa tạo tag release.
- Phạm vi đã có: payment schedule theo Contract, receipt/confirm/cancel, phí phạt thủ công, invoice stub, payment timeline qua Contract Activity, task/notification in-app cơ bản cho lịch đến hạn/quá hạn và trang UI `/payments`.
- Không reset DB, không đổi Docker volume, không seed đè dữ liệu thật.

## Sprint 17 — Receipt, Invoice & Contract Completion
- Bổ sung quản lý phiếu thu với danh sách/chi tiết, xác nhận, hủy có lý do bắt buộc và bản in bằng trình duyệt.
- Bổ sung quản lý hóa đơn/chứng từ với trạng thái Nháp / Đã phát hành / Đã hủy, tạo từ lịch thanh toán hoặc phiếu thu đã xác nhận, phát hành, hủy có lý do và bản in bằng trình duyệt.
- Hoàn tất hợp đồng chỉ được phép khi tiền cọc cộng tổng phiếu thu đã xác nhận của các lịch thanh toán chưa hủy đạt tối thiểu giá trị hợp đồng; nếu thiếu tiền, API trả lỗi tiếng Việt và không ghi timeline.
- Khi hợp đồng đã hoàn tất hoặc đã hủy, hệ thống chặn tạo mới lịch thanh toán, phiếu thu và hóa đơn; các dữ liệu tài chính cũ vẫn xem và in được.
- Giới hạn hiện tại: bản in phiếu thu/hóa đơn dùng `window.print()` của trình duyệt, chưa sinh PDF binary phía server.

## Sprint 18 — Finance Reports, Receivable Aging & Revenue Dashboard

Sprint 18 thêm hệ thống báo cáo tài chính tại frontend route `/reports/finance`, gồm KPI tổng quan, Công nợ hợp đồng, PMT quá hạn, Dòng tiền đã thu và Hóa đơn.

API mới:
- `GET /api/v1/reports/finance/summary`
- `GET /api/v1/reports/finance/receivables`
- `GET /api/v1/reports/finance/overdue-payments`
- `GET /api/v1/reports/finance/cash-collection`
- `GET /api/v1/reports/finance/invoices`
- `GET /api/v1/reports/finance/receivables/export`
- `GET /api/v1/reports/finance/overdue-payments/export`
- `GET /api/v1/reports/finance/cash-collection/export`
- `GET /api/v1/reports/finance/invoices/export`

Permissions:
- `reports.view.finance`: xem báo cáo tài chính; không có quyền thì backend trả 403 và frontend hiển thị “Bạn không có quyền xem báo cáo tài chính.”
- `reports.export`: xuất CSV báo cáo tài chính; không có quyền thì backend trả 403 và frontend ẩn nút xuất.
- Admin/superuser có toàn quyền xem và export.

Business rules Sprint 18:
- `receipt confirmed` mới tính vào đã thu.
- `receipt cancelled` không tính vào đã thu, KPI dòng tiền hay công nợ.
- `invoice issued` mới tính tổng hóa đơn phát hành.
- `invoice draft/cancelled` không tính vào tổng hóa đơn phát hành.
- `PMT overdue = due_date < today AND remaining > 0`; PMT đã paid không xuất hiện trong báo cáo quá hạn.
- Tổng đã thu hợp đồng = tiền cọc + phiếu thu confirmed; còn phải thu = max(contract_value - deposit_value - confirmed_receipts, 0).

Manual QA checklist:
- Admin mở `/reports/finance` thấy menu, KPI, các tab báo cáo và link detail dùng UUID nội bộ.
- Hủy phiếu thu làm giảm số đã thu và tăng còn phải thu.
- PMT quá hạn còn nợ xuất hiện, PMT paid không xuất hiện.
- Invoice issued được tính; invoice draft/cancelled không được tính.
- CSV tải được, có UTF-8 BOM để Excel đọc tiếng Việt.
- User không có `reports.view.finance` không thấy menu và bị chặn 403 khi gọi API.
- User có quyền xem nhưng không có `reports.export` xem được báo cáo nhưng không thấy nút xuất CSV.

## Sprint 19 — Sales Commission, Revenue Attribution & Performance Report

Sprint 19 adds dynamic reporting for sales commission and revenue attribution without creating payroll, accounting, commission payout, or multi-level approval workflows.

### Business rules
- Default `commission_rate_percent` is `1` (1%). API validates the rate from 0 to 100 and uses it only for report-time calculation.
- `estimated_commission = contract_value × commission_rate`.
- `confirmed_receipts_amount` includes only confirmed receipts; cancelled receipts are excluded.
- `total_collected_with_deposit = deposit_value + confirmed_receipts_amount`.
- `collected_commission = total_collected_with_deposit × commission_rate`.
- `eligible_commission = estimated_commission` only when the contract is completed or collected enough to cover contract value.
- Cancelled contracts are never commission eligible.
- Invoice data does not decide actual collected revenue or commission; invoices are evidence documents only.
- Detail links must use the internal UUID (`contract_id`) and display `contract_code` separately.

### API
- `GET /api/v1/reports/commissions/summary`
- `GET /api/v1/reports/commissions`
- `GET /api/v1/reports/revenue/by-sale`
- `GET /api/v1/reports/revenue/by-source`
- `GET /api/v1/reports/revenue/by-project`
- `GET /api/v1/reports/commissions/export`
- `GET /api/v1/reports/revenue/by-sale/export`
- `GET /api/v1/reports/revenue/by-source/export`
- `GET /api/v1/reports/revenue/by-project/export`

CSV exports use UTF-8 BOM, Vietnamese headers, raw numeric amounts, and filenames for sales commission, revenue by sale, revenue by lead source, and revenue by project/property.

### Permissions
- `reports.view.commissions`: required for commission summary/detail endpoints and `/reports/commissions` UI.
- `reports.view.revenue`: required for revenue attribution endpoints/tabs.
- `reports.export`: reused for all Sprint 19 CSV exports.
- Superuser/admin bypass remains available through the existing permission pattern.

### Frontend
- New route: `/reports/commissions`.
- New sidebar menu: “Báo cáo hoa hồng”.
- Page includes KPI cards, filters, four tabs (Hoa hồng, Doanh thu theo sale, Doanh thu theo nguồn, Doanh thu theo dự án), per-tab CSV export, loading/error/empty states, and “Hướng dẫn sử dụng” modal.

### Manual QA checklist
1. Admin sees menu “Báo cáo hoa hồng” and opens `/reports/commissions`.
2. KPI cards and all four tabs render.
3. Contract value 10,000 + deposit 2,000 + confirmed receipt 3,000 at 1% shows collected 5,000, remaining 5,000, estimated commission 100, collected commission 50, eligible commission 0 unless completed/fully paid.
4. Fully collected or completed contract shows eligible commission equal to contract value × rate.
5. Cancelled receipt reduces collected revenue and collected commission.
6. Cancelled contract shows commission status “Đã hủy” and eligible commission 0.
7. Revenue by sale/source/project matches contract grouping and collected totals.
8. Each CSV opens in Excel with Vietnamese text and numbers matching UI.
9. Users without view/export permissions are blocked or do not see export buttons.
10. Guide modal opens/closes and explains KPIs, tabs, and business rules.

### Known limitations
- This is a temporary/dynamic report, not payroll or an actual payout ledger.
- No commission payment voucher.
- No multi-person commission split.
- No approval/payment workflow for commissions.
