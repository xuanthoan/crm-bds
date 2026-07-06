import {useEffect,useMemo,useRef,useState} from 'react';

export type UserSelectUser={id:string;full_name?:string|null;name?:string|null;email?:string|null};

type BaseProps={label:string;users:UserSelectUser[];placeholder?:string;disabledIds?:string[];emptyText?:string;required?:boolean;hint?:string};
type SingleProps=BaseProps&{multiple?:false;value:string;onChange:(value:string)=>void};
type MultiProps=BaseProps&{multiple:true;value:string[];onChange:(value:string[])=>void;lockedIds?:string[];lockedText?:string};
type Props=SingleProps|MultiProps;

const displayName=(user:UserSelectUser)=>user.full_name||user.name||user.email||'Không rõ tên';
const searchText=(user:UserSelectUser)=>`${displayName(user)} ${user.email||''}`.toLowerCase();
const unique=(values:string[])=>Array.from(new Set(values.filter(Boolean)));

export function UserSelect(props:Props){
  const {label,users,placeholder='Tìm theo tên hoặc email',disabledIds=[],emptyText='Không tìm thấy nhân viên phù hợp',required,hint}=props;
  const [open,setOpen]=useState(false);
  const [search,setSearch]=useState('');
  const rootRef=useRef<HTMLDivElement|null>(null);
  const safeUsers=Array.isArray(users)?users:[];
  const disabledSet=useMemo(()=>new Set(disabledIds),[disabledIds]);
  const lockedSet=useMemo(()=>new Set(props.multiple?(props.lockedIds||[]):[]),[props]);
  const selectedIds=props.multiple?unique(props.value||[]):unique([props.value]);
  const selectedUsers=selectedIds.map(id=>safeUsers.find(user=>user.id===id)).filter(Boolean) as UserSelectUser[];
  const selectedSingle=props.multiple?null:selectedUsers[0]||null;
  const filtered=useMemo(()=>{const term=search.trim().toLowerCase();return term?safeUsers.filter(user=>searchText(user).includes(term)):safeUsers;},[safeUsers,search]);
  useEffect(()=>{const onDoc=(event:MouseEvent)=>{if(rootRef.current&&!rootRef.current.contains(event.target as Node))setOpen(false)};document.addEventListener('mousedown',onDoc);return()=>document.removeEventListener('mousedown',onDoc)},[]);
  function choose(user:UserSelectUser){if(disabledSet.has(user.id))return;if(props.multiple){const current=unique(props.value||[]);props.onChange(current.includes(user.id)?current.filter(id=>id!==user.id):[...current,user.id]);setSearch('');return}props.onChange(user.id);setSearch('');setOpen(false)}
  function remove(id:string){if(!props.multiple||lockedSet.has(id))return;props.onChange(unique(props.value||[]).filter(value=>value!==id))}
  const singleValue=open?search:(selectedSingle?`${displayName(selectedSingle)}${selectedSingle.email?` - ${selectedSingle.email}`:''}`:'');
  return <div className="user-select-field" ref={rootRef} data-multiple={props.multiple?'true':'false'}><div className="user-select-label">{label}{required&&<span aria-hidden="true"> *</span>}</div><div className="user-select-control" onClick={()=>setOpen(true)}>{props.multiple?<><div className="user-select-chips">{selectedUsers.map(user=><span className="user-select-chip" key={user.id}>{displayName(user)}<button type="button" disabled={lockedSet.has(user.id)} title={lockedSet.has(user.id)?(props.lockedText||'Không thể bỏ người này'):undefined} onClick={event=>{event.stopPropagation();remove(user.id)}}>×</button></span>)}<input value={search} placeholder={selectedUsers.length?'Tìm thêm nhân viên':placeholder} onFocus={()=>setOpen(true)} onChange={event=>{setSearch(event.target.value);setOpen(true)}}/></div></>:<input value={singleValue} required={required} placeholder={placeholder} onFocus={()=>{setOpen(true);setSearch('')}} onChange={event=>{setSearch(event.target.value);setOpen(true)}}/>}<button type="button" className="user-select-toggle" onClick={event=>{event.stopPropagation();setOpen(value=>!value)}}>⌄</button></div>{hint&&<small className="field-hint">{hint}</small>}{open&&<div className="user-select-menu">{filtered.length?filtered.map(user=>{const disabled=disabledSet.has(user.id);const selected=selectedIds.includes(user.id);return <button type="button" key={user.id} className="user-select-option" disabled={disabled} aria-selected={selected} onClick={()=>choose(user)}><span>{displayName(user)}</span><small>{user.email||'Chưa có email'}</small>{disabled&&<em>Đã có vai trò cao hơn</em>}</button>}):<p className="user-select-empty">{emptyText}</p>}</div>}</div>;
}
