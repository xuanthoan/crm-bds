import { useEffect, useState } from 'react';

type ValueType = 'string' | 'boolean' | 'number' | 'array';
type QueryConfig<T> = Partial<Record<keyof T & string, ValueType>>;

function convert(value: string, type: ValueType) {
  if (type === 'boolean') return value === 'true' || value === '1';
  if (type === 'number') return Number(value);
  if (type === 'array') return value.split(',').filter(Boolean);
  return value;
}

export function hydrateFiltersFromQuery<T extends Record<string, any>>(defaults: T, config: QueryConfig<T>, search = window.location.search): T {
  const params = new URLSearchParams(search);
  const next: Record<string, any> = { ...defaults };
  Object.entries(config).forEach(([key, type]) => {
    const value = params.get(key);
    if (value !== null && value !== '') next[key] = convert(value, type as ValueType);
  });
  return next as T;
}

export function useQueryHydratedFilters<T extends Record<string, any>>(defaults: T, config: QueryConfig<T>) {
  const [filters, setFilters] = useState<T>(() => hydrateFiltersFromQuery(defaults, config));
  useEffect(() => {
    const hydrate = () => setFilters(hydrateFiltersFromQuery(defaults, config));
    window.addEventListener('popstate', hydrate);
    return () => window.removeEventListener('popstate', hydrate);
  }, [JSON.stringify(defaults), JSON.stringify(config)]);
  return [filters, setFilters] as const;
}
