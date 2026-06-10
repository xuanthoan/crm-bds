import { useCallback, useEffect, useState } from 'react';

import { ConfirmDialog } from '../../components/ConfirmDialog';
import { formatApiError } from '../../services/apiClient';
import { navigateTo } from '../../routes/AppRoutes';
import { can } from '../auth/authStore';
import { listProperties } from '../properties/api';
import { PropertyFormModal } from '../properties/PropertyFormModal';
import { PropertyTable } from '../properties/components/PropertyTable';
import type { PropertyUnit } from '../properties/types';
import { deleteProject, getProject } from './api';
import { ProjectBadge } from './components/ProjectBadge';
import { formatProjectDeleteError } from './deleteError';
import { ProjectFormModal } from './ProjectFormModal';
import type { Project } from './types';

const show = (value: unknown) => value === null || value === undefined || value === '' ? 'Chưa cập nhật' : String(value);

export function ProjectDetailPage({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [properties, setProperties] = useState<PropertyUnit[]>([]);
  const [editing, setEditing] = useState(false);
  const [adding, setAdding] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [projectResponse, propertyResponse] = await Promise.all([
        getProject(projectId),
        listProperties({ project_id: projectId, page_size: 100 }),
      ]);
      setProject(projectResponse.data);
      setProperties(propertyResponse.data);
      setError('');
    } catch (requestError) {
      setError(formatApiError(requestError).join('. '));
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function confirmDelete() {
    if (!project) return;
    try {
      await deleteProject(project.id);
      navigateTo('/projects');
    } catch (requestError) {
      setDeleteError(formatProjectDeleteError(requestError));
    }
  }

  if (error) return <div className="form-error">{error}</div>;
  if (!project) return <p>Đang tải…</p>;

  return (
    <section className="detail-page">
      <header className="detail-header">
        <div>
          <button className="link-button" onClick={() => navigateTo('/projects')}>← Dự án</button>
          <p className="eyebrow">{project.project_code}</p>
          <h1>{project.name}</h1>
          <ProjectBadge status={project.status} />
        </div>
        <div className="header-actions">
          {can('inventory.projects.update') && <button onClick={() => setEditing(true)}>Sửa</button>}
          {can('inventory.projects.delete') && (
            <button
              className="danger-button"
              onClick={() => {
                setDeleteError('');
                setDeleting(true);
              }}
            >
              Xóa
            </button>
          )}
        </div>
      </header>

      <section className="detail-section">
        <h2>Thông tin dự án</h2>
        <dl className="detail-grid">
          <div><dt>Chủ đầu tư</dt><dd>{show(project.developer)}</dd></div>
          <div><dt>Loại dự án</dt><dd>{show(project.project_type_label)}</dd></div>
          <div><dt>Địa chỉ</dt><dd>{show(project.address)}</dd></div>
          <div><dt>Tỉnh/Thành phố</dt><dd>{show(project.province)}</dd></div>
          <div><dt>Quận/Huyện</dt><dd>{show(project.district)}</dd></div>
          <div><dt>Phường/Xã</dt><dd>{show(project.ward)}</dd></div>
          <div className="full-span"><dt>Mô tả</dt><dd>{show(project.description)}</dd></div>
        </dl>
      </section>

      <section className="detail-section">
        <div className="section-heading">
          <div>
            <h2>Bất động sản thuộc dự án</h2>
            <p>{project.property_count ?? properties.length} sản phẩm đang hoạt động</p>
          </div>
          {can('inventory.properties.create') && <button onClick={() => setAdding(true)}>Thêm bất động sản</button>}
        </div>
        <PropertyTable
          items={properties}
          abilities={{ update: false, status: false, price: false, delete: false }}
          onEdit={() => {}}
          onStatus={() => {}}
          onPrice={() => {}}
          onDelete={() => {}}
        />
      </section>

      {editing && (
        <ProjectFormModal
          project={project}
          onClose={() => setEditing(false)}
          onSaved={() => {
            setEditing(false);
            void load();
          }}
        />
      )}
      {adding && (
        <PropertyFormModal
          projects={[project]}
          defaultProjectId={project.id}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false);
            void load();
          }}
        />
      )}
      {deleting && (
        <ConfirmDialog
          title={deleteError ? 'Không thể xóa dự án' : 'Xóa dự án'}
          message={`Xóa mềm ${project.project_code} — ${project.name}?`}
          error={deleteError}
          onCancel={() => {
            setDeleting(false);
            setDeleteError('');
          }}
          onConfirm={() => void confirmDelete()}
        />
      )}
    </section>
  );
}
