# Known issues và technical debt

Danh sách chỉ gồm các điểm quan sát trực tiếp từ code/repository.

## 1. Chất lượng và kiểm thử

- Frontend không có test runner hoặc script `test`; chỉ có `dev`, `build`, `preview`.
- Nhiều test Sprint 10–12 kiểm tra chuỗi/source structure bên cạnh validation unit; chưa thay thế được integration test với PostgreSQL thật.
- Không thấy browser/E2E suite.
- Không thấy cấu hình CI trong repository.
- Docker smoke test không được tự động hóa trong test suite.

## 2. Contract frontend chưa tách hoàn chỉnh

Các file sau hiện chỉ là placeholder một dòng:

- `ContractActivityForm.tsx`
- `ContractPaymentModal.tsx`
- `ContractStatusModal.tsx`
- `ContractBadge.tsx`
- `ContractFilters.tsx`
- `ContractPaymentTable.tsx`
- `ContractSummaryCard.tsx`
- `ContractTable.tsx`

Chức năng đang được viết trực tiếp trong page/form chính, làm cấu trúc feature không đồng nhất với tên file đã tạo.

## 3. Code generation có race condition tiềm tàng

Lead/Customer/Deal/Project/Property/Booking/Contract/Payment code được sinh bằng cách đọc mã hiện có và lấy số lớn nhất + 1. Nhiều service có TODO chuyển sang database sequence. Cách hiện tại không đảm bảo an toàn khi nhiều transaction tạo đồng thời.

## 4. Deal close status chưa thống nhất

- Manual pipeline `completed` đặt Deal status `won`.
- Contract `completed` đặt Deal status `completed`.

Cả hai status tồn tại trong constants. Reporting/logic tương lai phải xử lý cả hai cho đến khi lifecycle được chuẩn hóa.

## 5. Contract/payment limitations được thể hiện trong code

- Không tự complete Deal khi tổng paid đạt contract value.
- Không tự refund Booking khi Deal/Contract hủy.
- Contract cancellation không tự trả Property sold về available.
- Không có invoice, VAT/tax, accounting ledger, e-signature, payment gateway hoặc contract file upload.
- `remaining_value` lưu lúc tạo Contract nhưng response remaining được tính lại từ payments; hai biểu diễn có thể cần chiến lược đồng bộ rõ hơn.

## 6. Hạ tầng chưa sử dụng hết

- Redis có trong Compose/config nhưng không có service integration được tìm thấy.
- Không có worker/scheduler cho overdue booking/payment, notification hay automation.

## 7. Permission vocabulary vượt quá implementation

Permission codes cho marketing, commissions, generic payments và reports tồn tại. Không có đầy đủ migration/model/service/API tương ứng cho các module này. UI/authorization không nên suy ra capability chỉ từ sự tồn tại của permission code.

## 8. Reports

Route `/reports` và permission liên quan tồn tại, nhưng không có reporting API/module chuyên biệt tương ứng trong router backend hiện tại. Đây chưa phải advanced reporting/revenue dashboard.

## 9. Tài liệu cũ

Một số tài liệu cũ trong `docs/` mô tả kiến trúc/roadmap mục tiêu và có thể không phản ánh code đã triển khai. Bộ tài liệu trạng thái hiện tại nên được ưu tiên khi bàn giao, còn các tài liệu PRD/plan cũ chỉ dùng làm lịch sử ý tưởng.

## 10. Điểm chưa xác minh bằng manual environment trong lần lập tài liệu

- Không chạy browser manual flow.
- Không xác minh dữ liệu production.
- Không kiểm tra migration upgrade/downgrade trên database có dữ liệu thật.
- Không đánh giá tải/concurrency.
