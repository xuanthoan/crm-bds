# DATABASE_SCHEMA.md

# REAL ESTATE CRM & SALES MANAGEMENT SYSTEM

Version: 1.0
Database: PostgreSQL
Recommended ORM: SQLAlchemy / Prisma / Drizzle
Status: Draft

---

# 1. MỤC TIÊU THIẾT KẾ DATABASE

Database cần phục vụ hệ thống CRM bất động sản gồm:

* Quản lý khách hàng
* Quản lý Lead
* Quản lý kho hàng bất động sản
* Quản lý dự án
* Quản lý căn hộ/sản phẩm
* Quản lý giao dịch
* Quản lý chăm sóc khách hàng
* Quản lý sale/leader/admin
* Quản lý marketing
* Quản lý hoa hồng
* Quản lý file đính kèm
* Quản lý báo cáo
* Quản lý workflow
* Quản lý audit log

Database phải đảm bảo:

* Không trùng khách hàng theo số điện thoại
* Phân quyền dữ liệu theo nhân sự
* Truy vết lịch sử thay đổi
* Dễ mở rộng module mới
* Dễ làm báo cáo
* Dễ tích hợp AI/automation sau này

---

# 2. NGUYÊN TẮC CHUNG

## 2.1. ID

Tất cả bảng chính dùng:

```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

## 2.2. Thời gian

Tất cả bảng nghiệp vụ nên có:

```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
deleted_at TIMESTAMP WITH TIME ZONE NULL
```

## 2.3. Người tạo / người sửa

Các bảng quan trọng nên có:

```sql
created_by UUID NULL REFERENCES users(id)
updated_by UUID NULL REFERENCES users(id)
```

## 2.4. Soft Delete

Không xóa cứng dữ liệu quan trọng.

Dùng:

```sql
deleted_at TIMESTAMP WITH TIME ZONE NULL
```

## 2.5. Trạng thái

Không nên để sale nhập trạng thái tự do.

Trạng thái phải dùng ENUM hoặc bảng `master_statuses`.

Khuyến nghị:

* Giai đoạn đầu: dùng ENUM
* Giai đoạn mở rộng: dùng bảng master data

## 2.6. Tiền tệ

Dùng:

```sql
NUMERIC(18,2)
```

Không dùng FLOAT cho tiền.

---

# 3. DANH SÁCH BẢNG CHÍNH

## Nhóm người dùng & phân quyền

* users
* roles
* permissions
* role_permissions
* user_roles
* teams
* team_members

## Nhóm khách hàng & lead

* customers
* customer_contacts
* customer_related_people
* leads
* customer_tags
* tags
* customer_timeline
* customer_notes

## Nhóm kho hàng

* projects
* properties
* property_owners
* property_owner_links
* property_price_history
* property_status_history
* property_media
* property_legal_documents

## Nhóm giao dịch

* deals
* deal_stage_history
* deal_negotiations
* deposits
* contracts
* payment_schedules
* commissions
* commission_splits

## Nhóm chăm sóc khách hàng

* activities
* tasks
* appointments
* site_visits
* followup_playbooks
* followup_steps

## Nhóm marketing

* marketing_campaigns
* marketing_adsets
* marketing_ads
* marketing_costs
* lead_sources

## Nhóm file & audit

* files
* audit_logs
* notifications
* workflow_rules
* workflow_executions

---

# 4. USERS / NHÂN SỰ

## 4.1. users

Lưu thông tin tài khoản nhân sự.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    employee_code VARCHAR(50) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(30),

    password_hash TEXT NOT NULL,

    avatar_url TEXT,

    position VARCHAR(100),
    department VARCHAR(100),

    status VARCHAR(50) NOT NULL DEFAULT 'active',
    -- active, probation, inactive, resigned, suspended

    joined_at DATE,
    resigned_at DATE,

    last_login_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

---

## 4.2. roles

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Role mặc định:

* admin
* director
* leader
* sale
* marketing
* accountant
* inventory_manager

---

## 4.3. permissions

```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(150) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    module VARCHAR(100) NOT NULL,
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Ví dụ permission:

