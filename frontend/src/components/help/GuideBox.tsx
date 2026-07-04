export function GuideBox({ title, description, items }: { title: string; description?: string; items: string[] }) {
  return <aside className="guide-box"><div><strong>{title}</strong>{description && <p>{description}</p>}</div><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></aside>;
}
