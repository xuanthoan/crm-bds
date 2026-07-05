import { useEffect, useMemo, useState } from 'react';
import { Modal } from '../../components/Modal';
import { GuideBox } from '../../components/help/GuideBox';
import { formatApiError } from '../../services/apiClient';
import { listAuditLogs, type AuditLog } from './api';
import { ENTITY_TYPE_LABELS, inferModuleFromAction, labelAction, labelField, labelModule } from './constants';

const initialFilters: Record<string,string> = { page:'1', page_size:'20' };
const fmt=(v?:string|null)=>v?new Date(v).toLocaleString('vi-VN'):'—';
const json=(v:unknown)=>JSON.stringify(v??{},null,2);
const isBlank=(v:unknown)=>v===null||v===undefined||String(v).trim()===''||String(v).trim().toLowerCase()==='null'||String(v).trim().toLowerCase()==='undefined';
const show=(v:unknown)=>isBlank(v)?'—':String(v);
const actionOpts=['','auth.login','auth.logout','create','update','approve','cancel','hold','record_received','mark_paid','create_voucher','cancel_voucher','update_policy','contracts.create','contracts.status_change','bookings.create','bookings.status_change','deals.create_from_booking','inventory.properties.create'];
const moduleOpts=['','auth','audit_log','sales_commission','company_commission','commission_payment_voucher','commission_payout_policy','commission_reconciliation_report','contracts','bookings','deals','payments','receipts','invoices','leads','customers','tasks','inventory.properties','property_units','system'];

function actorName(item: AuditLog){
  if(!isBlank(item.actor_name)) return String(item.actor_name);
  if(!isBlank(item.actor_email)) return String(item.actor_email);
  if(String(item.entity_type||'')==='user' && !isBlank(item.entity_label)) return String(item.entity_label);
  if(!isBlank(item.actor_id)) return 'Người dùng';
  return 'Hệ thống';
}
function displayModule(item: AuditLog){ return labelModule(inferModuleFromAction(item.module, item.action)); }
function entityDisplay(item: AuditLog){
  if(!isBlank(item.entity_display)) return String(item.entity_display);
  if(!isBlank(item.entity_label)) return String(item.entity_label);
  const type = !isBlank(item.entity_type) ? String(item.entity_type) : '';
  const id = !isBlank(item.entity_id) ? String(item.entity_id) : '';
  if(type && id) return `${ENTITY_TYPE_LABELS[type] || labelModule(type)} ${id}`;
  if(id) return id;
  return 'Không xác định';
}
function changedEntries(item: AuditLog){ return Object.entries(item.changed_fields || {}).filter(([,v])=>v); }

