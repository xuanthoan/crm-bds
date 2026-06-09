import{apiRequest}from'../../services/apiClient';import type{PropertyFilters,PropertyPayload,PropertyUnit}from'./types';
const query=(p:Record<string,unknown>)=>{const s=new URLSearchParams();Object.entries(p).forEach(([k,v])=>{if(v!==undefined&&v!==null&&v!=='')s.set(k,String(v))});return s.toString()};
export const listProperties=(filters:PropertyFilters={})=>apiRequest<PropertyUnit[]>(`/properties?${query(filters)}`);
export const getProperty=(id:string)=>apiRequest<PropertyUnit>(`/properties/${id}`);
export const createProperty=(payload:PropertyPayload)=>apiRequest<PropertyUnit>('/properties',{method:'POST',body:JSON.stringify(payload)});
export const updateProperty=(id:string,payload:PropertyPayload)=>apiRequest<PropertyUnit>(`/properties/${id}`,{method:'PUT',body:JSON.stringify(payload)});
export const changePropertyStatus=(id:string,payload:{inventory_status:string;note?:string|null})=>apiRequest<PropertyUnit>(`/properties/${id}/status`,{method:'POST',body:JSON.stringify(payload)});
export const updatePropertyPrices=(id:string,payload:Record<string,number|string|null>)=>apiRequest<PropertyUnit>(`/properties/${id}/prices`,{method:'POST',body:JSON.stringify(payload)});
export const deleteProperty=(id:string)=>apiRequest<null>(`/properties/${id}`,{method:'DELETE'});
