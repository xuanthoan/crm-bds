import { useEffect, useState } from 'react';
import { listEntityAuditLogs, type AuditLog } from '../../features/auditLogs/api';
import { labelAction } from '../../features/auditLogs/constants';

const fmt=(v:string)=>new Date(v).toLocaleString('vi-VN');
export function ActivityTimeline({entityType,entityId,title='Lịch sử thao tác hệ thống',compact=false}:{entityType:string;entityId:string;title?:string;compact?:boolean}){
 const [items,setItems]=useState<AuditLog[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(false);
 useEffect(()=>{let alive=true; setLoading(true); listEntityAuditLogs(entityType,entityId,1,compact?5:20).then(r=>{if(alive){setItems(r.data.items);setError(false)}}).catch(()=>{if(alive)setError(true)}).finally(()=>{if(alive)setLoading(false)}); return()=>{alive=false};},[entityType,entityId,compact]);
 return <section className="card activity-timeline"><h2>{title}</h2>{loading&&<p>Đang tải lịch sử thao tác...</p>}{error&&<p className="form-error">Không tải được lịch sử thao tác.</p>}{!loading&&!error&&items.length===0&&<p>Chưa có lịch sử thao tác hệ thống.</p>}<div className="audit-timeline-list">{items.map(i=><article key={i.id} className="audit-timeline-item"><div><strong>{labelAction(i.action)}</strong><span>{fmt(i.created_at)}</span></div><p>{i.description || 'Cập nhật dữ liệu'}</p><small>{i.actor_name || i.actor_email || 'Hệ thống'}{i.changed_fields?` · ${Object.keys(i.changed_fields).slice(0,3).join(', ')}`:''}</small></article>)}</div></section>;
}
