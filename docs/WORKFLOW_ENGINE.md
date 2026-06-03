# WORKFLOW_ENGINE.md

# REAL ESTATE CRM - WORKFLOW ENGINE

Version: 1.0
Status: Draft
Scope: Workflow Engine, Rule Engine, State Machine, SLA, Automation, Notification, Lead Reclaim

---

# 1. MỤC TIÊU

Workflow Engine là bộ máy tự động hóa nghiệp vụ trung tâm của hệ thống CRM bất động sản.

Mục tiêu:

* Tự động hóa các quy trình lặp lại.
* Không bỏ sót lead.
* Không bỏ quên khách hàng.
* Không cho nhảy sai trạng thái.
* Đồng bộ trạng thái giữa khách hàng, giao dịch, kho hàng, thanh toán, hoa hồng.
* Tự động tạo nhiệm vụ chăm sóc.
* Tự động cảnh báo sale/leader/admin.
* Tự động thu hồi lead nếu sale không xử lý.
* Tự động ghi lịch sử thay đổi.
* Tạo nền tảng cho AI Assistant trong giai đoạn sau.

---

# 2. NGUYÊN TẮC THIẾT KẾ

## 2.1. Workflow phải cấu hình được

Không hard-code toàn bộ logic nghiệp vụ.

Các phần cần cấu hình được:

* SLA thời gian xử lý lead
* Quy tắc thu hồi lead
* Quy tắc nhắc việc
* Quy tắc chuyển trạng thái
* Quy tắc tạo nhiệm vụ tự động
* Quy tắc phân bổ lead
* Quy tắc tính điểm khách hàng
* Quy tắc đồng bộ trạng thái

---

## 2.2. Workflow phải có Audit Log

Mọi workflow chạy tự động phải ghi lại:

* Workflow nào chạy
* Trigger là gì
* Entity nào bị tác động
* Điều kiện đúng/sai
* Action đã thực hiện
* Kết quả thành công/thất bại
* Thời gian chạy

---

## 2.3. Workflow không được phá vỡ phân quyền

Ngay cả workflow tự động cũng phải tôn trọng:

* Data ownership
* Team scope
* Permission rule
* State transition rule

---

## 2.4. Workflow phải idempotent

Một workflow không được tạo trùng nhiệm vụ hoặc gửi trùng cảnh báo nếu đã chạy trước đó cho cùng một điều kiện.

Ví dụ:

Lead mới tạo nhiệm vụ gọi điện.

Nếu job retry thì không được tạo 2 nhiệm vụ gọi điện giống nhau.

---

# 3. THÀNH PHẦN CHÍNH

Workflow Engine gồm 7 thành phần:

1. State Machine
2. Rule Engine
3. Trigger Engine
4. Action Engine
5. SLA Engine
6. Notification Engine
7. Workflow Log

---

# 4. STATE MACHINE

State Machine quản lý chuyển trạng thái hợp lệ.

Áp dụng cho:

* Lead
* Customer
* Deal
* Property
* Payment
* Commission
* Activity
* Appointment

---

# 5. CUSTOMER STATE MACHINE

## 5.1. Customer Status

Danh sách trạng thái:

* new
* contacted
* interested
* appointment_scheduled
* site_visited
* negotiating
* deposited
* contracted
* closed_won
* closed_lost
* inactive

---

## 5.2. Luồng chuyển hợp lệ

```text
new
→ contacted
→ interested
→ appointment_scheduled
→ site_visited
→ negotiating
→ deposited
→ contracted
→ closed_won
```

Luồng thất bại:

```text
new/contacted/interested/appointment_scheduled/site_visited/negotiating
→ closed_lost
```

Luồng tạm ngưng:

```text
new/contacted/interested
→ inactive
```

---

## 5.3. Không cho phép

Không cho phép:

```text
new → contracted
new → closed_won
contacted → closed_won
closed_lost → closed_won
closed_won → negotiating
```

