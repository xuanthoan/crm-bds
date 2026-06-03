export function CustomersPage() {
  return <PlaceholderPage title="Customers" />;
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <section className="rounded-2xl bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">Placeholder</p>
      <h2 className="mt-3 text-3xl font-bold text-slate-950">{title}</h2>
      <p className="mt-4 text-slate-600">This page is protected, but the {title.toLowerCase()} module is not implemented in Sprint 2.</p>
    </section>
  );
}
