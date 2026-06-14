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
