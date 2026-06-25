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
