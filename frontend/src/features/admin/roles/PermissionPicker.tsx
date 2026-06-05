import { useMemo, useState } from 'react';

import type { PermissionGroup } from '../permissions/api';

type PermissionPickerProps = {
  groups: PermissionGroup[];
  selectedCodes: string[];
  onChange: (codes: string[]) => void;
};

function labelFromCode(code: string): string {
  return code.replaceAll('.', ' · ').replaceAll('_', ' ');
}

export function PermissionPicker({ groups, selectedCodes, onChange }: PermissionPickerProps) {
  const [search, setSearch] = useState('');
  const selected = new Set(selectedCodes);

  const filteredGroups = useMemo(
    () =>
      groups
        .map((group) => ({
          ...group,
          permissions: group.permissions.filter((permission) => {
            const term = search.toLowerCase();
            return !term || permission.code.toLowerCase().includes(term) || permission.name.toLowerCase().includes(term);
          }),
        }))
        .filter((group) => group.permissions.length > 0),
    [groups, search],
  );

  function toggle(code: string) {
    const next = new Set(selectedCodes);
    if (next.has(code)) next.delete(code);
    else next.add(code);
    onChange(Array.from(next).sort());
  }

  function selectModule(codes: string[]) {
    onChange(Array.from(new Set([...selectedCodes, ...codes])).sort());
  }

  function clearModule(codes: string[]) {
    onChange(selectedCodes.filter((code) => !codes.includes(code)));
  }

  return (
    <div className="permission-picker">
      <div className="filter-row">
        <input placeholder="Tìm quyền theo code hoặc tên" value={search} onChange={(event: any) => setSearch(event.target.value)} />
        <span className="selected-count">Đã chọn {selectedCodes.length}</span>
      </div>
      <div className="permission-groups">
        {filteredGroups.map((group) => {
          const moduleCodes = group.permissions.map((permission) => permission.code);
          return (
            <section className="permission-group" key={group.module}>
              <header>
                <strong>{group.module}</strong>
                <div>
                  <button type="button" className="link-button" onClick={() => selectModule(moduleCodes)}>
                    Chọn tất cả
                  </button>
                  <button type="button" className="link-button" onClick={() => clearModule(moduleCodes)}>
                    Bỏ chọn
                  </button>
                </div>
              </header>
              <div className="permission-checkboxes">
                {group.permissions.map((permission) => (
                  <label key={permission.code} className="checkbox-row">
                    <input type="checkbox" checked={selected.has(permission.code)} onChange={() => toggle(permission.code)} />
                    <span>
                      <code>{permission.code}</code>
                      <small>{permission.name || labelFromCode(permission.code)}</small>
                    </span>
                  </label>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
