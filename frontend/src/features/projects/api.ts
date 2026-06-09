import {apiRequest,type ApiResponse} from '../../services/apiClient';import type{Project,ProjectFilters,ProjectPayload}from'./types';
const query=(p:Record<string,unknown>)=>{const s=new URLSearchParams();Object.entries(p).forEach(([k,v])=>{if(v!==undefined&&v!==null&&v!=='')s.set(k,String(v))});return s.toString()};
export const listProjects=(filters:ProjectFilters={})=>apiRequest<Project[]>(`/api/v1/projects?${query(filters)}`);
export const getProject=(id:string)=>apiRequest<Project>(`/api/v1/projects/${id}`);
export const createProject=(payload:ProjectPayload)=>apiRequest<Project>('/api/v1/projects',{method:'POST',body:JSON.stringify(payload)});
export const updateProject=(id:string,payload:ProjectPayload)=>apiRequest<Project>(`/api/v1/projects/${id}`,{method:'PUT',body:JSON.stringify(payload)});
export const deleteProject=(id:string)=>apiRequest<null>(`/api/v1/projects/${id}`,{method:'DELETE'});
