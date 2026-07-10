# Business rules hiện tại

## 1. Quy tắc chung

- Các aggregate chính dùng soft delete; list/detail service lọc record đã xóa.
- Scope quyền theo `own/team/department/all`; superuser có toàn quyền.
- Owner/assignee bán hàng phải active, chưa xóa và thuộc nhóm role hợp lệ.
- Các thao tác chính ghi audit log.
- Các enum được validate ở schema/service; UI dùng label tiếng Việt tại các module mới.

## 2. Lead

- Primary phone là bắt buộc và được chuẩn hóa chỉ còn chữ số.
- Phone chính/phụ không được trùng với Lead chưa xóa khác.
- `budget_min <= budget_max`; `area_min <= area_max`.
- Status và priority phải thuộc constants.
- Khi status `lost`, phải có lý do mất.
- Lead chỉ chuyển thành Customer một lần.
- Lead conversion cập nhật status `converted` và liên kết Customer.

## 3. Customer

- Phone Việt Nam được chuẩn hóa về 10 chữ số bắt đầu bằng `0`; đầu `84` được chuyển đổi.
- Phone không được trùng Customer chưa xóa.
- Email phải đúng định dạng khi có.
- Ngày sinh không được ở tương lai.
- Các số tài chính/diện tích/số lượng không âm.
- Loan ratio nằm trong 0–100.
- Customer type/status phải thuộc enum schema.
- Customer có thể được tạo trực tiếp hoặc từ Lead.

## 4. Deal

- Customer phải tồn tại/chưa xóa.
- Source Lead, Project và Property nếu cung cấp phải tồn tại/chưa xóa.
- Property `sold` bị chặn khi tạo Deal mới hoặc đổi sang một Property sold khác.
- Existing Deal vẫn được giữ liên kết tới chính Property đã sold khi edit.
- Nếu `project_id` khác `property.project_id`, request bị từ chối.
- Khi có Property, backend không tin text từ frontend mà dẫn xuất code/type/area/project.
- Expected value lấy listed price khi payload chưa có giá trị.
- Contract value không được nhỏ hơn deposit amount.
- Chuyển Deal status sang `contracted` yêu cầu Contract `signed`, `active` hoặc `completed`.
- Stage `completed` đặt status `won`; stage `lost` đặt status `lost`.
- Status `won/completed/lost/cancelled` đặt `closed_at`.
- Deal lost/cancelled chỉ trả Property về `available` nếu Property chưa sold và không còn active Booking/Deal khác.

Active closing Deal statuses dùng khi kiểm tra xung đột:

- `open`
- `negotiating`
- `contract_pending`
- `contracted`
- `payment_in_progress`

## 5. Inventory

### Project

- Project code unique.
- Project status thuộc: `planning`, `opening`, `selling`, `handover`, `completed`, `paused`, `cancelled`.
- Project còn Property chưa xóa không được xóa.
- Deal form có thể dùng Project không bị xóa làm bộ lọc; project status không phải điều kiện trực tiếp để tạo Deal nếu Property hợp lệ.

### Property

- Property code unique.
- Project là tùy chọn.
- Inventory status thuộc: `available`, `reserved`, `negotiating`, `deposited`, `sold`, `locked`, `unavailable`.
- Thay đổi giá/trạng thái tạo history.
- Sold/deleted Property không hợp lệ cho Deal mới.

## 6. Booking

- Customer, Property, assigned user phải hợp lệ.
- Booking create chỉ nhận Property có status `available` hoặc `negotiating`.
- Mỗi Property tối đa một Booking active (`draft`, `reserved`, `deposited`), được bảo vệ cả ở application và partial unique index.
- Service khóa row Property khi tạo/đổi status.
- Booking/deposit amount nếu có phải lớn hơn 0.
- Chuyển `deposited` bắt buộc deposit amount > 0.
- Chuyển `cancelled` bắt buộc cancel reason.
- Chuyển `refunded` bắt buộc refund amount > 0 và refund reason.
- Reservation expiry nếu cung cấp phải ở tương lai tại thời điểm validation service.
- `reserved` cập nhật Property `reserved`.
- `deposited` cập nhật Property `deposited`.
- `cancelled`, `expired`, `refunded` có thể giải phóng Property về `available`, trừ các trạng thái được service bảo vệ như sold/locked/unavailable.
- Chỉ Booking `cancelled`, `expired`, `refunded` được soft delete.
- Chỉ Booking `deposited` được tạo Deal.
- Không tự refund Booking khi Deal/Contract bị hủy.

