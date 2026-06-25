# Workflows hiện có

## 1. Luồng end-to-end hiện hành

Luồng nghiệp vụ chính sau Sprint 15:

```text
Lead
  -> Customer
  -> Booking reserved/deposited
  -> Deal deposited/contract_pending
  -> Contract draft/signed/active
  -> Payment planned/paid/overdue/cancelled
  -> Contract completed
  -> Deal completed/won
```

Các biến thể hợp lệ vẫn tồn tại:

- Customer có thể tạo Deal trực tiếp nếu Property còn `available`.
- Booking có thể được tạo từ Deal nguồn (`source_deal_id`) hoặc Deal có thể được tạo từ Booking đã cọc (`booking_id`).
- Contract luôn tạo từ Deal và tự dẫn xuất Booking / Customer / Property / Project từ Deal.

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

## 3. Customer → Deal trực tiếp

1. Actor có `deals.create` chọn Customer và owner.
2. Có thể chọn Project/Property thực từ inventory.
3. Nếu chọn Property, backend dẫn xuất property code/type/area/project và giá niêm yết làm expected value khi chưa nhập.
4. Tạo Deal trực tiếp chỉ cho Property khả dụng (`available`).
5. Deal bắt đầu với stage/status theo payload/default schema.
6. Deal activity “Tạo giao dịch”, notification giao Deal và audit log được ghi.
7. Deal có thể đổi stage, status, owner và thêm activity nếu không bị Contract guard khóa.

## 4. Deal → Booking

1. Booking create nhận Customer, Property, assigned user và `source_deal_id` tùy chọn.
2. Property phải phù hợp để booking và không có booking active xung đột.
3. Booking bắt đầu `draft`.
4. Khi `reserved`, Property chuyển `reserved`.
5. Khi `deposited`, Property chuyển `deposited` và có thể tạo Deal liên kết Booking.
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
   - stage/status theo logic deposited hoặc contract pending;
   - expected value từ payload, listed price hoặc deposit amount.
6. Deal activity, Booking activity, notification/auto task liên quan và audit được ghi.
7. Booking vẫn `deposited`; không tự xóa hay refund.

## 6. Deal stage/status workflow

Stage pipeline chính:

```text
new -> consulting -> reserved -> deposited -> contract_pending -> contract_signed -> completed
                                                        └────────────── lost
```

Status xử lý/kết quả chính:

```text
open -> pending/negotiating -> contract_pending/payment_in_progress -> contracted/completed/won
                                                                     └ lost/cancelled
```

Business guard:

- Deal có Contract `signed`/`active` không được chuyển lost/cancelled hoặc downgrade về stage không hợp lệ.
- Deal có Contract `completed` chỉ được giữ stage `completed` và status `completed`/`won`.
- Deal lost/cancelled thủ công bắt buộc lý do.
- Cancelled Contract không khóa Deal và cho phép xử lý/tạo Contract mới nếu không còn Contract active.

## 7. Deal → Contract

1. Actor mở Contract create từ Deal detail hoặc Contract list.
2. Backend luôn nhận `deal_id` và tự dẫn xuất Booking/Customer/Property/Project.
3. Deal phải tồn tại, chưa xóa, không `lost`/`cancelled`, và phải có Property.
4. Không được có active Contract khác cho Deal.
5. Contract code được sinh dạng `HD-000001`.
6. Contract activity “Tạo hợp đồng”, Deal activity liên kết Contract và audit được ghi.
7. Contract mặc định là `draft`, loại mặc định `deposit_contract`.

## 8. Contract lifecycle và Deal/Property

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
- Deal timeline ghi rõ Contract hoàn tất nên Deal được chốt thành công.

### `cancelled`

- Contract cancelled là terminal; không được ký/kích hoạt lại.
- Deal activity “Hợp đồng đã hủy” được ghi.
- Nếu không còn Contract hiệu lực khác, Deal/Property rollback theo Booking cọc còn hiệu lực hoặc trả Property về available khi đủ điều kiện.
- Code không tự hoàn tiền Booking.

## 9. Contract Payment

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
   - `remaining_amount`: `max(contract_value - deposit - total_paid, 0)`.
6. Thanh toán đủ chưa tự hoàn tất Deal; Sprint 16 Payment Management sẽ tiếp tục làm rõ quy trình này.

## 10. Task & Notification workflow

- Booking tạo/đặt cọc sinh task follow-up/chuẩn bị hợp đồng; Booking cancel/refund/expire auto cancel task liên quan.
- Deal vào `consulting`, `deposited/deposit`, `contract_pending/contract` tạo auto task gán cho owner nếu chưa có task active trùng.
- Deal đổi owner sẽ chuyển active auto task liên quan sang owner mới; task done/cancelled không bị reopen hoặc đổi assignee.
- Contract còn tiền phải thu tạo task theo dõi thanh toán; Contract completed auto complete payment follow-up task.
- Notification in-app được tạo cho assignee/owner liên quan task và Deal event quan trọng. Không realtime/websocket/email/SMS/Zalo.

## 11. Completed / Won

Có hai biểu diễn kết quả thành công hiện đang cùng tồn tại:

- Manual pipeline stage `completed` đặt Deal status `won`, đặt `closed_at`, ghi “Chốt thành công”.
- Contract status `completed` đặt Deal status `completed`, stage `completed`, đặt `closed_at`.

Do đó reporting/logic tương lai phải xem `completed` và `won` là kết quả thành công cho đến khi lifecycle được chuẩn hóa sâu hơn.
