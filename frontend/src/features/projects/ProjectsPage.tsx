import { useCallback, useEffect, useState } from 'react';

import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Pagination } from '../../components/common/Pagination';
import { formatApiError } from '../../services/apiClient';
import { can } from '../auth/authStore';
import { deleteProject, listProjects } from './api';
import { ProjectFilters } from './components/ProjectFilters';
import { ProjectTable } from './components/ProjectTable';
import { formatProjectDeleteError } from './deleteError';
import { ProjectFormModal } from './ProjectFormModal';
import type { Project, ProjectFilters as Filters } from './types';

export function ProjectsPage() {
  const [items, setItems] = useState<Project[]>([]);
  const [filters, setFilters] = useState<Filters>({ page: 1, page_size: 20 });
  const [editing, setEditing] = useState<Project | null | undefined>();
  const [deleting, setDeleting] = useState<Project | null>(null);
  const [deleteError, setDeleteError] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [meta, setMeta] = useState({ page: 1, total: 0, total_pages: 1 });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listProjects(filters);
      setItems(Array.isArray(response.data) ? response.data : []);
      setMeta({ page: Number(response.meta.page || filters.page || 1), total: Number(response.meta.total || 0), total_pages: Number(response.meta.total_pages || 1) });
      setError('');
    } catch (requestError) {
      setItems([]);
      setMeta({ page: Number(filters.page || 1), total: 0, total_pages: 1 });
      setError(formatApiError(requestError).join('. '));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void load();
  }, [load]);

  function openDelete(project: Project) {
    setDeleteError('');
    setDeleting(project);
  }

  async function confirmDelete() {
    if (!deleting) return;
    try {
      await deleteProject(deleting.id);
      setDeleting(null);
      setDeleteError('');
      await load();
    } catch (requestError) {
      setDeleteError(formatProjectDeleteError(requestError));
    }
  }

  return (
    <section className="admin-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Kho hàng</p>
          <h1>Dự án</h1>
          <p>Quản lý danh mục dự án bất động sản.</p>
        </div>
        {can('inventory.projects.create') && <button onClick={() => setEditing(null)}>Thêm dự án</button>}
      </header>
      <ProjectFilters value={filters} onChange={setFilters} />
      {error && <div className="form-error">{error}</div>}
      <ProjectTable items={items} onEdit={setEditing} onDelete={openDelete} />
      {loading && <p>Đang tải...</p>}
      {!loading && !error && items.length === 0 && <p className="empty-state">Không có dữ liệu phù hợp.</p>}
      <Pagination currentPage={meta.page} totalPages={meta.total_pages} totalItems={meta.total} itemLabel="dự án" loading={loading} onPageChange={(page) => setFilters((current) => ({ ...current, page }))} />
      {editing !== undefined && (
        <ProjectFormModal
          project={editing}
          onClose={() => setEditing(undefined)}
          onSaved={() => {
            setEditing(undefined);
            void load();
          }}
        />
      )}
      {deleting && (
        <ConfirmDialog
          title={deleteError ? 'Không thể xóa dự án' : 'Xóa dự án'}
          message={`Xóa mềm dự án ${deleting.project_code} — ${deleting.name}?`}
          error={deleteError}
          onCancel={() => {
            setDeleting(null);
            setDeleteError('');
          }}
          onConfirm={() => void confirmDelete()}
        />
      )}
    </section>
  );
}
