import { helpSections } from './helpContent';

const anchor = (title: string) => title.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export function HelpPage() {
  return <section className="help-page"><header className="page-header"><div><h1>Hướng dẫn sử dụng</h1><p>Hướng dẫn nhanh các luồng nghiệp vụ chính trong CRM bất động sản.</p></div></header>
    <nav className="help-toc" aria-label="Mục lục hướng dẫn">{helpSections.map((section) => <a key={section.title} href={`#${anchor(section.title)}`}>{section.title}</a>)}</nav>
    <div className="help-section-grid">{helpSections.map((section) => <article className="help-card" id={anchor(section.title)} key={section.title}><h2>{section.title}</h2>{section.items.length > 0 && <ul>{section.items.map((item) => <li key={item}>{item}</li>)}</ul>}{section.groups?.map((group) => <div className="help-subgroup" key={group.title}><h3>{group.title}</h3><ul>{group.items.map((item) => <li key={item}>{item}</li>)}</ul></div>)}</article>)}</div>
  </section>;
}