export function AuditLogsPage(){
 const [draft,setDraft]=useState<Record<string,string>>(initialFilters); const [filters,setFilters]=useState<Record<string,string>>(initialFilters); const [items,setItems]=useState<AuditLog[]>([]); const [total,setTotal]=useState(0); const [selected,setSelected]=useState<AuditLog|null>(null); const [loading,setLoading]=useState(false); const [error,setError]=useState<string|null>(null);
 const page=Number(filters.page||1), pageSize=Number(filters.page_size||20);
 const totalPages=useMemo(()=>Math.max(1,Math.ceil(total/pageSize)),[total,pageSize]);
 const setDraftValue=(k:string,v:string)=>setDraft(f=>({...f,[k]:v}));
 const apply=()=>setFilters({...draft,page:'1'});
 const reset=()=>{setDraft(initialFilters);setFilters(initialFilters);};
 const setPage=(next:number)=>setFilters(f=>({...f,page:String(next)}));
 useEffect(()=>{let active=true; setLoading(true); setError(null); listAuditLogs(filters).then(r=>{if(!active)return; setItems(r.data.items||[]);setTotal(r.data.total||0)}).catch(err=>{if(!active)return; setItems([]);setTotal(0);setError(formatApiError(err,'Không tải được lịch sử thao tác.').join('\n'))}).finally(()=>{if(active)setLoading(false)}); return()=>{active=false};},[filters]);
 return <div className="audit-logs-page"><header className="page-header"><div><h1>Lịch sử thao tác</h1><p>Theo dõi ai đã thao tác gì, lúc nào, trên module nào và dữ liệu thay đổi ra sao.</p></div></header><GuideBox title="Cách dùng lịch sử thao tác" items={['Dùng để kiểm tra ai đã tạo, sửa, duyệt, hủy hoặc xác nhận dữ liệu quan trọng.','Có thể lọc theo người thao tác, module, hành động và thời gian.','Với các thao tác cập nhật, hệ thống hiển thị dữ liệu trước/sau nếu có.']} />
 <section className="card audit-filter-card"><h2>Bộ lọc</h2><div className="audit-filter-grid"><label>Từ ngày<input type="date" value={draft.date_from||''} onChange={e=>setDraftValue('date_from',e.target.value)}/></label><label>Đến ngày<input type="date" value={draft.date_to||''} onChange={e=>setDraftValue('date_to',e.target.value)}/></label><label>Người thao tác<input value={draft.actor_id||''} onChange={e=>setDraftValue('actor_id',e.target.value)} title="ID hoặc email người thao tác" placeholder="ID, tên hoặc email người thao tác"/></label><label>Module<select value={draft.module||''} onChange={e=>setDraftValue('module',e.target.value)}>{moduleOpts.map(m=><option key={m} value={m}>{m?labelModule(m):'Tất cả'}</option>)}</select></label><label>Hành động<select value={draft.action||''} onChange={e=>setDraftValue('action',e.target.value)}>{actionOpts.map(a=><option key={a} value={a}>{a?labelAction(a):'Tất cả'}</option>)}</select></label><label>Loại đối tượng<input value={draft.entity_type||''} onChange={e=>setDraftValue('entity_type',e.target.value)} placeholder="VD: contract, booking, deal, user" title="Chỉ nhập loại đối tượng, không nhập tên người thao tác"/></label><label>Mã đối tượng<input value={draft.entity_id||''} onChange={e=>setDraftValue('entity_id',e.target.value)} placeholder="VD: HD-000066, BK-000107, DL-000086 hoặc UUID"/></label><label>Từ khóa<input value={draft.q||''} onChange={e=>setDraftValue('q',e.target.value)} title="Tìm người thao tác, mô tả, mã đối tượng" placeholder="Tìm theo người thao tác, hành động, module, mã đối tượng, mô tả..."/></label></div><div className="audit-filter-actions"><button type="button" onClick={apply}>Lọc</button><button type="button" className="secondary-button" onClick={reset}>Xóa lọc</button></div></section>
 <section className="card audit-table-wrap">{error&&<p className="error-message">{error}</p>}<table><thead><tr><th>Thời gian</th><th>Người thao tác</th><th>Module</th><th>Hành động</th><th>Đối tượng</th><th>Mô tả</th><th>Lý do</th><th>Chi tiết</th></tr></thead><tbody>{items.map(i=><tr key={i.id}><td>{fmt(i.created_at)}</td><td><strong>{actorName(i)}</strong>{!isBlank(i.actor_email)&&actorName(i)!==i.actor_email?<><br/><small>{i.actor_email}</small></>:null}</td><td><span className="audit-module-badge">{displayModule(i)}</span></td><td><span className="audit-action-badge">{labelAction(i.action)}</span></td><td>{entityDisplay(i)}</td><td>{show(i.description)}</td><td>{show(i.reason)}</td><td><button className="secondary-button audit-detail-button" onClick={()=>setSelected(i)}>Xem chi tiết</button></td></tr>)}</tbody></table>{loading&&<p>Đang tải...</p>}<div className="pagination"><button disabled={page<=1} onClick={()=>setPage(page-1)}>Trước</button><span>Trang {page} / {totalPages} · {total} dòng</span><button disabled={page>=totalPages} onClick={()=>setPage(page+1)}>Sau</button></div></section>
 {selected&&<Modal title="Chi tiết lịch sử thao tác" onClose={()=>setSelected(null)}><div className="modal-body audit-detail"><div className="audit-detail-summary"><p><strong>Thời gian</strong><span>{fmt(selected.created_at)}</span></p><p><strong>Người thao tác</strong><span>{actorName(selected)}</span></p><p><strong>Module</strong><span>{displayModule(selected)}</span></p><p><strong>Hành động</strong><span>{labelAction(selected.action)}</span></p><p><strong>Đối tượng</strong><span>{entityDisplay(selected)}</span></p><p><strong>Mô tả</strong><span>{show(selected.description)}</span></p><p><strong>Lý do</strong><span>{show(selected.reason)}</span></p><p><strong>IP/User agent</strong><span>{show(selected.ip_address)} / {show(selected.user_agent)}</span></p></div><h3>Trường thay đổi</h3>{changedEntries(selected).length?<div className="audit-changed-list">{changedEntries(selected).map(([k,v])=><article key={k}><strong>{labelField(k)}</strong><div><span>Trước: {show(v.before)}</span><span>Sau: {show(v.after)}</span></div></article>)}</div>:<p>Không có dữ liệu thay đổi.</p>}<details><summary>Dữ liệu trước</summary><pre>{json(selected.before_data)}</pre></details><details><summary>Dữ liệu sau</summary><pre>{json(selected.after_data)}</pre></details></div></Modal>}
 </div>;
}