Trừ Admin có quyền đặc biệt và phải nhập lý do.

---

# 6. LEAD STATE MACHINE

## 6.1. Lead Status

* new
* assigned
* contacted
* no_answer
* invalid_phone
* duplicated
* qualified
* unqualified
* converted_to_customer
* reclaimed
* closed

---

## 6.2. Luồng hợp lệ

```text
new → assigned → contacted → qualified → converted_to_customer
```

Các luồng khác:

```text
assigned → no_answer
assigned → invalid_phone
new → duplicated
assigned → reclaimed
contacted → unqualified
```

---

## 6.3. Rule bắt buộc

* Lead trùng số điện thoại phải chuyển sang duplicated.
* Lead sai số điện thoại phải chuyển sang invalid_phone.
* Lead đủ điều kiện phải chuyển sang qualified.
* Lead qualified có thể tạo customer hoặc gắn vào customer cũ.

---

# 7. DEAL STATE MACHINE

## 7.1. Deal Stage

Pipeline chuẩn:

1. lead
2. contacted
3. qualified
4. appointment
5. site_visit
6. negotiation
7. booking
8. deposit
9. contract
10. payment
11. closed_won
12. closed_lost

---

## 7.2. Luồng hợp lệ

```text
lead
→ contacted
→ qualified
→ appointment
→ site_visit
→ negotiation
→ booking
→ deposit
→ contract
→ payment
→ closed_won
```

Luồng thất bại:

```text
lead/contacted/qualified/appointment/site_visit/negotiation/booking/deposit/contract
→ closed_lost
```

---

## 7.3. Điều kiện chuyển trạng thái

### Chuyển sang appointment

Bắt buộc có:

* appointment_date
* appointment_type

---

### Chuyển sang site_visit

Bắt buộc có:

* visit_date
* property_id

---

### Chuyển sang negotiation

Bắt buộc có:

* offered_price hoặc expected_price

---

### Chuyển sang booking

Bắt buộc có:

* booking_amount
* booking_date

---

### Chuyển sang deposit

Bắt buộc có:

* deposit_amount
* deposit_date
* property_id
* customer_id

---

### Chuyển sang contract

Bắt buộc có:

* contract_number
* contract_date
* final_price

---

### Chuyển sang payment

Bắt buộc có:

* payment_schedule

---

### Chuyển sang closed_won

Bắt buộc có:

* contract_id
* final_price
* commission_amount hoặc commission_rule_id

---

### Chuyển sang closed_lost

Bắt buộc có:

* lost_reason
* lost_note

---

# 8. PROPERTY STATE MACHINE

## 8.1. Property Status

* available
* reserved
* negotiating
* deposited
* contracted
* sold
* locked
* off_market

---

## 8.2. Luồng hợp lệ

```text
available → reserved → negotiating → deposited → contracted → sold
```

Luồng khác:

```text
available → locked
available → off_market
reserved → available
negotiating → available
deposited → available
```

---

## 8.3. Rule bắt buộc

* Property ở trạng thái sold không được tạo deal mới.
* Property ở trạng thái deposited không được tạo deal deposit khác.
* Property locked không hiển thị cho sale.
* Property off_market không hiển thị trong danh sách bán.

---

# 9. PAYMENT STATE MACHINE

## 9.1. Payment Status

* unpaid
* partial
* paid
* overdue
* cancelled

---

## 9.2. Rule

* Nếu payment_due_date < today và status != paid → overdue.
* Nếu paid_amount = 0 → unpaid.
* Nếu paid_amount > 0 và paid_amount < total_amount → partial.
* Nếu paid_amount >= total_amount → paid.

---

# 10. COMMISSION STATE MACHINE

## 10.1. Commission Status

* not_generated
* pending
* approved
* partially_paid
* paid
* hold
* cancelled

---

## 10.2. Rule