## 7. Contract

- Deal phải tồn tại/chưa xóa.
- Deal `cancelled` hoặc `lost` không được tạo Contract.
- Deal phải có Property.
- Contract value bắt buộc và > 0.
- Contract type/status phải thuộc constants.
- Một Deal không được có nhiều active Contract; active set là constants `ACTIVE_CONTRACT_STATUSES`.
- Booking/Customer/Property/Project luôn được dẫn xuất từ Deal khi tạo.
- Contract `signed`/`active`:
  - Deal -> `contracted`;
  - pipeline -> `contract_signed`;
  - Property -> `sold`.
- Contract `completed`:
  - Deal status/stage -> `completed`;
  - Property -> `sold`.
- Contract status change tạo Contract activity; signed/active/completed/cancelled còn tạo Deal activity tiếng Việt.
- Chỉ Contract `draft` hoặc `cancelled` được soft delete.
- Signed/active/completed Contract bị chặn xóa.

## 8. Payment

- Amount bắt buộc và > 0 lúc tạo.
- Payment type/status phải thuộc constants lúc tạo.
- Xác nhận payment đặt status `paid` và mặc định `paid_date=now`.
- Totals bỏ qua payment đã soft delete.
- `remaining_amount` không âm.
- Payment confirmation không tự complete Deal.
- Payment code được sinh tại application.

## 9. Permission mapping Contract

- Admin: toàn bộ contract/payment permissions.
- Director: view/update/status/payment all, không create và không delete theo mapping hiện tại.
- Sales Manager: create và scope department cho view/update/status/payment/confirm.
- Leader: create và scope team.
- Sale: create, own view/update/status, payment view/create/update; không confirm.
- Viewer: own contract/payment view.

## Sprint 14 — Task & Notification Rules
- Booking creation creates a follow-up task for the assigned sale; deposited bookings create a contract-signing task.
- Cancelled, refunded, or expired bookings automatically cancel open/in-progress non-general tasks directly linked to that booking.
- Contracts with remaining receivable create payment follow-up tasks; completed contracts auto-complete open/in-progress payment-due tasks for that contract.
- Task assignment creates in-app notifications only; Sprint 14 does not include realtime push, cron, email, SMS, or Zalo notifications.
- Manual task assignment: leaving assignee blank assigns the current user; non-admin users need `tasks.assign` to assign another active user, otherwise the API returns a Vietnamese permission error.

## 8. Payment Management (Sprint 16)

- Mỗi Contract có nhiều lịch thanh toán, không tạo lịch mới cho Contract đã hủy.
- `sequence_no` không được trùng trong cùng Contract.
- `expected_amount` và receipt `amount` phải lớn hơn 0.
- `remaining_amount = expected_amount + penalty_amount - paid_amount` và không âm.
- Chỉ receipt `confirmed` được cộng vào `paid_amount`; `draft` và `cancelled` không được tính.
- Không cho xác nhận receipt làm thanh toán vượt số tiền còn lại.
- Hủy receipt đã confirmed sẽ trừ lại `paid_amount` và tính lại trạng thái lịch thanh toán.
- Lịch chưa `paid/cancelled` có `due_date` trước ngày hiện tại sẽ chuyển `overdue` khi load/refresh qua service.
- Phí phạt không được âm; phí phạt lớn hơn 0 bắt buộc có lý do.
- Invoice Sprint 16 là stub nghiệp vụ, chưa phải hóa đơn kế toán/thuế đầy đủ.

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

## Sprint 22 — Chính sách chi hoa hồng sale theo hoa hồng công ty đã nhận