* customer.view_own
* customer.view_team
* customer.view_all
* customer.create
* customer.update
* customer.delete
* deal.view_own
* deal.view_team
* deal.view_all
* property.manage
* report.view_all

---

## 4.4. role_permissions

```sql
CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    PRIMARY KEY (role_id, permission_id)
);
```

---

## 4.5. user_roles

```sql
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    PRIMARY KEY (user_id, role_id)
);
```

---

## 4.6. teams

```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    leader_id UUID REFERENCES users(id),

    description TEXT,
    status VARCHAR(50) DEFAULT 'active',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 4.7. team_members

```sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role_in_team VARCHAR(50) DEFAULT 'member',
    joined_at DATE DEFAULT CURRENT_DATE,
    left_at DATE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    UNIQUE(team_id, user_id)
);
```

---

# 5. CUSTOMERS / KHÁCH HÀNG

## 5.1. customers

Bảng khách hàng chính.

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_code VARCHAR(50) UNIQUE,

    full_name VARCHAR(255) NOT NULL,
    gender VARCHAR(20),
    date_of_birth DATE,

    phone_primary VARCHAR(30),
    phone_secondary VARCHAR(30),

    email VARCHAR(255),
    zalo VARCHAR(255),
    facebook VARCHAR(255),

    address TEXT,
    province VARCHAR(100),
    district VARCHAR(100),
    ward VARCHAR(100),

    occupation VARCHAR(255),
    company VARCHAR(255),
    job_title VARCHAR(255),

    assigned_sale_id UUID REFERENCES users(id),
    assigned_team_id UUID REFERENCES teams(id),

    lead_source_id UUID,
    status VARCHAR(50) DEFAULT 'new',
    temperature VARCHAR(50) DEFAULT 'cold',
    -- cold, warm, hot, super_hot

    score INTEGER DEFAULT 0,

    financial_rank VARCHAR(10),
    -- A, B, C, D

    budget_min NUMERIC(18,2),
    budget_max NUMERIC(18,2),
    cash_available NUMERIC(18,2),
    loan_needed NUMERIC(18,2),
    expected_loan_ratio NUMERIC(5,2),
    monthly_income NUMERIC(18,2),

    buying_purpose VARCHAR(100),
    -- living, investment, rental, for_children, for_parents

    expected_buying_time VARCHAR(100),
    -- now, 1_month, 3_months, 6_months, over_6_months

    note TEXT,

    last_contact_at TIMESTAMP WITH TIME ZONE,
    next_followup_at TIMESTAMP WITH TIME ZONE,

    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

Index quan trọng:

```sql
CREATE INDEX idx_customers_phone_primary ON customers(phone_primary);
CREATE INDEX idx_customers_phone_secondary ON customers(phone_secondary);
CREATE INDEX idx_customers_assigned_sale ON customers(assigned_sale_id);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_temperature ON customers(temperature);
CREATE INDEX idx_customers_next_followup ON customers(next_followup_at);
```

---

## 5.2. customer_contacts

Lưu thêm nhiều kênh liên hệ nếu cần.

```sql
CREATE TABLE customer_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    contact_type VARCHAR(50) NOT NULL,
    -- phone, email, zalo, facebook, telegram, other

    contact_value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 5.3. customer_related_people

Người liên quan đến quyết định mua.

```sql
CREATE TABLE customer_related_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    full_name VARCHAR(255),
    phone VARCHAR(30),
    relationship VARCHAR(100),
    -- wife, husband, parent, child, friend

    decision_role VARCHAR(100),
    -- payer, decision_maker, influencer, reference

    note TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 5.4. customer_demands

Lưu nhu cầu tìm kiếm bất động sản.

```sql
CREATE TABLE customer_demands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    property_type VARCHAR(100),
    -- apartment, house, villa, land, shophouse

    project_id UUID,
    province VARCHAR(100),
    district VARCHAR(100),

    bedroom_min INTEGER,
    bedroom_max INTEGER,

    area_min NUMERIC(10,2),
    area_max NUMERIC(10,2),

    price_min NUMERIC(18,2),
    price_max NUMERIC(18,2),

    direction VARCHAR(100),
    view_type VARCHAR(100),

    note TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 6. LEADS

