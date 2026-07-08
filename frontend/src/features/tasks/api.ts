import {apiRequest} from '../../services/apiClient'; import type {LeadTask,TaskComment,TaskPayload,TaskRelatedLink,TaskStatus,TaskTimelineEvent} from './types';
export type TaskAssignee={id:string;full_name:string;email:string};
export type TaskFilters={page?:number;page_size?:number;q?:string;status?:string;task_type?:string;priority?:string;assigned_user_id?:string;due_from?:string;due_to?:string;lead_id?:string;related_lead_id?:string;related_customer_id?:string;related_booking_id?:string;related_deal_id?:string;related_contract_id?:string;overdue?:boolean;today?:boolean};
function qs(filters:TaskFilters={}){const p=new URLSearchParams();Object.entries({page:1,page_size:20,...filters}).forEach(([k,v])=>{if(v!==undefined&&v!==''&&v!==false&&!['today','overdue'].includes(k))p.set(k,String(v))});return p.toString()}
export function listTasks(filters:TaskFilters={}){const path=filters.today?`/api/v1/tasks/today?${qs(filters)}`:filters.overdue?`/api/v1/tasks/overdue?${qs(filters)}`:`/api/v1/tasks?${qs(filters)}`;return apiRequest<LeadTask[]>(path)}
export const createTask=(p:TaskPayload)=>apiRequest<LeadTask>('/api/v1/tasks',{method:'POST',body:JSON.stringify(p)}); export const updateTask=(id:string,p:Partial<TaskPayload>)=>apiRequest<LeadTask>(`/api/v1/tasks/${id}`,{method:'PUT',body:JSON.stringify(p)}); export const updateTaskStatus=(id:string,status:TaskStatus,note?:string)=>apiRequest<LeadTask>(`/api/v1/tasks/${id}/status`,{method:'POST',body:JSON.stringify({status,note})}); export const completeTask=(id:string,note?:string)=>apiRequest<LeadTask>(`/api/v1/tasks/${id}/complete`,{method:'POST',body:JSON.stringify({note})}); export const cancelTask=(id:string,reason?:string)=>apiRequest<LeadTask>(`/api/v1/tasks/${id}/cancel`,{method:'POST',body:JSON.stringify({reason})});

export const listTaskAssignees=()=>apiRequest<TaskAssignee[]>('/api/v1/tasks/assignees');

export const listTaskComments=(id:string)=>apiRequest<TaskComment[]>(`/api/v1/tasks/${id}/comments`);
export const createTaskComment=(id:string,p:{content:string})=>apiRequest<TaskComment>(`/api/v1/tasks/${id}/comments`,{method:'POST',body:JSON.stringify(p)});
export const listTaskLinks=(id:string)=>apiRequest<TaskRelatedLink[]>(`/api/v1/tasks/${id}/links`);
export const createTaskLink=(id:string,p:{title:string;url:string;note?:string})=>apiRequest<TaskRelatedLink>(`/api/v1/tasks/${id}/links`,{method:'POST',body:JSON.stringify(p)});
export const deleteTaskLink=(taskId:string,linkId:string)=>apiRequest<{deleted:boolean}>(`/api/v1/tasks/${taskId}/links/${linkId}`,{method:'DELETE'});
export const listTaskTimeline=(id:string)=>apiRequest<TaskTimelineEvent[]>(`/api/v1/tasks/${id}/timeline`);
