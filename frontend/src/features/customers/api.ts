import { apiRequest } from '../../services/apiClient';
import type { Customer, CustomerActivity, CustomerActivityType, CustomerPayload, CustomerStatus, CustomerType, CustomerUser } from './types';
export type CustomerFilters={page?:number;page_size?:number;search?:string;status?:string;customer_type?:string;owner_id?:string;source?:string;project?:string;next_follow_up_from?:string;next_follow_up_to?:string};
export function listCustomers(filters:CustomerFilters={}){const p=new URLSearchParams();p.set('page',String(filters.page??1));p.set('page_size',String(filters.page_size??20));Object.entries(filters).forEach(([k,v])=>{if(v!==undefined&&v!==''&&k!=='page'&&k!=='page_size')p.set(k,String(v));});return apiRequest<Customer[]>(`/api/v1/customers?${p}`);}
export const getCustomer=(id:string)=>apiRequest<Customer>(`/api/v1/customers/${id}`);
export const createCustomer=(payload:CustomerPayload)=>apiRequest<Customer>('/api/v1/customers',{method:'POST',body:JSON.stringify(payload)});
export const updateCustomer=(id:string,payload:Partial<CustomerPayload>)=>apiRequest<Customer>(`/api/v1/customers/${id}`,{method:'PUT',body:JSON.stringify(payload)});
export const updateCustomerStatus=(id:string,status:CustomerStatus,note?:string)=>apiRequest<Customer>(`/api/v1/customers/${id}/status`,{method:'POST',body:JSON.stringify({status,note})});
export const updateCustomerOwner=(id:string,owner_id:string,note?:string)=>apiRequest<Customer>(`/api/v1/customers/${id}/owner`,{method:'POST',body:JSON.stringify({owner_id,note})});
export const addCustomerActivity=(id:string,payload:{activity_type:CustomerActivityType;title?:string;content:string})=>apiRequest<CustomerActivity>(`/api/v1/customers/${id}/activities`,{method:'POST',body:JSON.stringify(payload)});
export const deleteCustomer=(id:string)=>apiRequest<null>(`/api/v1/customers/${id}`,{method:'DELETE'});
export const listCustomerAssignees=()=>apiRequest<CustomerUser[]>('/api/v1/customers/assignees');
export const convertLead=(leadId:string,payload:{customer_type:CustomerType;status:CustomerStatus;owner_id?:string|null;note?:string})=>apiRequest<{customer:Customer;lead:any;message:string}>(`/api/v1/leads/${leadId}/convert`,{method:'POST',body:JSON.stringify({...payload,merge_strategy:'reject_existing'})});