## 6.1. lead_sources

```sql
CREATE TABLE lead_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Nguồn mặc định:

* facebook_ads
* google_ads
* tiktok_ads
* zalo_ads
* website
* landing_page
* hotline
* referral
* ctv
* sale_self

---

## 6.2. leads

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    lead_code VARCHAR(50) UNIQUE,

    full_name VARCHAR(255),
    phone VARCHAR(30),
    email VARCHAR(255),
    zalo VARCHAR(255),
    facebook VARCHAR(255),

    source_id UUID REFERENCES lead_sources(id),

    campaign_id UUID,
    adset_id UUID,
    ad_id UUID,

    raw_payload JSONB,

    customer_id UUID REFERENCES customers(id),

    assigned_sale_id UUID REFERENCES users(id),
    assigned_team_id UUID REFERENCES teams(id),

    status VARCHAR(50) DEFAULT 'new',
    -- new, assigned, contacted, duplicate, junk, converted, lost

    quality VARCHAR(50) DEFAULT 'unknown',
    -- unknown, valid, invalid, duplicate, junk

    duplicate_customer_id UUID REFERENCES customers(id),

    first_response_at TIMESTAMP WITH TIME ZONE,
    assigned_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Index:

```sql
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_source ON leads(source_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_assigned_sale ON leads(assigned_sale_id);
CREATE INDEX idx_leads_created_at ON leads(created_at);
```

---

# 7. TAGS

## 7.1. tags

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(20),
    module VARCHAR(100),
    -- customer, property, deal

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 7.2. customer_tags

```sql
CREATE TABLE customer_tags (
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    PRIMARY KEY (customer_id, tag_id)
);
```

---

# 8. PROJECTS / DỰ ÁN

## 8.1. projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    project_code VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,

    investor_name VARCHAR(255),
    developer_name VARCHAR(255),
    management_company VARCHAR(255),

    address TEXT,
    province VARCHAR(100),
    district VARCHAR(100),
    ward VARCHAR(100),

    website TEXT,
    hotline VARCHAR(50),

    status VARCHAR(50) DEFAULT 'selling',
    -- preparing, selling, constructing, delivered, paused, closed

    description TEXT,

    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

---

# 9. PROPERTIES / KHO HÀNG

## 9.1. properties

```sql
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    property_code VARCHAR(50) UNIQUE NOT NULL,
    internal_code VARCHAR(50),

    project_id UUID REFERENCES projects(id),

    property_type VARCHAR(100),
    -- apartment, house, villa, land, shophouse, office

    block VARCHAR(100),
    tower VARCHAR(100),
    floor INTEGER,
    unit_number VARCHAR(50),

    bedrooms INTEGER,
    bathrooms INTEGER,

    area_gross NUMERIC(10,2),
    area_net NUMERIC(10,2),
    balcony_area NUMERIC(10,2),
    garden_area NUMERIC(10,2),

    door_direction VARCHAR(100),
    balcony_direction VARCHAR(100),
    view_type VARCHAR(100),

    position_note TEXT,
    -- corner, near_elevator, far_elevator, near_trash_room

    listed_price NUMERIC(18,2),
    owner_expected_price NUMERIC(18,2),
    minimum_acceptable_price NUMERIC(18,2),
    last_transaction_price NUMERIC(18,2),

    price_per_m2 NUMERIC(18,2),

    commission_fixed NUMERIC(18,2),
    commission_percent NUMERIC(5,2),

    legal_status VARCHAR(100),
    -- red_book, sale_contract, booking, incomplete, dispute

    inventory_status VARCHAR(50) DEFAULT 'available',
    -- available, reserved, negotiating, deposited, contracted, sold, locked, off_market

    priority_score INTEGER DEFAULT 0,

    owner_id UUID,

    source_type VARCHAR(100),
    -- investor, owner, internal_sale, collaborator, partner

    source_contact_name VARCHAR(255),
    source_contact_phone VARCHAR(30),

    imported_at TIMESTAMP WITH TIME ZONE,
    imported_by UUID REFERENCES users(id),

    note TEXT,

    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

Index:

```sql
CREATE INDEX idx_properties_project ON properties(project_id);
CREATE INDEX idx_properties_status ON properties(inventory_status);
CREATE INDEX idx_properties_price ON properties(listed_price);
CREATE INDEX idx_properties_bedrooms ON properties(bedrooms);
CREATE INDEX idx_properties_area_net ON properties(area_net);
```

---

## 9.2. property_owners

```sql
CREATE TABLE property_owners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    email VARCHAR(255),
    address TEXT,

    cooperation_level VARCHAR(50),
    -- easy, normal, difficult

    urgency_level VARCHAR(50),
    -- urgent, normal, not_urgent

    note TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 9.3. property_owner_links

Một căn có thể có nhiều chủ sở hữu.

```sql
CREATE TABLE property_owner_links (
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES property_owners(id) ON DELETE CASCADE,

    ownership_percent NUMERIC(5,2),

    PRIMARY KEY (property_id, owner_id)
);
```

---

## 9.4. property_price_history

```sql
CREATE TABLE property_price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    old_price NUMERIC(18,2),
    new_price NUMERIC(18,2),

    reason TEXT,

    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 9.5. property_status_history

```sql
CREATE TABLE property_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    old_status VARCHAR(50),
    new_status VARCHAR(50),

    reason TEXT,

    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 10. DEALS / GIAO DỊCH

## 10.1. deals

```sql
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_code VARCHAR(50) UNIQUE,

    customer_id UUID NOT NULL REFERENCES customers(id),
    property_id UUID REFERENCES properties(id),
    project_id UUID REFERENCES projects(id),

    sale_id UUID REFERENCES users(id),
    leader_id UUID REFERENCES users(id),
    team_id UUID REFERENCES teams(id),

    deal_type VARCHAR(100),
    -- buy, rent, transfer, booking

    stage VARCHAR(50) DEFAULT 'lead',
    -- lead, contacted, qualified, appointment, site_visit, negotiation,
    -- booking, deposit, contract, closed_won, closed_lost

    status VARCHAR(50) DEFAULT 'open',
    -- open, won, lost, cancelled

    listed_price NUMERIC(18,2),
    offered_price NUMERIC(18,2),
    negotiated_price NUMERIC(18,2),
    final_price NUMERIC(18,2),

    expected_revenue NUMERIC(18,2),
    expected_commission NUMERIC(18,2),
    actual_commission NUMERIC(18,2),

    probability INTEGER DEFAULT 0,

    expected_close_date DATE,
    actual_close_date DATE,

    lost_reason VARCHAR(255),
    lost_note TEXT,

    note TEXT,

    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

Index:

```sql
CREATE INDEX idx_deals_customer ON deals(customer_id);
CREATE INDEX idx_deals_property ON deals(property_id);
CREATE INDEX idx_deals_sale ON deals(sale_id);
CREATE INDEX idx_deals_stage ON deals(stage);
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_expected_close_date ON deals(expected_close_date);
```

---

## 10.2. deal_stage_history

```sql
CREATE TABLE deal_stage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    old_stage VARCHAR(50),
    new_stage VARCHAR(50),

    note TEXT,

    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 10.3. deal_negotiations

```sql
CREATE TABLE deal_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    offer_by VARCHAR(50),
    -- customer, owner, company

    offer_price NUMERIC(18,2),
    response_price NUMERIC(18,2),

    content TEXT,
    result VARCHAR(100),
    -- accepted, rejected, pending

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 10.4. deposits

```sql
CREATE TABLE deposits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    deposit_date DATE NOT NULL,
    amount NUMERIC(18,2) NOT NULL,

    payment_method VARCHAR(50),
    -- cash, bank_transfer

    receipt_file_id UUID,

    status VARCHAR(50) DEFAULT 'confirmed',
    -- pending, confirmed, cancelled, refunded

    note TEXT,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 10.5. contracts

```sql
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    contract_number VARCHAR(100),
    signed_date DATE,

    contract_value NUMERIC(18,2),

    status VARCHAR(50) DEFAULT 'draft',
    -- draft, signed, cancelled, completed

    file_id UUID,

    note TEXT,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 10.6. payment_schedules

```sql
CREATE TABLE payment_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    installment_no INTEGER,
    due_date DATE,
    amount NUMERIC(18,2),

    paid_amount NUMERIC(18,2) DEFAULT 0,
    paid_date DATE,

    status VARCHAR(50) DEFAULT 'unpaid',
    -- unpaid, partial, paid, overdue

    note TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 11. COMMISSIONS / HOA HỒNG

## 11.1. commissions

```sql
CREATE TABLE commissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,

    total_commission NUMERIC(18,2) NOT NULL,
    received_amount NUMERIC(18,2) DEFAULT 0,

    status VARCHAR(50) DEFAULT 'pending',
    -- pending, approved, partially_paid, paid, held, cancelled

    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,

    note TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 11.2. commission_splits

```sql
CREATE TABLE commission_splits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    commission_id UUID NOT NULL REFERENCES commissions(id) ON DELETE CASCADE,

    user_id UUID REFERENCES users(id),

    role_type VARCHAR(50),
    -- sale, leader, collaborator, company

    percent NUMERIC(5,2),
    amount NUMERIC(18,2),

    paid_amount NUMERIC(18,2) DEFAULT 0,
    paid_at TIMESTAMP WITH TIME ZONE,

    status VARCHAR(50) DEFAULT 'pending',
    -- pending, approved, paid

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 12. ACTIVITIES / CHĂM SÓC KHÁCH HÀNG

## 12.1. activities

Lưu lịch sử chăm sóc.

```sql
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    deal_id UUID REFERENCES deals(id),

    user_id UUID REFERENCES users(id),

    activity_type VARCHAR(50) NOT NULL,
    -- call, zalo, facebook, email, sms, meeting, site_visit, video_call

    subject VARCHAR(255),
    content TEXT,

    result VARCHAR(100),
    -- no_answer, answered, interested, appointment, not_interested, callback

    activity_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    next_followup_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

Index:

```sql
CREATE INDEX idx_activities_customer ON activities(customer_id);
CREATE INDEX idx_activities_user ON activities(user_id);
CREATE INDEX idx_activities_activity_at ON activities(activity_at);
```

---

## 12.2. tasks

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID REFERENCES customers(id),
    deal_id UUID REFERENCES deals(id),
    assigned_to UUID REFERENCES users(id),

    title VARCHAR(255) NOT NULL,
    description TEXT,

    task_type VARCHAR(50),
    -- call, zalo, email, meeting, document, payment_reminder

    due_at TIMESTAMP WITH TIME ZONE,

    status VARCHAR(50) DEFAULT 'pending',
    -- pending, in_progress, completed, overdue, cancelled

    priority VARCHAR(50) DEFAULT 'normal',
    -- low, normal, high, urgent

    completed_at TIMESTAMP WITH TIME ZONE,

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 12.3. appointments

```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id),
    deal_id UUID REFERENCES deals(id),
    property_id UUID REFERENCES properties(id),

    assigned_sale_id UUID REFERENCES users(id),

    appointment_type VARCHAR(50),
    -- meeting, site_visit, contract_signing

    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    location TEXT,

    status VARCHAR(50) DEFAULT 'scheduled',
    -- scheduled, confirmed, completed, postponed, cancelled, no_show

    result TEXT,

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 12.4. site_visits

```sql
CREATE TABLE site_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    appointment_id UUID REFERENCES appointments(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    property_id UUID REFERENCES properties(id),
    project_id UUID REFERENCES projects(id),

    visit_date TIMESTAMP WITH TIME ZONE,

    customer_feedback VARCHAR(100),
    -- loved, liked, neutral, disliked

    liked_points TEXT,
    disliked_points TEXT,

    next_action TEXT,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 13. FOLLOW-UP PLAYBOOK

## 13.1. followup_playbooks

```sql
CREATE TABLE followup_playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,
    description TEXT,

    customer_status VARCHAR(50),
    temperature VARCHAR(50),

    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 13.2. followup_steps

```sql
CREATE TABLE followup_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    playbook_id UUID NOT NULL REFERENCES followup_playbooks(id) ON DELETE CASCADE,

    step_order INTEGER NOT NULL,
    delay_days INTEGER DEFAULT 0,

    task_type VARCHAR(50),
    title VARCHAR(255),
    description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 14. MARKETING

## 14.1. marketing_campaigns

```sql
CREATE TABLE marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    campaign_code VARCHAR(100),
    name VARCHAR(255) NOT NULL,

    platform VARCHAR(50),
    -- facebook, google, tiktok, zalo, website

    project_id UUID REFERENCES projects(id),

    start_date DATE,
    end_date DATE,

    daily_budget NUMERIC(18,2),
    total_budget NUMERIC(18,2),

    status VARCHAR(50) DEFAULT 'draft',
    -- draft, running, paused, ended

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 14.2. marketing_adsets

```sql
CREATE TABLE marketing_adsets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    campaign_id UUID NOT NULL REFERENCES marketing_campaigns(id) ON DELETE CASCADE,

    adset_code VARCHAR(100),
    name VARCHAR(255),

    target_audience JSONB,

    status VARCHAR(50) DEFAULT 'active',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 14.3. marketing_ads

```sql
CREATE TABLE marketing_ads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    adset_id UUID NOT NULL REFERENCES marketing_adsets(id) ON DELETE CASCADE,

    ad_code VARCHAR(100),
    name VARCHAR(255),

    creative_type VARCHAR(50),
    -- image, video, text, carousel

    creative_url TEXT,
    landing_page_url TEXT,

    status VARCHAR(50) DEFAULT 'active',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 14.4. marketing_costs

```sql
CREATE TABLE marketing_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    campaign_id UUID REFERENCES marketing_campaigns(id),
    adset_id UUID REFERENCES marketing_adsets(id),
    ad_id UUID REFERENCES marketing_ads(id),

    cost_date DATE NOT NULL,
    amount NUMERIC(18,2) NOT NULL,

    impressions INTEGER,
    clicks INTEGER,
    leads INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 15. FILES / ĐÍNH KÈM

## 15.1. files

```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    original_name VARCHAR(255) NOT NULL,
    stored_name VARCHAR(255) NOT NULL,

    file_url TEXT NOT NULL,
    file_type VARCHAR(100),
    mime_type VARCHAR(100),
    file_size BIGINT,

    entity_type VARCHAR(100),
    -- customer, property, project, deal, contract, deposit

    entity_id UUID,

    uploaded_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 16. NOTES / TIMELINE

## 16.1. customer_notes

```sql
CREATE TABLE customer_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    note TEXT NOT NULL,

    visibility VARCHAR(50) DEFAULT 'internal',
    -- private, team, internal

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 16.2. customer_timeline

```sql
CREATE TABLE customer_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    event_type VARCHAR(100),
    title VARCHAR(255),
    description TEXT,

    related_entity_type VARCHAR(100),
    related_entity_id UUID,

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 17. NOTIFICATIONS

## 17.1. notifications

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(255) NOT NULL,
    message TEXT,

    notification_type VARCHAR(100),
    -- task_due, lead_overdue, deal_update, commission_paid

    related_entity_type VARCHAR(100),
    related_entity_id UUID,

    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 18. WORKFLOW ENGINE

## 18.1. workflow_rules

```sql
CREATE TABLE workflow_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(255) NOT NULL,
    description TEXT,

    trigger_entity VARCHAR(100),
    -- lead, customer, deal, property, task

    trigger_event VARCHAR(100),
    -- created, updated, status_changed, overdue

    conditions JSONB,
    actions JSONB,

    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 18.2. workflow_executions

```sql
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    rule_id UUID REFERENCES workflow_rules(id),

    entity_type VARCHAR(100),
    entity_id UUID,

    status VARCHAR(50),
    -- success, failed, skipped

    result JSONB,
    error_message TEXT,

    executed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 19. AUDIT LOG

## 19.1. audit_logs

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,

    action VARCHAR(50) NOT NULL,
    -- create, update, delete, status_change, assign, import, export

    old_values JSONB,
    new_values JSONB,

    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    ip_address VARCHAR(100),
    user_agent TEXT
);
```

Index:

```sql
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_changed_by ON audit_logs(changed_by);
CREATE INDEX idx_audit_changed_at ON audit_logs(changed_at);
```

---

# 20. IMPORT / EXPORT

## 20.1. import_jobs

```sql
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    import_type VARCHAR(100),
    -- customers, properties, leads

    file_id UUID REFERENCES files(id),

    status VARCHAR(50) DEFAULT 'pending',
    -- pending, processing, completed, failed

    total_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,

    error_report JSONB,

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

---

## 20.2. export_jobs

```sql
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    export_type VARCHAR(100),
    -- customers, properties, deals, reports

    filters JSONB,

    file_id UUID REFERENCES files(id),

    status VARCHAR(50) DEFAULT 'pending',
    -- pending, processing, completed, failed

    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

---

# 21. MASTER DATA

## 21.1. master_statuses

Dùng để cấu hình trạng thái linh hoạt.

```sql
CREATE TABLE master_statuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    module VARCHAR(100) NOT NULL,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,

    sort_order INTEGER DEFAULT 0,
    color VARCHAR(20),

    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    UNIQUE(module, code)
);
```

---

## 21.2. master_lost_reasons

```sql
CREATE TABLE master_lost_reasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    module VARCHAR(100),
    -- customer, deal

    code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,

    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

# 22. VIEW BÁO CÁO GỢI Ý

## 22.1. vw_sale_dashboard

Dữ liệu cho Sale:

* Tổng khách đang chăm
* Khách nóng
* Task hôm nay
* Task quá hạn
* Deal đang mở
* Hoa hồng dự kiến

---

## 22.2. vw_leader_dashboard

Dữ liệu cho Leader:

* Tổng lead team
* Tổng khách team
* Tổng deal team
* Sale bỏ quên khách
* Conversion theo sale

---

## 22.3. vw_ceo_dashboard

Dữ liệu cho Giám đốc:

* Tổng doanh thu
* Tổng deal
* Tổng lead
* Tồn kho
* Marketing ROI

---

## 22.4. vw_marketing_roi

Dữ liệu:

* Campaign
* Cost
* Lead
* Appointment
* Deposit
* Deal
* Revenue
* ROI

---

# 23. RÀNG BUỘC CHỐNG TRÙNG

## 23.1. Chống trùng khách hàng

Không nên unique trực tiếp phone vì có thể có số rỗng/null.

Nên tạo index partial:

```sql
CREATE UNIQUE INDEX uq_customers_phone_primary_not_null
ON customers(phone_primary)
WHERE phone_primary IS NOT NULL AND deleted_at IS NULL;
```

Có thể bổ sung thêm bảng chuẩn hóa số điện thoại để chống trùng tốt hơn.

---

## 23.2. Chống trùng mã căn

```sql
CREATE UNIQUE INDEX uq_properties_code_not_deleted
ON properties(property_code)
WHERE deleted_at IS NULL;
```

---

# 24. TRIGGER CẦN CÓ

## 24.1. Auto updated_at

Tự động cập nhật `updated_at` khi sửa dữ liệu.

## 24.2. Log thay đổi trạng thái khách hàng

Khi `customers.status` thay đổi, ghi vào `customer_timeline`.

## 24.3. Log thay đổi trạng thái căn hộ

Khi `properties.inventory_status` thay đổi, ghi vào `property_status_history`.

## 24.4. Log thay đổi giá căn hộ

Khi `properties.listed_price` thay đổi, ghi vào `property_price_history`.

## 24.5. Log thay đổi stage giao dịch

Khi `deals.stage` thay đổi, ghi vào `deal_stage_history`.

## 24.6. Đồng bộ trạng thái

Ví dụ:

Khi deal chuyển sang `deposit`:

* property.inventory_status = deposited
* customer.status = deposit
* commission.status = pending

---

# 25. INDEX CẦN CÓ

## Customers

* phone_primary
* phone_secondary
* assigned_sale_id
* assigned_team_id
* status
* temperature
* next_followup_at

## Leads

* phone
* source_id
* campaign_id
* status
* assigned_sale_id
* created_at

## Properties

* project_id
* inventory_status
* listed_price
* bedrooms
* area_net
* property_type

## Deals

* customer_id
* property_id
* sale_id
* team_id
* stage
* status
* expected_close_date

## Activities

* customer_id
* user_id
* activity_at

## Tasks

* assigned_to
* status
* due_at

---

# 26. QUY ƯỚC ENUM / STATUS

## Customer Status

* new
* contacted
* no_answer
* interested
* appointment
* site_visit
* negotiation
* deposit
* contract
* won
* lost

## Lead Temperature

* cold
* warm
* hot
* super_hot

## Inventory Status

* available
* reserved
* negotiating
* deposited
* contracted
* sold
* locked
* off_market

## Deal Stage

* lead
* contacted
* qualified
* appointment
* site_visit
* negotiation
* booking
* deposit
* contract
* closed_won
* closed_lost

## Task Status

* pending
* in_progress
* completed
* overdue
* cancelled

## Payment Status

* unpaid
* partial
* paid
* overdue

## Commission Status

* pending
* approved
* partially_paid
* paid
* held
* cancelled

---

# 27. GỢI Ý SEED DATA

## Roles

* Admin
* Director
* Leader
* Sale
* Marketing
* Accountant
* Inventory Manager

## Lead Sources

* Facebook Ads
* Google Ads
* TikTok Ads
* Zalo Ads
* Website
* Landing Page
* Hotline
* Referral
* Collaborator
* Sale Self

## Tags

* Khách nóng
* Khách đầu tư
* Khách mua ở
* Cần vay ngân hàng
* Tài chính mạnh
* Khách chờ giá tốt
* Khách rác

---

# 28. GỢI Ý THỨ TỰ MIGRATION

1. Enable extensions
2. users
3. roles
4. permissions
5. role_permissions
6. user_roles
7. teams
8. team_members
9. lead_sources
10. customers
11. customer_contacts
12. customer_related_people
13. customer_demands
14. leads
15. tags
16. customer_tags
17. projects
18. property_owners
19. properties
20. property_owner_links
21. property_price_history
22. property_status_history
23. deals
24. deal_stage_history
25. deal_negotiations
26. deposits
27. contracts
28. payment_schedules
29. commissions
30. commission_splits
31. activities
32. tasks
33. appointments
34. site_visits
35. files
36. notifications
37. workflow_rules
38. workflow_executions
39. audit_logs
40. import_jobs
41. export_jobs
42. master_statuses
43. master_lost_reasons

---

# 29. EXTENSION CẦN BẬT

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

# 30. GHI CHÚ CHO CODEX

Khi code hệ thống:

1. Không hard delete dữ liệu quan trọng.
2. Không cho sale xem dữ liệu không thuộc quyền.
3. Không cho tạo khách trùng số điện thoại.
4. Mọi thay đổi trạng thái phải có audit log.
5. Mọi deal phải gắn với khách hàng.
6. Property có thể chưa gắn deal.
7. Deal có thể chưa gắn property ở giai đoạn đầu.
8. Báo cáo phải lấy dữ liệu theo quyền người dùng.
9. Import Excel phải kiểm tra dữ liệu trước khi ghi vào database.
10. Export Excel phải theo permission.
11. Tất cả tiền dùng NUMERIC, không dùng FLOAT.
12. Tất cả bảng lớn cần index theo trường lọc chính.
13. Thiết kế API phải hỗ trợ phân trang, tìm kiếm, lọc nâng cao.
14. Customer Timeline phải tự động ghi nhận các sự kiện quan trọng.
15. Workflow Engine phải chạy sau các event quan trọng như tạo lead, đổi trạng thái, quá hạn task.
