# Testing checklist

## 1. Static và build checks

```bash
python -m compileall backend/app backend/alembic backend/tests
cd frontend && npm run build
git diff --check
git diff --cached --check
```

## 2. Backend regression suites

```bash
PYTHONPATH=backend python -m unittest backend.tests.test_sprint6_permissions -v
PYTHONPATH=backend python -m unittest backend.tests.test_sprint7_permissions backend.tests.test_sprint7_customer_validation -v
PYTHONPATH=backend python -m unittest backend.tests.test_sprint8_deal_permissions backend.tests.test_sprint8_deal_validation -v
PYTHONPATH=backend python -m unittest backend.tests.test_sprint9_customer_profile_validation backend.tests.test_sprint9_customer_scoring -v
PYTHONPATH=backend python -m unittest backend.tests.test_sprint10_inventory_permissions backend.tests.test_sprint10_inventory_validation backend.tests.test_sprint10_project_delete_protection -v
PYTHONPATH=backend python -m unittest backend.tests.test_sprint11_booking_permissions backend.tests.test_sprint11_booking_validation -v
PYTHONPATH=backend python -m unittest backend.tests.test_sprint12_contract_permissions backend.tests.test_sprint12_contract_validation -v
PYTHONPATH=backend python -m unittest backend.tests.test_lead_assignment_timeline backend.tests.test_role_code_sets -v
```

Focused Sprint 12 handoff suite:

```bash
PYTHONPATH=backend python -m unittest backend.tests.test_sprint11_booking_validation backend.tests.test_sprint8_deal_validation backend.tests.test_sprint12_contract_validation -v
```

