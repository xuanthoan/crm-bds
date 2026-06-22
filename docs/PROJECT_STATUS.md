# Trạng thái dự án

## 1. Baseline tài liệu

- Baseline trước lần cập nhật tài liệu này: commit `0d5b425` trên nhánh làm việc Sprint 12.
- Migration mới nhất trong code: `20260613_0010_deal_closing_contracts.py`.
- Tài liệu này chỉ phản ánh code hiện có trong repository, không mô tả roadmap chưa triển khai.
- Không có migration mới cho cập nhật tài liệu này.

## 2. Sprint đã hoàn thành

| Sprint | Trạng thái | Phạm vi đã có trong code |
|---|---:|---|
| 1–3 | Hoàn thành | Auth/RBAC nền tảng, user/role/permission, Lead nền tảng |
| 4 | Hoàn thành | Department, team, membership và organization scope |
| 5 | Hoàn thành | Lead tasks, appointments, dashboard |
| 6 | Hoàn thành | Permission matrix và scoped authorization mở rộng |
| 7 | Hoàn thành | Customer 360 và Lead → Customer conversion |
| 8 | Hoàn thành | Deal pipeline, Deal detail/timeline |
| 9 | Hoàn thành | Customer profile nâng cao, related people, scoring |
| 10 | Hoàn thành | Project và Property inventory |
| 11 | Hoàn thành | Booking/reservation/deposit/refund lifecycle |
| 12 | Passed trong branch Sprint 12 | Booking → Deal → Contract foundation, Contract Payment, guard và rollback nghiệp vụ |

## 3. Sprint 12 — trạng thái hiện tại

Sprint 12 hiện được xem là **passed trên branch Sprint 12** theo các regression/validation đã bổ sung trong codebase.

Các hành vi chính đã có:

- Booking đã cọc có thể tạo Deal qua luồng Booking → Deal.
- Deal từ Booking giữ liên kết Booking / Customer / Property / Project.
- Deal có thể tạo Contract và Contract lấy dữ liệu liên kết từ Deal.
- Contract signed/active chuyển Deal sang trạng thái/giai đoạn đã ký hợp đồng và chuyển Property sang sold.
- Contract cancelled rollback Deal/Property theo trạng thái giữ chỗ/cọc còn hiệu lực hoặc trả Property về available khi đủ điều kiện.
- Booking có Contract hiệu lực (`signed`, `active`, `completed`) bị chặn thao tác status/delete/refund trực tiếp.
- Direct Deal chỉ được tạo trên Property khả dụng (`available`) theo validation backend và lựa chọn frontend.
- Booking cancel/refund/expire khi không có Contract hiệu lực release Property về available nếu không còn Booking/Deal/Contract khác giữ Property.
- Deal được tạo từ Booking sẽ tự bị hủy/đóng khi Booking đó cancel/refund/expire mà không có Contract hiệu lực, để không chặn flow mới.
- Booking refund hỗ trợ refund amount, refund reason, deduction reason và tự tính deduction amount từ booking/deposit amount.
- Contract Payment có payment method/reference/paid date, total paid và remaining amount.

## 4. Module hiện có

### Đang hoạt động

- Authentication, refresh token, RBAC.
- User, role, permission administration.
- Department, team, user organization membership.
- Lead management, assignment, activity timeline.
- Lead tasks, appointments, dashboard.
- Customer 360, conversion, related people, scoring.
- Deal pipeline, assignment, stage/status và timeline.
- Project và Property inventory, price/status history.
- Booking, reservation, deposit, refund và booking timeline.
- Contract, Contract Payment, Contract Activity.
- Booking → Deal → Contract integration.
- Audit log backend.

### Có nền tảng một phần

- Reports: có UI/permission nền, chưa có reporting backend chuyên sâu.
- Contract UI: đã có list/detail/form/status/payment/timeline; một số component vẫn tối giản và cần polish thêm.
- Docker/local stack: có compose và cấu hình local; vẫn cần smoke test đều đặn trên database sạch.

## 5. Module chưa có implementation nghiệp vụ đầy đủ

Các module sau chưa có model + migration + service + API + UI hoàn chỉnh:

- Commission calculation/payout.
- KPI engine.
- Invoice/accounting ledger.
- VAT/tax.
- Contract file attachment/scan/e-signature.
- Payment gateway integration.
- Marketing campaign automation/ROI.
- Workflow automation engine.
- Notification/background job system.
- Finance/revenue dashboard nâng cao.

## 6. Known UI polish còn lại

- Một số màn Contract/Payment đã chạy được nhưng layout và empty-state vẫn nên polish thêm trước production.
- Frontend hiện chủ yếu được kiểm bằng Vite build và source assertions; chưa có browser E2E test.
- Một số component contract phụ còn tối giản, cần chuẩn hóa style/interaction khi Sprint 12 chuyển sang hardening.

## 7. Khuyến nghị tiếp theo

1. Chạy Docker smoke test trên database sạch.
2. Chạy regression thủ công toàn bộ Booking → Deal → Contract → Payment.
3. Bổ sung browser E2E cho Booking refund, Contract signed/cancelled rollback và Payment confirmation.
4. Hardening UI Contract/Payment và Booking refund modal.
5. Trước Sprint kế tiếp, chốt lại enum/status cuối cùng cho Deal completed/won/cancelled.

## Sprint 13 UI/UX polish + workflow hardening

- Booking Detail đã bổ sung header/action rõ hơn, lock banner khi có hợp đồng hiệu lực, money summary, related entities và empty-state tiếng Việt.
- Booking Status modal hiển thị trạng thái hiện tại/trạng thái mới, chặn thao tác khi booking bị khóa bởi hợp đồng hiệu lực hoặc đã final, và hiển thị lỗi API ngay trong modal.
- Deal Detail đã chuẩn hóa tiêu đề liên kết Booking / Bất động sản / Dự án, badge trạng thái booking/contract tiếng Việt và điều kiện hiển thị nút tạo hợp đồng khi chỉ còn hợp đồng đã hủy.
- Contract Detail đã có terminal banner cho hợp đồng đã hủy, disable đổi trạng thái/thêm thanh toán, summary trạng thái thanh toán, bảng payment tiếng Việt và modal status/payment rõ hơn.
- Property Detail related deal/contract hiển thị badge tiếng Việt thay vì raw enum.
- Không thêm migration, dashboard, commission, invoice, reporting, upload hay module nghiệp vụ mới.
