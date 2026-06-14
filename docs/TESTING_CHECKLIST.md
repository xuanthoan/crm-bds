# Testing checklist

## 1. Static và build checks

```bash
python -m compileall backend/app backend/alembic backend/tests
cd frontend && npm run build
git diff --check
git diff --cached --check
```

## 2. Backend test suites hiện có

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

## 3. Docker smoke test

```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
docker compose logs --no-color backend
docker compose down
```

Kiểm tra backend log xác nhận `alembic upgrade head` thành công.

## 4. Manual regression checklist

### Auth/RBAC/organization

- [ ] Login, refresh, logout.
- [ ] User bị vô hiệu hóa không đăng nhập được.
- [ ] Route/menu bị ẩn theo permission.
- [ ] Backend trả 403 khi gọi trực tiếp API ngoài scope.
- [ ] Department/team membership ảnh hưởng đúng own/team/department.

### Lead/Customer

- [ ] Tạo Lead và chặn phone trùng.
- [ ] Gán owner, thêm activity/task/appointment.
- [ ] Chuyển Lead thành Customer.
- [ ] Chặn conversion lần hai.
- [ ] Customer detail hiển thị profile/related people/scoring.

### Deal/Inventory

- [ ] Tạo Project và Property có/không có Project.
- [ ] Deal form tìm Project/Property thực.
- [ ] Chọn Property tự điền project/code/type/area/listed price.
- [ ] Chặn Property sold/deleted và project mismatch.
- [ ] Existing Deal liên kết Property sold vẫn mở/edit an toàn.
- [ ] Đổi Deal stage/status và kiểm tra timeline.

### Booking

- [ ] Tạo Booking draft trên Property available.
- [ ] Chặn booking active thứ hai cho cùng Property.
- [ ] Reserved yêu cầu amount hợp lệ và Property -> reserved.
- [ ] Deposited yêu cầu deposit amount và Property -> deposited.
- [ ] Cancel/refund yêu cầu lý do/số tiền.
- [ ] Soft delete chỉ cho final Booking status.
- [ ] Tạo Deal từ Booking deposited.
- [ ] Chặn tạo Deal từ trạng thái khác và chặn duplicate active Deal.

### Contract/Payment

- [ ] Tạo Contract từ Deal; liên kết Booking/Customer/Property/Project đúng.
- [ ] Chặn Deal lost/cancelled, Deal không Property và duplicate active Contract.
- [ ] Signed/active -> Deal contracted + `contract_signed`, Property sold.
- [ ] Contract/Deal/Property timeline/history có nội dung tiếng Việt.
- [ ] Tạo planned payment và xác nhận paid.
- [ ] `total_paid`, `total_planned`, `remaining_amount` đúng.
- [ ] Payment timeline format tiền/metadata đúng.
- [ ] Chặn xóa Contract signed/active/completed.
- [ ] Cho soft delete Contract draft/cancelled.
- [ ] Payment đủ không tự complete Deal.

## 5. Database checks

- [ ] Upgrade database mới từ base đến `20260613_0010`.
- [ ] Kiểm tra đủ 28 bảng.
- [ ] Kiểm tra FK và partial unique booking index.
- [ ] Kiểm tra soft-delete records không xuất hiện trong list/detail.
- [ ] Kiểm tra concurrent code generation trước khi triển khai tải cao.

## 6. Những gì checklist hiện chưa tự động hóa

- Browser E2E.
- Accessibility.
- Load/concurrency.
- Migration trên bản sao dữ liệu production.
- Security penetration test.
- Backup/restore và disaster recovery.
