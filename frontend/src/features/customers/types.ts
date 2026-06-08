export type CustomerUser = { id: string; full_name: string; email: string };
export type CustomerType = 'individual' | 'company' | 'investor' | 'agent' | 'other';
export type CustomerStatus = 'active' | 'inactive' | 'potential' | 'vip' | 'blacklisted';
export type CustomerActivityType = 'note' | 'call' | 'zalo' | 'email' | 'meeting' | 'conversion' | 'status_change' | 'owner_change' | 'other';
export type CustomerActivity = { id:string; activity_type:CustomerActivityType; title:string; content:string|null; old_value:string|null; new_value:string|null; user:CustomerUser|null; created_at:string };
export type SourceLead = { id:string; code:string; full_name:string; status:string };
export type RelatedTask = { id:string; title:string; status:string; priority:string; due_at:string; assigned_to:CustomerUser|null };
export type RelatedAppointment = { id:string; title:string; status:string; appointment_type:string; start_at:string; location:string|null; assigned_to:CustomerUser|null };
export type Customer = {
 id:string; customer_code:string; full_name:string; customer_type:CustomerType; status:CustomerStatus;
 primary_phone:string; secondary_phone:string|null; email:string|null; zalo:string|null; facebook:string|null; address:string|null;
 source:string|null; source_lead_id:string|null; source_note:string|null; interested_project:string|null; interested_area:string|null;
 budget_min:string|number|null; budget_max:string|number|null; bedroom_count:number|null; area_min:string|number|null; area_max:string|number|null; purpose:string|null;
 owner:CustomerUser|null; created_by:CustomerUser; first_contact_at:string|null; last_contact_at:string|null; next_follow_up_at:string|null; converted_at:string|null;
 note:string|null; created_at:string; updated_at:string; source_lead:SourceLead|null; activities?:CustomerActivity[]; lead_activities?:any[]; related_tasks?:RelatedTask[]; related_appointments?:RelatedAppointment[];
};
export type CustomerPayload = Partial<Omit<Customer,'id'|'customer_code'|'owner'|'created_by'|'created_at'|'updated_at'|'source_lead'|'activities'|'lead_activities'|'related_tasks'|'related_appointments'>> & { full_name:string; primary_phone:string; owner_id?:string|null };
