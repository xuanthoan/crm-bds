import { apiRequest } from '../../services/apiClient';
export type AuditLog={id:string;actor_id?:string|null;actor_name?:string|null;actor_email?:string|null;action:string;action_label?:string;module:string;module_label?:string;entity_type:string;entity_id:string;entity_label?:string|null;entity_display?:string|null;before_data?:Record<string,unknown>|null;after_data?:Record<string,unknown>|null;changed_fields?:Record<string,{before:unknown;after:unknown}>|null;description?:string|null;reason?:string|null;ip_address?:string|null;user_agent?:string|null;created_at:string};
export type AuditLogList={items:AuditLog[];total:number;page:number;page_size:number};
const qs=(f:Record<string,string|number|undefined>)=>new URLSearchParams(Object.entries(f).filter(([,v])=>v!==undefined&&v!==''&&v!==null).map(([k,v])=>[k,String(v)])).toString();
export const listAuditLogs=(f:Record<string,string|number|undefined>)=>apiRequest<AuditLogList>(`/api/v1/audit-logs?${qs(f)}`);
export const getAuditLog=(id:string)=>apiRequest<AuditLog>(`/api/v1/audit-logs/${id}`);
export const listEntityAuditLogs=(entityType:string,entityId:string,page=1,pageSize=20)=>apiRequest<AuditLogList>(`/api/v1/audit-logs/entity/${entityType}/${entityId}?${qs({page,page_size:pageSize})}`);