* Deal sang deposit hoặc contract thì tạo commission pending.
* Kế toán/Admin duyệt thì sang approved.
* Thanh toán một phần thì sang partially_paid.
* Thanh toán đủ thì sang paid.
* Deal bị closed_lost thì commission cancelled.

---

# 11. ACTIVITY STATE MACHINE

## 11.1. Activity Status

* pending
* in_progress
* completed
* overdue
* cancelled

---

## 11.2. Rule

* Activity quá hạn mà chưa completed → overdue.
* Activity completed phải có result.
* Activity cancelled phải có cancel_reason.

---

# 12. TRIGGER ENGINE

Trigger là sự kiện làm workflow chạy.

## 12.1. Trigger theo sự kiện

* lead.created
* lead.assigned
* lead.status_changed
* customer.created
* customer.status_changed
* deal.created
* deal.stage_changed
* property.status_changed
* activity.created
* activity.completed
* payment.due
* payment.overdue
* commission.created
* commission.approved
* file.uploaded

---

## 12.2. Trigger theo thời gian

* every_5_minutes
* hourly
* daily_at_08_00
* daily_at_18_00
* weekly_monday_08_00
* monthly_first_day

---

## 12.3. Trigger theo điều kiện

Ví dụ:

* Lead mới chưa gọi sau 15 phút.
* Khách nóng chưa chăm sóc sau 24 giờ.
* Deal deposit chưa có hợp đồng sau 7 ngày.
* Payment quá hạn.
* Sale giữ quá nhiều khách không chăm.

---

# 13. RULE ENGINE

Rule Engine đánh giá điều kiện.

## 13.1. Cấu trúc Rule

Một rule gồm:

* id
* name
* entity_type
* trigger_event
* conditions
* actions
* priority
* is_active

---

## 13.2. Điều kiện

Hỗ trợ:

* equals
* not_equals
* greater_than
* less_than
* greater_or_equal
* less_or_equal
* contains
* not_contains
* is_null
* is_not_null
* in
* not_in
* before
* after
* minutes_since
* hours_since
* days_since

---

## 13.3. Ví dụ Rule JSON

```json
{
  "name": "Auto create call task for new lead",
  "entity_type": "lead",
  "trigger_event": "lead.assigned",
  "conditions": [
    {
      "field": "status",
      "operator": "equals",
      "value": "assigned"
    }
  ],
  "actions": [
    {
      "type": "create_activity",
      "activity_type": "call",
      "due_in_minutes": 15,
      "assigned_to": "{{lead.assigned_user_id}}",
      "title": "Gọi điện cho lead mới"
    }
  ]
}
```

---

# 14. ACTION ENGINE

Action là hành động workflow thực hiện.

## 14.1. Action được hỗ trợ

* create_activity
* create_notification
* send_email
* send_sms
* assign_lead
* reclaim_lead
* update_status
* update_field
* create_audit_log
* create_commission
* update_property_status
* create_payment_schedule
* create_followup_task
* add_tag
* remove_tag
* create_internal_note
* call_webhook

---

## 14.2. create_activity

Tạo nhiệm vụ chăm sóc.

Fields:

* activity_type
* title
* description
* due_at
* assigned_to
* related_entity_type
* related_entity_id

---

## 14.3. create_notification

Tạo thông báo trong hệ thống.

Fields:

* user_id
* title
* message
* notification_type
* priority
* link_url

---

## 14.4. update_status

Đổi trạng thái entity.

Bắt buộc kiểm tra:

* State transition hợp lệ
* Permission
* Required fields

---

## 14.5. reclaim_lead

Thu hồi lead từ sale.

Fields:

* lead_id
* from_user_id
* to_user_id hoặc queue_id
* reason

---

## 14.6. call_webhook

Gọi webhook ra hệ thống ngoài.

Dùng cho:

* n8n
* Zalo
* Email system
* Google Sheet
* BI tools

---

