export type UserSummary = { id: string; full_name: string; email: string };
export type LeadActivity = { id: string; activity_type: string; title: string | null; content: string; old_value: string | null; new_value: string | null; user: UserSummary; created_at: string };
export type Lead = {
  id: string; code: string; full_name: string; phone_primary: string; phone_secondary: string | null;
  zalo?: string | null; facebook?: string | null; email?: string | null; address?: string | null; source: string | null;
  project_interest: string | null; location_interest?: string | null; budget_min: number | null; budget_max: number | null;
  bedroom_need?: number | null; area_min?: number | null; area_max?: number | null; note?: string | null;
  status: string; priority: string; owner: UserSummary | null; created_by?: UserSummary; assigned_by?: UserSummary | null;
  assigned_at?: string | null; last_contact_at?: string | null; next_follow_up_at: string | null;
  lost_reason?: string | null; created_at: string; updated_at: string; activities?: LeadActivity[];
};
export type LeadPayload = Partial<Omit<Lead, 'id' | 'code' | 'owner' | 'created_by' | 'assigned_by' | 'activities' | 'created_at' | 'updated_at'>> & { full_name: string; phone_primary: string; owner_id?: string | null };
