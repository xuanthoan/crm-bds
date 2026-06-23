-- Sprint 14 Task & Notification Engine tables.
CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY,
  task_code VARCHAR(30) UNIQUE NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  task_type VARCHAR(40) NOT NULL,
  priority VARCHAR(20) NOT NULL DEFAULT 'medium',
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  due_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  assigned_user_id UUID REFERENCES users(id),
  created_by_id UUID REFERENCES users(id),
  related_customer_id UUID REFERENCES customers(id),
  related_lead_id UUID REFERENCES leads(id),
  related_booking_id UUID REFERENCES bookings(id),
  related_deal_id UUID REFERENCES deals(id),
  related_contract_id UUID REFERENCES contracts(id),
  related_property_unit_id UUID REFERENCES property_units(id),
  auto_generated BOOLEAN NOT NULL DEFAULT FALSE,
  source_event VARCHAR(80),
  note TEXT,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tasks_assigned_user_id ON tasks(assigned_user_id);
CREATE INDEX IF NOT EXISTS ix_tasks_due_at ON tasks(due_at);
CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status);
CREATE TABLE IF NOT EXISTS task_activities (
  id UUID PRIMARY KEY,
  task_id UUID NOT NULL REFERENCES tasks(id),
  activity_type VARCHAR(40) NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT,
  old_value VARCHAR(255),
  new_value VARCHAR(255),
  actor_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY,
  recipient_user_id UUID NOT NULL REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  content TEXT,
  notification_type VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'unread',
  related_task_id UUID REFERENCES tasks(id),
  related_booking_id UUID REFERENCES bookings(id),
  related_deal_id UUID REFERENCES deals(id),
  related_contract_id UUID REFERENCES contracts(id),
  related_customer_id UUID REFERENCES customers(id),
  related_property_unit_id UUID REFERENCES property_units(id),
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_notifications_recipient_user_id ON notifications(recipient_user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_read_at ON notifications(read_at);
