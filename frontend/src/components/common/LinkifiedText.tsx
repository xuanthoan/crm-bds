import type {ReactNode} from 'react';
const URL_RE=/https?:\/\/[^\s<]+/g;
const trimTrailing=(url:string)=>{let tail='';while(/[.,!?;:)]$/.test(url)){tail=url.slice(-1)+tail;url=url.slice(0,-1)}return{url,tail}};
export function LinkifiedText({text}:{text:string}){const nodes:ReactNode[]=[];let last=0;for(const match of text.matchAll(URL_RE)){const raw=match[0];const start=match.index??0;if(start>last)nodes.push(text.slice(last,start));const {url,tail}=trimTrailing(raw);nodes.push(<a key={`${start}-${url}`} href={url} target="_blank" rel="noopener noreferrer">{url}</a>);if(tail)nodes.push(tail);last=start+raw.length}if(last<text.length)nodes.push(text.slice(last));return <span className="linkified-text">{nodes}</span>}
