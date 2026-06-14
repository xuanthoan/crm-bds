import {useEffect, useMemo, useRef, useState} from 'react';

export type ComboboxOption = {
  value: string;
  label: string;
  searchText?: string;
  className?: string;
};

type Props = {
  ariaLabel: string;
  value: string;
  options: ComboboxOption[];
  placeholder: string;
  emptyMessage: string;
  loadingMessage: string;
  loading?: boolean;
  onChange: (value: string) => void;
};

export const normalizeSearchText = (value: string) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLocaleLowerCase('vi-VN')
  .trim();

export function SearchableCombobox({
  ariaLabel,
  value,
  options,
  placeholder,
  emptyMessage,
  loadingMessage,
  loading = false,
  onChange,
}: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const selected = options.find(option => option.value === value);
  const filteredOptions = useMemo(() => {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) return options;
    return options.filter(option => normalizeSearchText(`${option.label} ${option.searchText || ''}`).includes(normalizedQuery));
  }, [options, query]);

  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        setQuery('');
      }
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, []);

  useEffect(() => setActiveIndex(0), [query, options]);

  const choose = (option: ComboboxOption) => {
    onChange(option.value);
    setOpen(false);
    setQuery('');
    inputRef.current?.focus();
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') {
      setOpen(false);
      setQuery('');
      return;
    }
    if (!open && ['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key)) {
      event.preventDefault();
      setOpen(true);
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex(index => Math.min(index + 1, filteredOptions.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex(index => Math.max(index - 1, 0));
    } else if (event.key === 'Enter' && filteredOptions[activeIndex]) {
      event.preventDefault();
      choose(filteredOptions[activeIndex]);
    }
  };

  return <div className="searchable-combobox" ref={rootRef}>
    <input
      ref={inputRef}
      role="combobox"
      aria-label={ariaLabel}
      aria-expanded={open}
      aria-autocomplete="list"
      autoComplete="off"
      value={open ? query : selected?.label || ''}
      placeholder={loading ? loadingMessage : placeholder}
      disabled={loading}
      onClick={() => setOpen(true)}
      onFocus={() => setOpen(true)}
      onChange={event => {
        setQuery(event.target.value);
        setOpen(true);
      }}
      onKeyDown={onKeyDown}
    />
    <button
      type="button"
      className="searchable-combobox-toggle"
      aria-label={`${open ? 'Đóng' : 'Mở'} ${ariaLabel.toLocaleLowerCase('vi-VN')}`}
      disabled={loading}
      onClick={() => {
        setOpen(current => !current);
        inputRef.current?.focus();
      }}
    >⌄</button>
    {open && <div className="searchable-combobox-menu" role="listbox">
      {loading
        ? <p className="searchable-combobox-empty">{loadingMessage}</p>
        : filteredOptions.length
          ? filteredOptions.map((option, index) => <button
            type="button"
            role="option"
            aria-selected={option.value === value}
            className={`${option.className || ''}${index === activeIndex ? ' active' : ''}`}
            key={`${option.value || 'empty'}-${option.label}`}
            onMouseEnter={() => setActiveIndex(index)}
            onClick={() => choose(option)}
          >{option.label}</button>)
          : <p className="searchable-combobox-empty">{emptyMessage}</p>}
    </div>}
  </div>;
}