- Hoa hồng sale (COM) vẫn được tạo từ hợp đồng đủ điều kiện theo Sprint 20, kể cả khi hợp đồng chưa có hoa hồng công ty (CCR).
- Khi duyệt hoa hồng sale, hợp đồng bắt buộc phải có CCR và CCR không được ở trạng thái `on_hold` hoặc `cancelled`.
- CCR ở trạng thái `pending`, `approved`, `partially_received`, hoặc `received` cho phép duyệt hoa hồng sale.
- Khi đánh dấu đã chi trả hoa hồng sale, CCR bắt buộc phải ở trạng thái `partially_received` hoặc `received` và `received_amount` phải lớn hơn 0.
- Số tiền chi hoa hồng sale không được vượt số hoa hồng công ty đã nhận còn lại, đồng thời vẫn không được vượt số hoa hồng sale đã duyệt.
- Sprint 22 chưa hỗ trợ boss override, tạm ứng hoa hồng sale khi công ty chưa nhận tiền, hoặc cấu hình policy động theo từng công ty/dự án.
- Backlog sau Sprint 22: cấu hình policy theo công ty, boss override, tạm ứng hoa hồng sale, và tùy chọn tính hoa hồng sale trực tiếp từ company commission.

## Sprint 31 — Duplicate Lead Ownership & Customer Journey Rules

- **Một database chung:** CRM BĐS không tách database theo team/phòng. Phạm vi xem/sửa được xác định bằng `owner_id`, lead journey, team/phòng từ permission hiện tại và quyền cấp cao.
- **Customer Profile chung:** `customers` là hồ sơ khách hàng thật của công ty. Team/sale có journey lead gắn với customer trùng được xem thông tin chung: liên hệ, quan tâm, hồ sơ cá nhân, hồ sơ tài chính, nhu cầu & tiêu chí, người liên quan, điểm khách hàng và ghi chú/ngày/người upload ban đầu.
- **Team-scoped Journey:** `leads` là journey theo sale/team/phòng. Lead/journey/booking/deal/contract notes, comment, related links, activity và timeline riêng của team nào chỉ được team đó và cấp quản lý có quyền tương ứng xem; Admin/Giám đốc hoặc quyền `*.view.all` xem toàn bộ.
- **Duplicate rule:** Sprint 31 chỉ coi trùng chắc chắn theo số điện thoại chính/phụ sau chuẩn hóa. Các cặp match hợp lệ gồm primary-primary, primary-secondary, secondary-primary, secondary-secondary. Email, Zalo ID, Facebook link không được dùng làm điều kiện trùng chắc chắn.
- **Hành vi tạo lead trùng:** API tạo lead không fail mặc định khi trùng phone. Hệ thống tạo lead/journey mới thuộc owner/team/phòng của người upload sau, gắn vào Customer Profile chung đã tồn tại, đánh dấu duplicate và ghi audit/timeline lý do match.
- **Visibility rule:** Sale/user thường xem Customer Profile chung nếu họ có lead/journey thuộc customer đó, nhưng chỉ xem journey trong phạm vi permission hiện tại. Team Leader/Trưởng phòng xem profile và journey thuộc team/phòng mình. Admin/Giám đốc xem toàn bộ journey/team history.
- **Revenue/commission rule:** Doanh số và hoa hồng tính cho sale/team/phòng chốt hợp đồng có hiệu lực (contract/deal winning owner hoặc owner hiện có của deal/contract). First uploader không mặc định được chia doanh số/hoa hồng nếu không chốt hợp đồng.
- **Chưa làm trong Sprint 31:** Không làm dashboard lớn, co-sale/chia hoa hồng phức tạp, release policy tự động phức tạp, tách database theo team/phòng hoặc reset/xóa dữ liệu cũ.

## Sprint 32 — Dashboard Foundation & Revenue Attribution Verification

Sprint 32 bổ sung nền tảng Dashboard Foundation cho Boss/Giám đốc và khóa lại quy tắc Revenue Attribution kế thừa Sprint 31.