# 15. SLA ENGINE

SLA Engine dùng để kiểm soát thời gian xử lý.

---

## 15.1. SLA Lead mới

Mặc định:

* Lead mới phải được gọi trong 15 phút.
* Nếu sau 15 phút chưa có activity call → cảnh báo sale.
* Nếu sau 30 phút chưa có activity call → cảnh báo leader.
* Nếu sau 60 phút chưa có activity call → cho phép thu hồi lead.

---

## 15.2. SLA Khách nóng

Mặc định:

* Khách Hot phải được chăm sóc trong 24 giờ.
* Khách Super Hot phải được chăm sóc trong 4 giờ.

---

## 15.3. SLA Deal

Mặc định:

* Deal ở booking quá 48 giờ chưa deposit → cảnh báo.
* Deal ở deposit quá 7 ngày chưa contract → cảnh báo.
* Deal ở contract quá 7 ngày chưa payment → cảnh báo.

---

## 15.4. SLA Payment

Mặc định:

* Trước hạn 3 ngày → nhắc sale/kế toán.
* Đến hạn → nhắc.
* Quá hạn → cảnh báo leader/kế toán.

---

# 16. LEAD ASSIGNMENT WORKFLOW

## 16.1. Manual Assignment

Leader/Admin giao lead thủ công.

Rule:

* Leader chỉ giao cho sale thuộc team mình.
* Admin giao cho bất kỳ sale nào.

---

## 16.2. Round Robin Assignment

Lead mới được chia lần lượt.

Ví dụ:

* Sale A
* Sale B
* Sale C

Lead 1 → Sale A
Lead 2 → Sale B
Lead 3 → Sale C
Lead 4 → Sale A

---

## 16.3. Assignment theo dự án

Ví dụ:

* Lead dự án A → Team A
* Lead dự án B → Team B

---

## 16.4. Assignment theo năng lực

Ví dụ:

* Khách ngân sách > 10 tỷ → Sale Senior
* Khách Super Hot → Sale có conversion cao
* Lead rác → Sale Junior hoặc queue lọc lead

---

# 17. LEAD RECLAIM WORKFLOW

## 17.1. Mục tiêu

Thu hồi khách/lead bị sale bỏ quên.

---

## 17.2. Điều kiện thu hồi

Lead có thể bị thu hồi nếu:

* Không gọi sau 60 phút từ khi được giao.
* Không có activity trong 3 ngày.
* Khách Hot không được chăm sóc trong 24 giờ.
* Sale nghỉ việc.
* Leader/Admin thu hồi thủ công.

---

## 17.3. Quy trình

```text
Lead assigned to Sale
→ SLA timer starts
→ No activity within configured time
→ Warning to Sale
→ Warning to Leader
→ Reclaim Lead
→ Move to Lead Pool or assign to another Sale
→ Write Audit Log
```

---

## 17.4. Lead Pool

Lead sau khi thu hồi có thể:

* Chuyển về kho lead chung.
* Giao cho sale khác.
* Giao cho leader duyệt lại.
* Đánh dấu reclaimed.

---

# 18. FOLLOW-UP PLAYBOOK WORKFLOW

## 18.1. Khách mới

Khi customer.status = new:

Tạo nhiệm vụ:

* Gọi điện trong 15 phút.
* Nhắn Zalo sau 1 ngày nếu chưa phản hồi.
* Gửi bảng hàng sau khi liên hệ thành công.

---

## 18.2. Khách quan tâm

Khi customer.status = interested:

Tạo nhiệm vụ:

* Gửi căn phù hợp.
* Hẹn xem nhà trong 3 ngày.
* Nhắc lại sau 2 ngày.

---

## 18.3. Khách đã xem nhà

Khi customer.status = site_visited:

Tạo nhiệm vụ:

* Gọi hỏi phản hồi trong 24 giờ.
* Gửi phương án tài chính nếu cần vay.
* Đề xuất căn thay thế nếu khách không thích.

