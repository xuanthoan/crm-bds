import { useMemo, useState } from 'react';
import { glossaryTerms } from './helpContent';

const groups = ['Tất cả', ...Array.from(new Set(glossaryTerms.map((term) => term.group)))];

export function GlossaryPage() {
  const [query, setQuery] = useState('');
  const [group, setGroup] = useState('Tất cả');
  const terms = useMemo(() => {
    const q = query.trim().toLowerCase();
    return glossaryTerms.filter((term) => (group === 'Tất cả' || term.group === group) && (!q || [term.term, term.group, term.description, term.modules?.join(' ')].join(' ').toLowerCase().includes(q)));
  }, [query, group]);
  return <section className="help-page glossary-page"><header className="page-header"><div><h1>Từ điển nghiệp vụ</h1><p>Giải thích các thuật ngữ thường gặp trong hệ thống CRM bất động sản.</p></div></header>
    <div className="glossary-controls"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm thuật ngữ, nhóm, mô tả..." aria-label="Tìm kiếm thuật ngữ" /><select value={group} onChange={(event) => setGroup(event.target.value)} aria-label="Lọc nhóm thuật ngữ">{groups.map((name) => <option key={name} value={name}>{name}</option>)}</select></div>
    <div className="glossary-count">Đang hiển thị {terms.length}/{glossaryTerms.length} thuật ngữ.</div>
    {terms.length ? <div className="glossary-grid">{terms.map((term) => <article className="glossary-card" key={term.term}><div className="glossary-card-heading"><h2>{term.term}</h2><span>{term.group}</span></div><p>{term.description}</p>{term.example && <p><strong>Ví dụ:</strong> {term.example}</p>}{term.modules?.length ? <small>Module liên quan: {term.modules.join(', ')}</small> : null}</article>)}</div> : <p className="empty-state">Không tìm thấy thuật ngữ phù hợp.</p>}
  </section>;
}
