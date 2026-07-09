import type { DashboardPreset } from './types';

const PRESETS: { value: DashboardPreset; label: string }[] = [
  { value: 'today', label: 'Hôm nay' },
  { value: 'last_7_days', label: '7 ngày qua' },
  { value: 'last_30_days', label: '30 ngày qua' },
  { value: 'this_month', label: 'Tháng này' },
  { value: 'last_month', label: 'Tháng trước' },
  { value: 'custom', label: 'Tùy chọn' },
];

export function DashboardDateRangeFilter({ preset, fromDate, toDate, onChange }: { preset: DashboardPreset; fromDate: string; toDate: string; onChange: (next: { preset: DashboardPreset; fromDate: string; toDate: string }) => void }) {
  return (
    <div className="dashboard-filter" aria-label="Bộ lọc thời gian dashboard">
      <div className="filter-pills">
        {PRESETS.map((item) => (
          <button key={item.value} type="button" className={preset === item.value ? 'active' : ''} onClick={() => onChange({ preset: item.value, fromDate, toDate })}>
            {item.label}
          </button>
        ))}
      </div>
      {preset === 'custom' && (
        <div className="custom-range">
          <label>Từ ngày<input type="date" value={fromDate} onChange={(event) => onChange({ preset, fromDate: event.target.value, toDate })} /></label>
          <label>Đến ngày<input type="date" value={toDate} onChange={(event) => onChange({ preset, fromDate, toDate: event.target.value })} /></label>
        </div>
      )}
    </div>
  );
}