---

## 18.4. Khách đang đàm phán

Khi customer.status = negotiating:

Tạo nhiệm vụ:

* Cập nhật giá chào.
* Ghi nhận phản hồi khách.
* Nhắc leader hỗ trợ nếu deal lớn.

---

## 18.5. Khách đã mua

Khi customer.status = closed_won:

Tạo nhiệm vụ:

* Chăm sóc sau bán.
* Chúc mừng nhận nhà.
* Hỏi giới thiệu khách mới sau 30 ngày.

---

# 19. DEAL WORKFLOW

## 19.1. Deal created

Khi tạo deal:

* Gắn customer_id
* Gắn property_id
* Gắn owner_user_id
* Gắn team_id
* Tạo timeline event
* Tạo activity follow-up đầu tiên

---

## 19.2. Deal chuyển sang deposit

Khi deal.stage = deposit:

Actions:

* Bắt buộc nhập deposit_amount
* Update property.status = deposited
* Update customer.status = deposited
* Create commission pending
* Create payment schedule nếu có
* Notify leader
* Write audit log

---

## 19.3. Deal chuyển sang contract

Khi deal.stage = contract:

Actions:

* Bắt buộc nhập contract_number
* Update property.status = contracted
* Update customer.status = contracted
* Notify accountant
* Create payment schedule
* Update forecast
* Write audit log

---

## 19.4. Deal closed won

Actions:

* Update customer.status = closed_won
* Update property.status = sold
* Update commission.status = approved hoặc pending approval
* Update reports
* Notify director/leader
* Write audit log

---

## 19.5. Deal closed lost

Actions:

* Bắt buộc chọn lost_reason
* Update customer.status = closed_lost hoặc interested nếu còn nhu cầu
* Nếu property chưa bán thì trả property.status về available
* Cancel pending commission
* Tạo task đề xuất căn khác nếu khách còn nhu cầu
* Write audit log

---

# 20. INVENTORY WORKFLOW

## 20.1. Property created

Actions:

* status = available
* Create timeline event
* Notify inventory manager nếu thiếu pháp lý/media
* Calculate property score

---

## 20.2. Property status changed

Actions:

* Validate transition
* Write property_status_history
* Write audit log
* Notify related deal owner nếu căn bị khóa/hết hàng

---

## 20.3. Property price changed

Actions:

* Write price_history
* Recalculate price_per_m2
* Notify sale đang có khách quan tâm căn này
* Notify deal owner nếu deal active

---

## 20.4. Property sold

Actions:

* Không cho tạo deal mới
* Ẩn khỏi danh sách hàng còn bán
* Update reports
* Write audit log

---

# 21. MARKETING WORKFLOW

## 21.1. Lead imported from marketing

Actions:

* Normalize phone
* Check duplicate
* Attach campaign/adset/ad
* Calculate lead quality
* Assign lead theo rule
* Create SLA timer
* Write audit log

---

## 21.2. Duplicate lead

Actions:

* Không tạo customer trùng.
* Gắn lead vào customer cũ nếu có.
* Ghi source mới vào attribution.
* Notify owner hiện tại.
* Nếu khách cũ bị bỏ quên thì notify leader.

---

## 21.3. Lead quality scoring

Điểm gợi ý:

* Có số điện thoại hợp lệ: +20
* Có ngân sách: +20
* Có dự án quan tâm: +20
* Có nhu cầu mua ngay: +30
* Không nghe máy nhiều lần: -20
* Sai số: -100

---

# 22. NOTIFICATION ENGINE

## 22.1. Kênh thông báo

Phase 1:

* In-app notification
* Email notification

Phase 2:

* Zalo
* SMS
* Push notification
* Telegram/Slack

---

## 22.2. Loại thông báo

* task_due
* task_overdue
* lead_assigned
* lead_reclaimed
* customer_hot
* deal_stage_changed
* payment_due
* commission_ready
* property_status_changed
* system_alert