- API Boss Dashboard v1: `GET /api/v1/dashboard/boss` với quyền `dashboard.boss.view`, `dashboard.view.all` hoặc `reports.view.ceo_dashboard`.
- Date range presets dùng chung: `today`, `last_7_days`, `last_30_days` (mặc định), `this_month`, `last_month`, `custom`. Khoảng ngày được resolve từ 00:00 ngày bắt đầu đến trước 00:00 ngày kế tiếp của ngày kết thúc để tránh lỗi off-by-one.
- Metrics v1 gồm lead mới, lead chuyển khách hàng, booking, khách đã cọc, deal, hợp đồng ký, doanh số, hoa hồng công ty, hoa hồng sale, chi phí quảng cáo, ROI, funnel, time series theo ngày, breakdown nguồn/dự án và ranking top sale/team/project/source.
- Revenue attribution: doanh số tính theo hợp đồng hợp lệ `signed`/`effective`/`active`/`completed`/`won`, lấy giá trị `contracts.contract_value` và sale chốt từ owner của deal/contract hiện có. Doanh số không theo first_touch, không theo người upload lead đầu tiên, không theo lead creator và không tính cho team upload lead nếu team đó không chốt hợp đồng.
- Commission attribution: hoa hồng sale lấy từ `sales_commissions`; hoa hồng công ty lấy từ `company_commission_receivables`. Cả hai không dùng first_touch lead để phân bổ.
- Duplicate re-engagement không tính là lead mới vì Sprint 31 không tạo lead row mới khi trùng số điện thoại; dashboard có thể hiển thị `duplicate_reengagement_count` riêng nếu có activity tương ứng.
- ROI v1 dùng `roi_ratio = revenue_total / ads_cost_total` và `roi_profit_ratio = (revenue_total - ads_cost_total) / ads_cost_total`; nếu ads cost bằng 0 thì trả `null`, không chia cho 0.
- Chưa làm trong Sprint 32: dashboard trưởng phòng/team leader/kế toán/admin điều phối, export Excel/PDF dashboard, realtime dashboard phức tạp, multi-touch marketing attribution.

### Sprint 32.1 — Boss Dashboard UI/UX Polish & Financial KPIs

Sprint 32.1 mở rộng dashboard giám đốc nhưng không đổi revenue attribution: doanh số vẫn theo hợp đồng hợp lệ và deal/contract owner, không theo `first_touch` hoặc người upload lead đầu tiên; duplicate re-engagement không tính là lead mới.

Financial KPI bổ sung:
- `customer_paid_total`: tổng phiếu thu khách hàng đã xác nhận/đã thu trong range; nếu không có receipt hợp lệ thì trả 0.
- `customer_outstanding_total`: `max(revenue_total - customer_paid_total, 0)`.
- `avg_contract_value`: `revenue_total / contract_signed_count`, trả null nếu không có hợp đồng.
- `company_commission_outstanding_total`: `max(company_commission_receivable_total - company_commission_received_total, 0)`.
- `sales_commission_outstanding_total`: `max(sales_commission_approved_total - sales_commission_paid_total, 0)`.
- `gross_profit_received_estimate`: `company_commission_received_total - sales_commission_paid_total - ads_cost_total`.
- `gross_profit_receivable_estimate`: `company_commission_receivable_total - sales_commission_approved_total - ads_cost_total`.
- `company_commission_collection_rate`: `company_commission_received_total / company_commission_receivable_total`, null nếu mẫu số bằng 0.
- `sales_commission_payment_rate`: `sales_commission_paid_total / sales_commission_approved_total`, null nếu mẫu số bằng 0.

UI Sprint 32.1 chia KPI thành nhóm tinted cards, phóng to chart xu hướng, đổi funnel thành dạng hình thang/tầng, và giữ top 10 rankings. Sprint này vẫn chưa làm export Excel/PDF, realtime dashboard hoặc dashboard cho toàn bộ role.

### Sprint 32.2 — Boss Dashboard Visual Polish
- Sprint 32.2 chỉ polish UI dashboard: Modern KPI cards / KPI card hiện đại hơn với icon badge, subtitle, accent/tinted background; không đổi công thức revenue attribution hoặc financial KPI Sprint 32.1.
- Biểu đồ xu hướng phải giữ đủ điểm dữ liệu cho preset `last_7_days` và `last_30_days`; ngày không phát sinh dữ liệu vẫn hiển thị 0 để tránh hiểu nhầm xu hướng.
- Funnel dashboard dùng hình thang đúng chiều: tầng trên rộng hơn tầng dưới, thu hẹp dần từ Lead/Booking xuống Customer/Hợp đồng.
- Bảng chi tiết top sale/team/project/source chỉ là lớp phụ trợ, hiển thị tối đa top 10 với rank badge và không tạo scroll ngang toàn trang.
