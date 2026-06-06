from pydantic import BaseModel
class MyWorkSummary(BaseModel):
    tasks_today: int; tasks_overdue: int; appointments_today: int; appointments_upcoming: int; leads_need_follow_up: int; completed_tasks_today: int
class TeamWorkSummary(BaseModel):
    team_tasks_today: int; team_tasks_overdue: int; team_appointments_today: int; team_leads_need_follow_up: int; per_user_summary: list[dict]