---

## 22.3. Priority

* low
* normal
* high
* urgent

---

# 23. WORKFLOW LOG

Mỗi lần workflow chạy phải ghi:

* id
* workflow_id
* trigger_event
* entity_type
* entity_id
* status
* started_at
* finished_at
* error_message
* executed_actions
* created_by_system

---

# 24. DATABASE TABLES CẦN CÓ

Codex cần tạo các bảng sau:

## Workflow

* workflow_definitions
* workflow_rules
* workflow_conditions
* workflow_actions
* workflow_runs
* workflow_run_logs

---

## State Machine

* state_definitions
* state_transitions
* state_transition_logs

---

## SLA

* sla_policies
* sla_instances
* sla_events

---

## Notifications

* notifications
* notification_templates
* notification_preferences

---

## Jobs

* background_jobs
* scheduled_jobs

---

# 25. WORKFLOW DEFINITION MODEL

## workflow_definitions

Fields:

* id
* name
* description
* entity_type
* trigger_event
* is_active
* priority
* created_at
* updated_at

---

## workflow_rules

Fields:

* id
* workflow_id
* name
* condition_logic
* is_active

---

## workflow_conditions

Fields:

* id
* rule_id
* field_name
* operator
* value
* value_type

---

## workflow_actions

Fields:

* id
* workflow_id
* action_type
* action_config
* execution_order
* is_active

---

# 26. BACKGROUND JOBS

Hệ thống cần job chạy định kỳ.

## 26.1. check_overdue_activities

Chạy mỗi 5 phút.

Làm việc:

* Tìm activity quá hạn.
* Chuyển status = overdue.
* Gửi notification.

---

## 26.2. check_lead_sla

Chạy mỗi 5 phút.

Làm việc:

* Tìm lead chưa xử lý.
* Cảnh báo sale/leader.
* Thu hồi nếu quá hạn.

---

## 26.3. check_payment_due

Chạy mỗi ngày 08:00.

Làm việc:

* Tìm payment sắp đến hạn.
* Tìm payment quá hạn.
* Gửi notification.

---

## 26.4. update_lead_scores

Chạy mỗi ngày.

Làm việc:

* Tính lại lead score.
* Cập nhật temperature.

---

## 26.5. update_forecast

Chạy mỗi ngày.

Làm việc:

* Tính forecast doanh thu.
* Tính forecast hoa hồng.

---

# 27. API CẦN CÓ

## Workflow APIs

* GET /workflows
* POST /workflows
* GET /workflows/{id}
* PUT /workflows/{id}
* DELETE /workflows/{id}
* POST /workflows/{id}/activate
* POST /workflows/{id}/deactivate
* POST /workflows/{id}/test

---

## State APIs

* GET /states/{entity_type}
* POST /states
* PUT /states/{id}
* GET /transitions/{entity_type}
* POST /transitions
* POST /entities/{entity_type}/{id}/transition

---

## SLA APIs

* GET /sla-policies
* POST /sla-policies
* PUT /sla-policies/{id}
* GET /sla-instances
* POST /sla-instances/{id}/pause
* POST /sla-instances/{id}/resume

---

## Notification APIs

* GET /notifications
* POST /notifications/{id}/read
* POST /notifications/read-all

---

# 28. BACKEND IMPLEMENTATION NOTES

## 28.1. Service cần có

* WorkflowService
* RuleEngineService
* StateMachineService
* SLAService
* NotificationService
* BackgroundJobService
* AuditLogService

---

## 28.2. Hàm quan trọng

```python
evaluate_conditions(entity, conditions)
execute_actions(entity, actions)
validate_transition(entity_type, from_state, to_state)
run_workflow(trigger_event, entity_type, entity_id)
create_sla_instance(policy_id, entity_type, entity_id)
check_sla_breach()
create_notification(user_id, title, message)
write_workflow_log()
```

