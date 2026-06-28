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

### Sprint 18 UI guide update

Sprint 18 đã bổ sung nút “Hướng dẫn sử dụng” trên trang `/reports/finance`. Modal hướng dẫn giải thích KPI, tab báo cáo, bộ lọc, CSV export và rule nghiệp vụ quan trọng: phiếu thu đã hủy không tính vào tiền đã thu, hóa đơn bản nháp/đã hủy không tính vào giá trị hóa đơn phát hành, tiền cọc được tính vào tổng đã thu, số liệu phụ thuộc quyền truy cập và người không có quyền export sẽ không thấy nút Xuất CSV.

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

## Sprint 20 — Commission Payout, Approval Workflow & Payment Tracking

Sprint 20 bổ sung nghiệp vụ quản lý hoa hồng thật từ hợp đồng đủ điều kiện: tạo bản ghi hoa hồng, duyệt, tạm giữ, hủy có lý do, đánh dấu đã chi trả, theo dõi timeline thao tác và xuất CSV.

### Quy tắc nghiệp vụ
- Chỉ tạo hoa hồng cho hợp đồng không bị hủy và đã hoàn tất hoặc đã thu đủ tiền.
- Tiền đã thu = tiền cọc hợp đồng + tổng phiếu thu trạng thái `confirmed`.
- Phiếu thu đã hủy không được tính vào điều kiện và số tiền hoa hồng.
- Hóa đơn không quyết định doanh thu thực thu hoặc hoa hồng.
- Hoa hồng đủ điều kiện = giá trị hợp đồng × tỷ lệ hoa hồng snapshot tại thời điểm tạo.
- Chỉ `eligible` hoặc `on_hold` được duyệt; số tiền duyệt không âm và không vượt hoa hồng đủ điều kiện.
- Chỉ `approved` được đánh dấu đã chi trả; số tiền chi trả không âm và không vượt số tiền đã duyệt.
- Chỉ `eligible` hoặc `approved` được tạm giữ và bắt buộc nhập lý do.
- Hoa hồng đã chi trả không được hủy; các trạng thái chưa chi trả khi hủy bắt buộc nhập lý do.
- Nếu dữ liệu phiếu thu thay đổi sau khi hoa hồng đã duyệt/chi trả, Sprint 20 giữ snapshot và chưa tự tạo điều chỉnh.

### API mới
- `GET /api/v1/commissions` — danh sách hoa hồng.
- `GET /api/v1/commissions/summary` — KPI tổng hợp hoa hồng.
- `POST /api/v1/commissions/generate` — tạo/cập nhật snapshot hoa hồng từ hợp đồng đủ điều kiện.
- `GET /api/v1/commissions/{id}` — chi tiết hoa hồng và timeline.
- `POST /api/v1/commissions/{id}/approve` — duyệt hoa hồng.
- `POST /api/v1/commissions/{id}/mark-paid` — đánh dấu đã chi trả.
- `POST /api/v1/commissions/{id}/hold` — tạm giữ hoa hồng.
- `POST /api/v1/commissions/{id}/cancel` — hủy hoa hồng.
- `GET /api/v1/commissions/export` — xuất CSV UTF-8 BOM với header tiếng Việt.

### Permissions mới
- `commissions.view`
- `commissions.create`
- `commissions.approve`
- `commissions.mark_paid`
- `commissions.hold`
- `commissions.cancel`
- `commissions.export`

Admin/superuser được bypass theo cơ chế permission hiện có. User thường cần permission tương ứng để xem/tạo/duyệt/tạm giữ/hủy/đánh dấu chi trả/xuất CSV. Row-level visibility của hoa hồng tuân theo các ràng buộc quyền hiện có nếu được mở rộng; hiện tại luồng Sprint 20 tối thiểu guard theo permission.

### Database
- Bảng `sales_commissions`: snapshot hợp đồng, sale, tỷ lệ hoa hồng, các số tiền eligible/approved/paid, trạng thái, người duyệt, người đánh dấu chi trả, lý do giữ/hủy và ghi chú.
- Bảng `sales_commission_events`: timeline thao tác `generated`, `regenerated`, `approved`, `held`, `cancelled`, `paid`.
- Migration mới: `backend/alembic/versions/20260627_0014_sales_commissions.py`.

### Frontend
- Menu “Hoa hồng”.
- Route `/commissions` cho danh sách, filter, KPI, action buttons theo quyền/trạng thái và modal “Hướng dẫn sử dụng”.
- Route `/commissions/:id` cho chi tiết snapshot, hợp đồng, sale/khách hàng, duyệt, chi trả, lý do/ghi chú và timeline.
- UI tiếng Việt, không dùng `window.alert`, `window.confirm`, `window.prompt`.

### Known limitations
- Chưa phải bảng lương.
- Chưa có phiếu chi kế toán.
- Chưa chia hoa hồng nhiều người.
- Chưa có workflow duyệt nhiều cấp.
- Chưa tự động tạo điều chỉnh hoa hồng khi dữ liệu thu tiền thay đổi sau duyệt/chi trả.

## Sprint 21 — Company Commission Receivable

Sprint 21 bổ sung tầng **Hoa hồng công ty** để quản lý khoản công ty môi giới/phân phối BĐS phải thu từ chủ đầu tư, chủ đất, chủ nhà, đối tác phân phối, khách hàng hoặc bên trả hoa hồng khác. Khoản này khác với **Sales Commission Payout** của Sprint 20: Company commission receivable là tiền công ty phải thu; Sales commission payout là tiền công ty chi nội bộ cho sale.

Các hợp đồng có thêm thông tin vai trò công ty, bên bán thực tế, bên trả hoa hồng, mã hợp đồng/chính sách môi giới và ghi chú căn cứ hoa hồng. Module `/company-commissions` có API list, summary, eligible-contracts, generate, detail, approve, receive, hold, cancel và export CSV. Quyền mới gồm `company_commissions.view`, `company_commissions.create`, `company_commissions.approve`, `company_commissions.receive`, `company_commissions.hold`, `company_commissions.cancel`, `company_commissions.export`.

Sprint 21 chưa thay đổi công thức hoa hồng sale của Sprint 20 và chưa bắt buộc chi hoa hồng sale phải phụ thuộc trạng thái đã nhận hoa hồng công ty. Backlog sprint sau: tính hoa hồng sale từ hoa hồng công ty, chặn/kiểm soát chi hoa hồng sale khi hoa hồng công ty chưa nhận, bổ sung báo cáo hoa hồng công ty theo bên trả hoa hồng, báo cáo công nợ hoa hồng công ty và báo cáo chênh lệch công ty nhận so với sale được chi.
