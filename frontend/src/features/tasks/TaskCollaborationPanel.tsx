import {useEffect,useMemo,useState} from 'react';
import {formatApiError} from '../../services/apiClient';
import {LinkifiedText} from '../../components/common/LinkifiedText';
import {createTaskComment,createTaskLink,deleteTaskLink,listTaskComments,listTaskLinks,listTaskTimeline} from './api';
import type {LeadTask,TaskComment,TaskRelatedLink,TaskTimelineEvent} from './types';

type TabKey='comments'|'links'|'timeline';
const tabs:Array<{key:TabKey;label:string}>=[{key:'comments',label:'Bình luận'},{key:'links',label:'Link liên quan'},{key:'timeline',label:'Dòng thời gian'}];
const dt=(v:string)=>new Intl.DateTimeFormat('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(v));
const isHttp=(v:string)=>v.startsWith('http://')||v.startsWith('https://');
const initials=(name?:string|null)=>{const parts=(name||'ND').trim().split(/\s+/).slice(-2);return parts.map(x=>x[0]?.toUpperCase()).join('')||'ND'};
const uuidLike=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const prettyValue=(value?:string|null)=>{if(!value||uuidLike.test(value)||value.includes('{')||value.includes('['))return '';if(value.includes(',')){const parts=value.split(',').map(x=>x.trim()).filter(x=>x&&!uuidLike.test(x));return parts.length?parts.join(', '):''}return value};
function ValueChange({event}:{event:TaskTimelineEvent}){const oldValue=prettyValue(event.old_value);const newValue=prettyValue(event.new_value);if(!oldValue&&!newValue)return null;return <div className="task-timeline-change">{oldValue&&<span><b>Từ:</b> {oldValue}</span>}{newValue&&<span><b>Sang:</b> {newValue}</span>}</div>}

export function TaskCollaborationPanel({task}:{task:LeadTask}){
  const [activeTab,setActiveTab]=useState<TabKey>('comments');
  const [comments,setComments]=useState<TaskComment[]>([]);
  const [links,setLinks]=useState<TaskRelatedLink[]>([]);
  const [timeline,setTimeline]=useState<TaskTimelineEvent[]>([]);
  const [comment,setComment]=useState('');
  const [link,setLink]=useState({title:'',url:'',note:''});
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [linkError,setLinkError]=useState('');
  const tabCounts=useMemo(()=>({comments:comments.length,links:links.length,timeline:timeline.length}),[comments.length,links.length,timeline.length]);
  const load=async()=>{setLoading(true);setError('');try{const [c,l,t]=await Promise.all([listTaskComments(task.id),listTaskLinks(task.id),listTaskTimeline(task.id)]);setComments(Array.isArray(c.data)?c.data:[]);setLinks(Array.isArray(l.data)?l.data:[]);setTimeline(Array.isArray(t.data)?t.data:[])}catch(e){setError(formatApiError(e,'Không tải được trao đổi công việc.').join('. '));setComments([]);setLinks([]);setTimeline([])}finally{setLoading(false)}};
  useEffect(()=>{void load()},[task.id]);
  const sendComment=async()=>{if(!comment.trim())return;await createTaskComment(task.id,{content:comment});setComment('');await load()};
  const addLink=async()=>{setLinkError('');if(!link.title.trim()){setLinkError('Tiêu đề link là bắt buộc.');return}if(!link.url.trim()){setLinkError('URL là bắt buộc.');return}if(!isHttp(link.url.trim())){setLinkError('URL phải bắt đầu bằng http:// hoặc https://.');return}await createTaskLink(task.id,{title:link.title.trim(),url:link.url.trim(),note:link.note.trim()});setLink({title:'',url:'',note:''});await load()};
  return <section className="task-collaboration-panel" aria-label="Trao đổi công việc">
    <div className="task-tabs" role="tablist" aria-label="Nội dung cộng tác">
      {tabs.map(tab=><button key={tab.key} type="button" role="tab" aria-selected={activeTab===tab.key} className={`task-tab ${activeTab===tab.key?'active':''}`} onClick={()=>setActiveTab(tab.key)}>{tab.label}<span>{tabCounts[tab.key]}</span></button>)}
    </div>
    {error&&<p className="form-error">{error}</p>}
    {activeTab==='comments'&&<div className="task-tab-panel" role="tabpanel">
      <header className="task-section-heading"><div><h3>Bình luận</h3><p>Trao đổi tiến độ, ghi chú xử lý và dán link tài liệu bên ngoài.</p></div></header>
      {loading&&<p className="task-muted">Đang tải bình luận...</p>}
      <div className="task-comment-list">
        {comments.length?comments.map(c=><article key={c.id} className="task-comment-card"><div className="task-avatar">{initials(c.author?.full_name)}</div><div className="task-comment-body"><header><strong className="task-comment-author">{c.author?.full_name??'Người dùng'}</strong><small className="task-comment-meta">{c.author?.email?`${c.author.email} · `:''}{dt(c.created_at)}</small></header><p className="task-comment-content comment-content"><LinkifiedText text={c.content}/></p></div></article>):!loading&&<div className="task-empty-state">Chưa có bình luận nào. Hãy ghi chú tiến độ xử lý công việc tại đây.</div>}
      </div>
      <div className="task-comment-composer"><textarea value={comment} onChange={e=>setComment(e.target.value)} placeholder="Nhập bình luận hoặc dán link tài liệu..." maxLength={5000}/><div><small>{comment.length}/5000</small><button type="button" onClick={()=>void sendComment()} disabled={!comment.trim()}>Gửi bình luận</button></div></div>
    </div>}
    {activeTab==='links'&&<div className="task-tab-panel" role="tabpanel">
      <header className="task-section-heading"><div><h3>Link liên quan</h3><p>Lưu đường dẫn Google Drive, hợp đồng online hoặc tài liệu cloud bên ngoài.</p></div></header>
      <div className="task-link-form"><div className="form-grid"><label>Tiêu đề link<input value={link.title} onChange={e=>setLink({...link,title:e.target.value})} placeholder="Ví dụ: Hồ sơ pháp lý"/></label><label>URL<input value={link.url} onChange={e=>setLink({...link,url:e.target.value})} placeholder="https://..."/></label><label className="full-span">Ghi chú<textarea value={link.note} onChange={e=>setLink({...link,note:e.target.value})} maxLength={2000} placeholder="Mô tả ngắn về link này"/></label></div>{linkError&&<p className="form-error">{linkError}</p>}<button type="button" onClick={()=>void addLink()}>Thêm link</button></div>
      <div className="task-link-list">{links.length?links.map(x=><article key={x.id} className="task-link-card"><div className="task-link-icon">↗</div><div className="task-link-main"><strong>{x.title}</strong><a href={x.url} target="_blank" rel="noopener noreferrer" title={x.url}>{x.url}</a>{x.note&&<p>{x.note}</p>}<small>{x.created_by?.full_name??'Người dùng'} · {dt(x.created_at)}</small></div><div className="task-link-actions"><a className="secondary-button" href={x.url} target="_blank" rel="noopener noreferrer">Mở link</a><button type="button" className="link-button danger-link" onClick={async()=>{await deleteTaskLink(task.id,x.id);await load()}}>Xóa</button></div></article>):<div className="task-empty-state">Chưa có link liên quan.</div>}</div>
    </div>}
    {activeTab==='timeline'&&<div className="task-tab-panel" role="tabpanel">
      <header className="task-section-heading"><div><h3>Dòng thời gian</h3><p>Theo dõi các mốc nghiệp vụ quan trọng của công việc.</p></div></header>
      <div className="task-timeline-list">{timeline.length?timeline.map(e=><article key={e.id} className="task-timeline-item"><div className="task-timeline-dot"/><div className="task-timeline-card"><strong>{e.title}</strong><small className="task-timeline-meta"><span className="task-timeline-actor">{e.actor?.full_name??'Hệ thống'}</span><span>{dt(e.created_at)}</span></small>{e.description&&!uuidLike.test(e.description)&&<p className="task-timeline-description"><LinkifiedText text={e.description}/></p>}<ValueChange event={e}/></div></article>):<div className="task-empty-state">Chưa có hoạt động nào.</div>}</div>
    </div>}
  </section>
}