---

## 28.3. Event Bus nội bộ

Khi một hành động xảy ra, backend nên phát event:

```python
publish_event("lead.created", lead_id)
publish_event("deal.stage_changed", deal_id)
publish_event("property.status_changed", property_id)
```

Workflow Engine lắng nghe event và chạy workflow phù hợp.

---

# 29. FRONTEND IMPLEMENTATION NOTES

Cần có màn hình:

## 29.1. Workflow Builder

Cho Admin cấu hình:

* Trigger
* Condition
* Action
* Priority
* Active/Inactive

---

## 29.2. State Transition Config

Cho Admin cấu hình:

* Entity type
* From state
* To state
* Required fields
* Required permission

---

## 29.3. SLA Config

Cho Admin cấu hình:

* Entity type
* SLA time
* Warning time
* Escalation user/role
* Reclaim rule

---

## 29.4. Notification Center

Cho user xem:

* Thông báo mới
* Việc quá hạn
* Lead mới
* Deal thay đổi

---

# 30. ACCEPTANCE CRITERIA

## 30.1. Lead Workflow

* Khi lead mới được giao, hệ thống tự tạo nhiệm vụ gọi điện.
* Nếu sale không gọi trong 15 phút, hệ thống cảnh báo sale.
* Nếu sale không gọi trong 30 phút, hệ thống cảnh báo leader.
* Nếu sale không gọi trong 60 phút, leader/admin có thể thu hồi lead.

---

## 30.2. Deal Workflow

* Không cho deal chuyển sang deposit nếu thiếu số tiền cọc.
* Khi deal chuyển sang deposit, property tự chuyển sang deposited.
* Khi deal closed_won, property tự chuyển sang sold.
* Khi deal closed_lost, bắt buộc nhập lý do thất bại.

---

## 30.3. Inventory Workflow

* Khi đổi giá căn hộ, hệ thống lưu lịch sử giá.
* Khi căn hộ sold, sale không còn thấy căn trong danh sách còn hàng.
* Khi căn đang deposited, không cho tạo deal deposit khác.

---

## 30.4. SLA Workflow

* Activity quá hạn tự đổi status thành overdue.
* Notification được gửi đúng người.
* Không gửi trùng notification cho cùng một SLA breach.

---

## 30.5. Audit

* Mọi workflow thay đổi trạng thái phải ghi audit log.
* Workflow run thất bại phải có error message.
* Admin xem được lịch sử workflow run.

---

# 31. PHASE IMPLEMENTATION

## Phase 1

Bắt buộc có:

* State Machine
* Basic Workflow Trigger
* Activity Reminder
* SLA Lead
* Deal Stage Validation
* Notification In-App
* Audit Log

---

## Phase 2

Bổ sung:

* Workflow Builder
* Rule Engine Dynamic
* Lead Reclaim
* Payment Reminder
* Commission Workflow
* Email Notification

---

## Phase 3

Nâng cao:

* AI Lead Scoring
* AI Deal Scoring
* AI Next Best Action
* Advanced Automation
* External Webhook
* Zalo/SMS Integration

---

# 32. KẾT LUẬN

Workflow Engine là bộ máy vận hành tự động của CRM bất động sản.

Nếu không có Workflow Engine, hệ thống chỉ là nơi nhập liệu.

Nếu có Workflow Engine, hệ thống trở thành công cụ ép quy trình, ép sale chăm khách đúng hạn, tự động cảnh báo, tự động đồng bộ dữ liệu, tự động bảo vệ doanh thu.

Các phần bắt buộc phải làm tốt:

* State Machine
* SLA Lead
* Follow-up Automation
* Deal Stage Validation
* Lead Reclaim
* Notification
* Audit Log

Đây là nền tảng để sau này phát triển AI Assistant và hệ thống tự động hóa marketing/sales chuyên sâu.
