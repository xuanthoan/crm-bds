# Workflows hiện có

## 1. Luồng end-to-end

Code hỗ trợ chuỗi mục tiêu:

```text
Lead
  -> Customer
  -> Deal
  -> Booking
  -> Contract
  -> Closed Won
```

Đồng thời Sprint 12 bổ sung một nhánh thực tế:

```text
Customer + Property
  -> Booking deposited
  -> tạo Deal liên kết Booking
  -> Contract
```

Hai nhánh cùng tồn tại vì Booking có `source_deal_id` tùy chọn, còn Deal có `booking_id` tùy chọn.

## 2. Lead → Customer

1. Người dùng tạo Lead với phone chính và dữ liệu nhu cầu.
2. Lead được gán owner và có activity/task/appointment.
3. Actor có `leads.convert.<scope>` gọi conversion.
4. Service kiểm tra Lead chưa được chuyển đổi.
5. Customer được tạo, dùng dữ liệu nguồn từ Lead.
6. `leads.converted_customer_id`, `converted_at`, `converted_by_id` được cập nhật.
7. Lead status trở thành `converted`.
8. Customer/Lead activity và audit được ghi.

Kết quả: một Lead chỉ chuyển thành Customer một lần.

## 3. Customer → Deal

1. Actor có `deals.create` chọn Customer và owner.
2. Có thể chọn Project/Property thực từ inventory.
3. Nếu chọn Property, backend dẫn xuất property code/type/area/project và giá niêm yết làm expected value khi chưa nhập.
4. Deal bắt đầu với stage/status theo payload/default schema.
5. Deal activity “Tạo giao dịch” và audit log được ghi.
6. Deal có thể đổi stage, status, owner và thêm activity.

## 4. Deal → Booking

1. Booking create nhận Customer, Property, assigned user và `source_deal_id` tùy chọn.
2. Property phải phù hợp để booking và không có booking active xung đột.
3. Booking bắt đầu `draft`.
4. Khi `reserved`, Property chuyển `reserved`.
5. Khi `deposited`, Property chuyển `deposited`.
6. Booking giữ liên kết nguồn Deal/Lead nếu được cung cấp.

Đây là đường Deal trước Booking.

## 5. Booking → Deal

1. Booking phải tồn tại, chưa xóa và status `deposited`.
2. Customer và Property liên quan phải tồn tại/chưa xóa.
3. Không được có active Deal khác cho cùng Booking.
4. Không được có active closing Deal khác cho cùng Property.
5. Service tạo Deal với:
   - Customer từ Booking;
   - Booking ID;
   - Property ID và Project ID;
   - source Lead;
   - owner là assigned user;
   - status `contract_pending`;
   - expected value từ payload, listed price hoặc deposit amount.
6. Deal activity, Booking activity và audit được ghi.
7. Booking vẫn `deposited`; không tự xóa hay refund.

## 6. Deal → Contract

1. Actor mở Contract create từ Deal detail hoặc Contract list.
2. Backend luôn nhận `deal_id` và tự dẫn xuất Booking/Customer/Property/Project.
3. Deal phải tồn tại, chưa xóa, không `lost`/`cancelled`, và phải có Property.
4. Không được có active Contract khác cho Deal.
5. Contract code được sinh dạng `HD-000001`.
6. Contract activity “Tạo hợp đồng” và audit được ghi.
7. Contract mặc định là `draft`, loại mặc định `deposit_contract`.

## 7. Contract lifecycle và Deal/Property

### `draft` / `pending_signature`

- Chưa tự bán Property.
- Contract `draft` có thể soft delete.

### `signed` hoặc `active`

- Deal status -> `contracted`.
- Deal pipeline stage -> `contract_signed`.
- Deal contract date được đặt nếu chưa có.
- Property inventory -> `sold`.
- Property status history được ghi.
- Contract activity và Deal activity tiếng Việt được ghi.
- Deal chưa được tự coi là hoàn tất.

### `completed`

- Deal status -> `completed`.
- Deal pipeline stage -> `completed`.
- `closed_at` được đặt.
- Property vẫn/được đặt `sold`.

### `cancelled`

- Deal activity “Hợp đồng đã hủy” được ghi.
- Code không tự hoàn tiền Booking.
- Code không tự đưa Property đã sold về available khi chỉ hủy Contract.

## 8. Contract Payment

1. Actor có quyền tạo payment tạo khoản `planned` (default).
2. Payment liên kết Contract, Deal, Customer và Property.
3. Contract activity lưu metadata có cấu trúc: code, amount, type/status label.
4. Xác nhận payment:
   - status -> `paid`;
   - `paid_date` mặc định thời điểm hiện tại;
   - cập nhật method/reference/note nếu có;
   - ghi timeline và audit.
5. Contract response tính:
   - `total_paid`: tổng payment `paid`;
   - `total_planned`: tổng `planned` + `overdue`;
   - `remaining_amount`: `max(contract_value - total_paid, 0)`.
6. Thanh toán đủ không tự hoàn tất Deal.

## 9. Closed Won

Có hai cơ chế đóng Deal trong code:

- Stage đổi sang `completed` làm status `won`, đặt `closed_at`, ghi “Chốt thành công”.
- Contract status `completed` đặt Deal status `completed`, stage `completed`, đặt `closed_at`.

Do đó enum hiện tại giữ cả `won` và `completed` trong Deal status. Đây là hành vi thực tế cần được cân nhắc khi chuẩn hóa lifecycle sau này.
