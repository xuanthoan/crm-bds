import { useEffect, useState } from "react";
import { FormError } from "../../components/FormError";
import { Pagination } from "../../components/common/Pagination";
import { GuideBox } from "../../components/help/GuideBox";
import { can } from "../auth/authStore";
import { formatApiError } from "../../services/apiClient";
import { navigateTo } from "../../routes/AppRoutes";
import { listOverdueLeads, reclaimLead } from "./api";
import { PRIORITY_LABELS } from "./constants";
import { LeadPriorityBadge } from "./components/LeadPriorityBadge";
import { LeadStatusBadge } from "./components/LeadStatusBadge";
import type { Lead } from "./types";
const days = (v: string | null) =>
  v
    ? Math.max(0, Math.floor((Date.now() - new Date(v).getTime()) / 86400000))
    : 0;
export function OverdueLeadsPage() {
  const [items, setItems] = useState<Lead[]>([]),
    [priority, setPriority] = useState(""),
    [page, setPage] = useState(1),
    [meta, setMeta] = useState({ page: 1, total: 0, total_pages: 1 }),
    [errors, setErrors] = useState<string[] | null>(null),
    [loading, setLoading] = useState(true);
  async function load(nextPage = page, nextPriority = priority) {
    setLoading(true);
    try {
      const response = await listOverdueLeads({ page: nextPage, page_size: 20, priority: nextPriority });
      setItems(Array.isArray(response.data) ? response.data : []);
      setMeta({
        page: Number(response.meta.page || nextPage),
        total: Number(response.meta.total || 0),
        total_pages: Number(response.meta.total_pages || 1),
      });
      setErrors(null);
    } catch (e) {
      setItems([]);
      setMeta({ page: nextPage, total: 0, total_pages: 1 });
      setErrors(formatApiError(e));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load(page, priority);
  }, [page]);
  const apply = () => {
    setPage(1);
    void load(1, priority);
  };
  const reset = () => {
    setPriority("");
    setPage(1);
    void load(1, "");
  };
  async function reclaim(lead: Lead) {
    const reason = window.prompt(
      "Lý do thu hồi lead",
      "Sale không chăm sóc quá hạn",
    );
    if (!reason) return;
    try {
      await reclaimLead(lead.id, undefined, reason);
      await load();
    } catch (e) {
      setErrors(formatApiError(e));
    }
  }
  return (
    <section className="admin-page leads-page">
      <header className="page-header">
        <div>
          <h1>Lead quá hạn chăm sóc</h1>
          <p>Theo dõi các lead đã quá thời điểm chăm sóc tiếp theo.</p>
        </div>
      </header>
      <GuideBox
        title="Cách xử lý lead quá hạn"
        items={[
          "Ưu tiên gọi lại các lead quá hạn trước.",
          "Cập nhật kết quả chăm sóc sau khi gọi.",
          "Nếu không còn tiềm năng, ghi rõ lý do.",
          "Không để lead quá hạn lặp lại nhiều lần.",
        ]}
      />
      <div className="filter-panel">
        <select
          value={priority}
          onChange={(e: any) => setPriority(e.target.value)}
        >
          <option value="">Tất cả ưu tiên</option>
          {Object.entries(PRIORITY_LABELS).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
        <button onClick={apply}>Lọc</button><button type="button" className="secondary-button" onClick={reset}>Xóa lọc</button>
      </div>
      <FormError messages={errors} />
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Mã</th>
              <th>Khách hàng</th>
              <th>Điện thoại</th>
              <th>Trạng thái</th>
              <th>Ưu tiên</th>
              <th>Phụ trách</th>
              <th>Chăm sóc tiếp</th>
              <th>Quá hạn</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9}>Đang tải…</td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={9}>Không có dữ liệu phù hợp.</td>
              </tr>
            ) : (
              items.map((i) => (
                <tr key={i.id}>
                  <td>{i.code}</td>
                  <td>{i.full_name}</td>
                  <td>{i.phone_primary}</td>
                  <td>
                    <LeadStatusBadge status={i.status} />
                  </td>
                  <td>
                    <LeadPriorityBadge priority={i.priority} />
                  </td>
                  <td>{i.owner?.full_name ?? "—"}</td>
                  <td>
                    {i.next_follow_up_at
                      ? new Date(i.next_follow_up_at).toLocaleString("vi-VN")
                      : "—"}
                  </td>
                  <td>{days(i.next_follow_up_at)} ngày</td>
                  <td>
                    <button
                      className="link-button"
                      onClick={() => navigateTo(`/leads/${i.id}`)}
                    >
                      Chi tiết
                    </button>
                    {(can("leads.reclaim.team") ||
                      can("leads.reclaim.all")) && (
                      <button
                        className="link-button"
                        onClick={() => void reclaim(i)}
                      >
                        Thu hồi
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <Pagination
        currentPage={meta.page}
        totalPages={meta.total_pages}
        totalItems={meta.total}
        itemLabel="lead quá hạn"
        loading={loading}
        onPageChange={setPage}
      />
    </section>
  );
}
