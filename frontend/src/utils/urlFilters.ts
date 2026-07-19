export type FilterValue = string | number | boolean | undefined;
export type FilterState = Record<string, FilterValue>;

const BOOLEAN_KEYS = new Set(['today', 'overdue', 'upcoming', 'has_activity', 'stale']);
const NUMBER_KEYS = new Set(['page', 'page_size']);

export function queryFilters<T extends FilterState>(defaults: T = {} as T, search = window.location.search): T {
  const params = new URLSearchParams(search);
  const next: FilterState = { page: 1, page_size: 20, ...defaults };
  params.forEach((value, key) => {
    if (value === '') return;
    if (BOOLEAN_KEYS.has(key)) next[key] = value === 'true' || value === '1';
    else if (NUMBER_KEYS.has(key)) next[key] = Number(value);
    else next[key] = value;
  });
  return next as T;
}

export function mergeQueryFilters<T extends FilterState>(defaults: T = {} as T, search = window.location.search): T {
  return queryFilters(defaults, search);
}
