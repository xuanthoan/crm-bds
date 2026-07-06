export type PaginationItem = number | 'ellipsis';

type PaginationProps = {
  currentPage: number;
  totalPages: number;
  totalItems?: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
  itemLabel?: string;
  className?: string;
};

export function getPaginationItems(currentPage: number, totalPages: number): PaginationItem[] {
  const safeTotal = Math.max(1, Math.floor(Number(totalPages) || 1));
  const safeCurrent = Math.min(Math.max(1, Math.floor(Number(currentPage) || 1)), safeTotal);
  if (safeTotal <= 7) return Array.from({ length: safeTotal }, (_, index) => index + 1);
  const pages = new Set<number>([1, safeTotal]);
  let start = Math.max(2, safeCurrent - 2);
  let end = Math.min(safeTotal - 1, safeCurrent + 2);
  if (safeCurrent <= 4) { start = 2; end = 5; }
  if (safeCurrent >= safeTotal - 3) { start = safeTotal - 4; end = safeTotal - 1; }
  for (let page = start; page <= end; page += 1) pages.add(page);
  const sorted = Array.from(pages).sort((a, b) => a - b);
  return sorted.flatMap((page, index) => {
    const previous = sorted[index - 1];
    return previous && page - previous > 1 ? ['ellipsis' as const, page] : [page];
  });
}

export function Pagination({ currentPage, totalPages, totalItems, onPageChange, loading = false, itemLabel = 'dòng', className = '' }: PaginationProps) {
  const safeTotal = Math.max(1, Math.floor(Number(totalPages) || 1));
  const safeCurrent = Math.min(Math.max(1, Math.floor(Number(currentPage) || 1)), safeTotal);
  const goToPage = (page: number) => {
    if (loading || page < 1 || page > safeTotal || page === safeCurrent) return;
    onPageChange(page);
  };
  return (
    <nav className={`pagination ${className}`.trim()} aria-label="Phân trang">
      <div className="pagination-controls">
        <button type="button" className="secondary-button pagination-nav" disabled={loading || safeCurrent <= 1} onClick={() => goToPage(safeCurrent - 1)}>Trước</button>
        {getPaginationItems(safeCurrent, safeTotal).map((item, index) => item === 'ellipsis'
          ? <span key={`ellipsis-${index}`} className="pagination-ellipsis">...</span>
          : <button key={item} type="button" className={`secondary-button pagination-page${item === safeCurrent ? ' active' : ''}`} aria-current={item === safeCurrent ? 'page' : undefined} disabled={loading || item === safeCurrent} onClick={() => goToPage(item)}>{item}</button>)}
        <button type="button" className="secondary-button pagination-nav" disabled={loading || safeCurrent >= safeTotal} onClick={() => goToPage(safeCurrent + 1)}>Sau</button>
      </div>
      <span className="pagination-summary">Trang {safeCurrent} / {safeTotal}{typeof totalItems === 'number' ? ` · ${totalItems} ${itemLabel}` : ''}</span>
    </nav>
  );
}
