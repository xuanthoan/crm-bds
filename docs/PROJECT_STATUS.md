# Trạng thái dự án

## 1. Baseline được phân tích

- Commit hiện tại khi lập tài liệu: `554caab`.
- Commit `5015c62` là merge Sprint 11 vào `dev` và nằm trong lịch sử hiện tại.
- Migration mới nhất: `20260613_0010`.
- README ghi nhận các mốc Sprint 1–11 và phần Sprint 12.

## 2. Sprint đã hoàn thành trong lịch sử code

| Sprint | Phạm vi có thể kiểm chứng |
|---|---|
| 1–3 | Auth/RBAC, nền tảng người dùng và Lead |
| 4 | Organization scope: department, team, membership |
| 5 | Lead tasks, appointments, dashboard |
| 6 | Permission matrix và scoped authorization mở rộng |
| 7 | Customer 360 và Lead → Customer conversion |
| 8 | Deal pipeline, Deal detail/timeline |
| 9 | Customer profile nâng cao, related people, scoring |
| 10 | Project và Property inventory |
| 11 | Booking/reservation/deposit |

Các sprint trên có migration/model/service/API/frontend tương ứng và có test file theo sprint.

## 3. Sprint đang làm

Sprint 12 — Deal closing / Contract foundation đang nằm trên commit hiện tại. Code đã có:

- liên kết Deal với Booking, Property và Project;
- tạo Deal từ Booking đã cọc;
- Contract, Contract Payment, Contract Activity;
- contract/payment API và UI cơ bản;
- đồng bộ Contract signed/active sang Deal contracted, pipeline `contract_signed`, Property `sold`;
- contract/payment timeline;
- Deal form liên kết Project/Property inventory;
- searchable combobox cho Project/Property trong Deal form.

Sprint 12 chưa thể coi là một module UI đã hoàn thiện toàn bộ cấu trúc: nhiều component contract được khai báo dưới dạng placeholder một dòng, và test hiện thiên về unit/source assertions hơn là end-to-end database/browser.

## 4. Module hiện có

### Hoạt động

- Authentication, refresh token, RBAC.
- User/role/permission administration.
- Departments, teams, memberships.
- Lead management, activity timeline, assignment.
- Tasks, appointments, personal/team dashboard.
- Customer 360, conversion, related people, scoring.
- Deal pipeline, stage/status, assignment và timeline.
- Project/Property inventory, price/status history.
- Booking/reservation/deposit, refund lifecycle và timeline.
- Contract, contract payments, activities và totals.
- Audit log ở backend.

### Chỉ có nền tảng một phần

- Reports: có route/page và permission vocabulary, nhưng không có reporting backend chuyên biệt được đăng ký.
- Contract frontend: page/form/timeline có code; nhiều component/modal tách riêng vẫn là placeholder.
- Redis: có container/config, chưa có consumer/cache integration trong service code.

## 5. Module chưa có implementation nghiệp vụ

Những nội dung sau không có model + migration + service + API hoàn chỉnh trong code hiện tại:

- Commission calculation/payout.
- KPI engine.
- Invoice và accounting ledger.
- VAT/tax.
- Contract scan/file attachment.
- E-signature.
- Payment gateway.
- Marketing campaign automation/ROI implementation.
- Workflow automation engine.
- Notification/background job system.
- Revenue/finance dashboard nâng cao.

Một số permission code cho marketing, commissions, generic payments và reports có tồn tại; đó không phải bằng chứng module đã được triển khai.

## 6. Chất lượng và khả năng vận hành

- Backend có 16 test modules `unittest`, phủ permissions và validation theo Sprint 6–12 cùng một số timeline/scoring cases.
- Frontend không khai báo test script; kiểm tra tự động khả dụng là TypeScript/Vite production build.
- Docker Compose cung cấp stack local đầy đủ.
- README chứa hướng dẫn chạy, test và lịch sử sprint.
- Không thấy cấu hình CI trong repository ở thời điểm lập tài liệu.

## 7. Việc tiếp theo được chứng minh bởi code/TODO

- Thay code generation dạng scan-max bằng database sequence.
- Bổ sung integration tests dùng PostgreSQL và API client.
- Bổ sung frontend component/tests cho Contract.
- Hoàn thiện reporting thay cho page nền.
- Sprint kế tiếp theo README/Sprint 12 notes được gợi ý là Commission/KPI, nhưng chưa có implementation.