## 3. Docker smoke test

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
docker compose logs --no-color backend
docker compose down
```

Kiểm tra backend log xác nhận `alembic upgrade head` thành công và migration `20260613_0010_deal_closing_contracts.py` đã chạy.

## 4. Sprint 12 passed regression checklist

### Booking → Deal → Contract

- [ ] Tạo Lead.
- [ ] Chuyển Lead thành Customer.
- [ ] Tạo Project và Property `available`.
- [ ] Tạo Booking cho Customer + Property.
- [ ] Chuyển Booking sang `deposited`.
- [ ] Tạo Deal từ Booking deposited.
- [ ] Deal Detail hiển thị Booking / Property / Project.
- [ ] Tạo Contract từ Deal.
- [ ] Contract lấy đúng Deal / Booking / Customer / Property / Project / Contract Value.

### Contract signed → Deal contracted → Property sold

- [ ] Chuyển Contract từ draft sang signed.
- [ ] Contract Detail hiển thị `Đã ký`.
- [ ] Deal chuyển sang trạng thái/giai đoạn đã ký hợp đồng.
- [ ] Property chuyển sang `sold` / `Đã bán`.
- [ ] Contract timeline ghi status change tiếng Việt.
- [ ] Deal timeline ghi hoạt động Contract signed tiếng Việt.
- [ ] Property status history ghi chuyển trạng thái sang sold.

### Contract cancelled rollback

- [ ] Contract signed có Booking deposited liên quan: cancel Contract.
- [ ] Contract chuyển `cancelled`.
- [ ] Deal không còn giữ stage/status đã ký hợp đồng.
- [ ] Property quay về `deposited` nếu Booking cọc vẫn còn hiệu lực.
- [ ] Contract cancelled không được chuyển lại signed/active/completed.
- [ ] Contract cancelled không chặn flow mới nếu Property đã available và không còn holder khác.

### Booking guard khi có Contract hiệu lực

- [ ] Booking → Deal → Contract signed.
- [ ] Thử cancel Booking: bị chặn.
- [ ] Thử refund Booking: bị chặn.
- [ ] Thử expire Booking: bị chặn.
- [ ] Thử delete Booking: bị chặn.
- [ ] Property vẫn sold, Deal vẫn contracted, Contract vẫn signed sau thao tác bị chặn.

### Booking refund/deduction

- [ ] Booking deposited không có Contract hiệu lực: refund amount = booking/deposit amount.
- [ ] Deduction hiển thị `0`.
- [ ] Booking deposited không có Contract hiệu lực: refund amount < booking/deposit amount.
- [ ] Deduction tự tính đúng.
- [ ] Deduction reason optional.
- [ ] Refund amount > booking/deposit amount bị chặn.
- [ ] Booking Detail hiển thị booking amount, refund amount, deduction amount, refund reason, deduction reason.
- [ ] Booking timeline hiển thị `Số tiền hoàn`, `Khấu trừ`, `Lý do hoàn tiền`, `Lý do khấu trừ`.

### Property release sau Booking cancel/refund/expire

- [ ] Booking deposited chưa có Contract effective → cancelled: Property về available nếu không còn holder khác.
- [ ] Booking deposited chưa có Contract effective → refunded: Property về available nếu không còn holder khác.
- [ ] Booking deposited chưa có Contract effective → expired: Property về available nếu không còn holder khác.
- [ ] Deal tạo từ Booking bị release không còn chặn Booking/Deal mới.
- [ ] Unrelated active Deal trên cùng Property vẫn chặn release/new flow.

### Direct Deal chỉ cho Property available

- [ ] Property available có thể chọn để tạo Deal trực tiếp.
- [ ] Property reserved/deposited/sold không selectable hoặc bị backend chặn.
- [ ] Property deleted không selectable và bị backend chặn.
- [ ] Booking → Deal từ Booking deposited vẫn hoạt động vì đó là holder hợp lệ.

### Contract Payment

- [ ] Tạo planned payment.
- [ ] Confirm payment với method/reference/paid date.
- [ ] Contract total paid chỉ tính payment paid.
- [ ] Remaining amount = contract value - deposit - total paid.
- [ ] Payment vượt remaining bị chặn.
- [ ] Payment timeline hiển thị tiền VND và metadata theo từng dòng.

## 5. Known remaining UI polish checks

- [ ] Contract form/modal spacing ổn ở màn nhỏ.
- [ ] Contract payment modal labels không overlap.
- [ ] Booking refund modal hiển thị deduction dễ hiểu trên mobile.
- [ ] Empty states ở Contract/Payment/Timeline thống nhất.
- [ ] Frontend chưa có automated browser E2E; cần manual hoặc Playwright/Cypress trước production.

## 6. Những gì checklist hiện chưa tự động hóa

- Browser E2E.
- Accessibility.
- Load/concurrency.
- Migration trên bản sao dữ liệu production.
- Security penetration test.
- Backup/restore và disaster recovery.

## Sprint 13 UI regression checklist

- [ ] Booking có effective Contract hiển thị lock banner và không cho đổi trạng thái/xóa.
- [ ] Booking status modal hiển thị lỗi API trong modal, refund tự tính tiền khấu trừ.
- [ ] Deal detail không hiển thị raw contract status; hợp đồng hủy hiện badge Đã hủy.
- [ ] Contract cancelled hiển thị terminal banner và disable thao tác ký/kích hoạt/thanh toán.
- [ ] Payment modal có đủ method/reference/paid date/note và lỗi validation rõ ràng.
- [ ] Property related deal/contract hiển thị trạng thái tiếng Việt, không raw enum.

## Sprint 14 — Task & Notification Engine
- Run `python -m compileall backend/app backend/tests`.
- Run `PYTHONPATH=backend python -m unittest backend.tests.test_sprint14_task_notification -v`.
- Run Sprint 11/12 booking-contract validation tests when dependencies are available.
- Run `cd frontend && npm run build`.
- Run `git diff --check` and `git diff --cached --check` before delivery.

## Sprint 15 — Professional Deal Workflow completed checklist

### Required automated checks

```bash
python -m compileall backend/app backend/tests
PYTHONPATH=backend python -m unittest backend.tests.test_sprint8_deal_validation backend.tests.test_sprint12_contract_validation backend.tests.test_sprint14_task_notification backend.tests.test_sprint15_deal_workflow -v
cd frontend && npm run build
git diff --check
git diff --cached --check
```

### Manual QA — passed before approval

#### A. Deal workflow basic

- [x] Tạo Booking.
- [x] Đặt cọc Booking.
- [x] Tạo Deal từ Booking.
- [x] Chuyển Deal qua các stage hợp lệ.
- [x] Kiểm tra timeline Deal hiển thị tiếng Việt và mới nhất/nhất quán theo UI hiện có.

#### B. Contract lock

- [x] Tạo Contract từ Deal.
- [x] Chuyển Contract sang Đã ký hoặc Có hiệu lực.
- [x] Thử hủy/thất bại Deal.
- [x] Kỳ vọng bị chặn với thông báo tiếng Việt: không thể hủy/thất bại vì đang có hợp đồng hiệu lực.

#### C. Completed contract

- [x] Chuyển Contract Hoàn tất.
- [x] Deal auto Hoàn tất/Thành công theo logic hiện hành.
- [x] Thử chuyển Deal khỏi hoàn tất.
- [x] Kỳ vọng backend chặn direct API mutation không hợp lệ.

#### D. Cancelled contract

- [x] Tạo Contract.
- [x] Hủy Contract.
- [x] Deal không bị khóa nếu chỉ còn cancelled Contract.
- [x] Có thể tạo Contract mới khi các điều kiện nghiệp vụ khác hợp lệ.

#### E. Deal auto task

- [x] Chuyển Deal sang `consulting` / `contract_pending` / `deposited`.
- [x] Kiểm tra `/tasks` có task liên quan Deal.
- [x] Cột Liên kết ưu tiên hiển thị Deal `DL-xxxxx` khi task linked trực tiếp tới Deal.
- [x] Không tạo trùng active auto task khi thao tác lại.

#### F. Deal reassignment

- [x] Deal có active auto task.
- [x] Đổi người phụ trách Deal.
- [x] Active auto task đổi assignee theo owner mới.
- [x] Task done/cancelled không đổi assignee và không bị reopen.

#### G. Notification

- [x] Đổi assignee Deal hoặc tạo Deal auto task.
- [x] User nhận có notification in-app.
- [x] Header unread badge đúng.
- [x] `/notifications` không lỗi.

#### H. Search

- [x] Search `deal_code`.
- [x] Search `booking_code`.
- [x] Search `contract_code`.
- [x] Search customer phone.
- [x] Search `property_code`.
- [x] Không lỗi 500 và không tái diễn TooManyColumns.

### Sprint 15 regression expectations

- [x] Deal có Contract `signed`/`active` không thể lost/cancelled.
- [x] Deal có Contract `completed` không thể chuyển khỏi completed/won.
- [x] Cancelled Contract không khóa Deal.
- [x] Contract completed auto chuyển Deal completed/won và ghi timeline tiếng Việt.
- [x] Deal lost/cancelled bắt buộc reason.
- [x] Deal stage/status timeline dùng label tiếng Việt.
- [x] Deal auto task không trùng.
- [x] Deal đổi assignee thì active auto task đổi assignee.
- [x] Task done/cancelled không bị đổi assignee.
- [x] Deal search/list dùng query narrow, không joinedload rộng object graph.

## Sprint 16 — Payment Management checklist

### Automated checks

```bash
python -m compileall backend/app backend/tests
PYTHONPATH=backend python -m unittest backend.tests.test_sprint12_contract_validation backend.tests.test_sprint14_task_notification backend.tests.test_sprint15_deal_workflow backend.tests.test_sprint16_payment_management -v
cd frontend && npm run build
git diff --check
git diff --cached --check
```

### Manual browser checklist

- Contract detail: mở Contract còn hiệu lực, tạo 3 đợt thanh toán và kiểm tra section Thanh toán.
- Payment list: search contract code/customer phone, filter pending/partial/paid/overdue.
- Receipt: ghi nhận một phần, ghi nhận phần còn lại, thử thanh toán vượt và kỳ vọng bị chặn.
- Penalty: áp dụng phí phạt có lý do, thử phí phạt âm/không lý do và kỳ vọng bị chặn.
- Overdue: tạo due date quá khứ và kiểm tra badge Quá hạn.
- Contract cancelled: thử tạo payment schedule và kỳ vọng bị chặn.
- Notification/task: kiểm tra task/notification đến hạn/quá hạn không bị tạo trùng.
- Regression: Deal completed từ Contract completed, Deal/Contract/Task/Notification Sprint 15 vẫn hoạt động.

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

### Sprint 18 finance report guide modal QA

- Admin vào `/reports/finance` và thấy nút “Hướng dẫn sử dụng” trên header Báo cáo tài chính.
- Bấm “Hướng dẫn sử dụng” mở modal nội bộ, không dùng alert/prompt mặc định của browser.
- Modal “Hướng dẫn sử dụng Báo cáo tài chính” hiển thị đầy đủ mục đích màn hình, ý nghĩa KPI, ý nghĩa từng tab, bộ lọc, Xuất CSV và lưu ý nghiệp vụ.
- Nội dung modal dài có thể scroll trong modal; bấm “Đóng” hoặc icon X đóng modal.
- Các tab báo cáo, link detail UUID và export CSV Sprint 18 vẫn hoạt động như trước.
- User không có `reports.view.finance` vẫn bị chặn như trước và không vào được nội dung báo cáo.

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

## Sprint 22 QA checklist

- Tạo COM không có CCR vẫn thành công, nhưng approve/mark-paid bị chặn với lý do rõ.
- CCR `pending`/`approved` cho approve COM nhưng chưa cho mark paid khi `received_amount = 0`.
- CCR `partially_received`/`received` cho mark paid trong phạm vi `received_amount` còn lại và không vượt approved amount.
- CCR `on_hold`/`cancelled` chặn approve và mark paid COM.
- `/commissions` list và detail hiển thị HH công ty, số đã nhận, số còn phải thu, khả năng duyệt/chi và reason bị chặn.

### Sprint 22 regression quick checks
- `/contracts`: verify pagination shows total contracts and Trang trước/Trang sau so older HD records can be opened after seeded data pushes them past page 1.
- `/payments/:id`: verify a payment with any non-cancelled invoice cannot create another draft invoice; backend message: “Đợt thanh toán này đã có hóa đơn, không thể tạo thêm hóa đơn nháp.”
- `/company-commissions/:id` and `/commissions/:id`: verify statuses, payer types, contract status, and timeline events show Vietnamese labels instead of raw enum values.
- Partial COM payout: pay part of approved COM, receive more CCR, confirm COM stays “Đã chi một phần” until user explicitly marks the remaining sale payout as paid.

## Sprint 23 — Commission Payout Policy Configuration

- Kiểm tra cấu hình toàn hệ thống tại **Cài đặt chính sách chi hoa hồng sale**.
- Policy 1 — **Chi theo hạn mức tiền hoa hồng công ty đã nhận** (`received_amount_capacity`):
  - Tạo/chuẩn bị CCR xác nhận 600đ, CCR đã nhận 200đ, COM đã duyệt 60đ, COM đã chi 0đ.
  - Mở `/commissions` hoặc `/commissions/:id` và xác nhận tối đa có thể chi lần này là 60đ.
- Policy 2 — **Chi theo tỷ lệ hoa hồng công ty đã thu** (`received_ratio`):
  - Chuyển cấu hình sang policy tỷ lệ.
  - Với CCR xác nhận 600đ, CCR đã nhận 200đ, COM đã duyệt 60đ, COM đã chi 0đ, xác nhận tỷ lệ đã thu là 33,33% và tối đa có thể chi lần này là 20đ.
- Modal **Đã chi trả** phải tự điền số tiền bằng tối đa có thể chi theo policy hiện tại và backend phải chặn khi nhập vượt số này.
- Ghi nhận CCR receipt chỉ tăng capacity/tỷ lệ đã thu; không tự động tăng `COM.paid_amount`.
