import { useEffect, useState, type FormEvent } from 'react';

import { FormError } from '../../components/FormError';
import { Modal } from '../../components/Modal';
import { formatApiError } from '../../services/apiClient';
import { listLeads } from '../leads/api';
import type { Lead } from '../leads/types';
import type { AppointmentPayload, LeadAppointment } from './types';

const toLocalDateTime = (value?: string | null) =>
  value ? new Date(value).toISOString().slice(0, 16) : '';

type AppointmentFormModalProps = {
  item?: LeadAppointment;
  leadId?: string;
  ownerId?: string | null;
  onClose: () => void;
  onSubmit: (payload: AppointmentPayload) => Promise<void>;
};

export function AppointmentFormModal({
  item,
  leadId,
  ownerId,
  onClose,
  onSubmit,
}: AppointmentFormModalProps) {
  const requiresLeadSelection = !leadId && !item;
  const [accessibleLeads, setAccessibleLeads] = useState<Lead[]>([]);
  const [loadingLeads, setLoadingLeads] = useState(requiresLeadSelection);
  const [leadLoadError, setLeadLoadError] = useState<string[] | null>(null);
  const [errors, setErrors] = useState<string[] | null>(null);
  const [payload, setPayload] = useState<AppointmentPayload>({
    lead_id: leadId ?? item?.lead_id ?? '',
    title: item?.title ?? '',
    description: item?.description,
    appointment_type: item?.appointment_type ?? 'site_visit',
    start_at: toLocalDateTime(item?.start_at),
    end_at: toLocalDateTime(item?.end_at),
    location: item?.location,
    meeting_link: item?.meeting_link,
    assigned_to_id: ownerId ?? item?.assigned_to_id,
  });

  useEffect(() => {
    if (!requiresLeadSelection) return;

    let cancelled = false;

    async function loadAccessibleLeads() {
      setLoadingLeads(true);
      setLeadLoadError(null);

      try {
        const firstPage = await listLeads({ page: 1, page_size: 100 });
        const leads = [...firstPage.data];
        const totalPages = Number(firstPage.meta.total_pages ?? 1);

        for (let page = 2; page <= totalPages; page += 1) {
          const response = await listLeads({ page, page_size: 100 });
          leads.push(...response.data);
        }

        if (!cancelled) {
          setAccessibleLeads(leads);
        }
      } catch (error) {
        if (!cancelled) {
          setLeadLoadError(formatApiError(error, 'Không thể tải danh sách lead.'));
        }
      } finally {
        if (!cancelled) {
          setLoadingLeads(false);
        }
      }
    }

    void loadAccessibleLeads();

    return () => {
      cancelled = true;
    };
  }, [requiresLeadSelection]);

  function setField<Key extends keyof AppointmentPayload>(key: Key, value: AppointmentPayload[Key]) {
    setPayload((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!payload.lead_id) {
      setErrors(['Vui lòng chọn lead']);
      return;
    }
    if (!payload.title.trim()) {
      setErrors(['Tiêu đề lịch hẹn là bắt buộc']);
      return;
    }
    if (!payload.start_at) {
      setErrors(['Thời gian bắt đầu là bắt buộc']);
      return;
    }

    try {
      setErrors(null);
      await onSubmit({
        ...payload,
        start_at: new Date(payload.start_at).toISOString(),
        end_at: payload.end_at ? new Date(payload.end_at).toISOString() : null,
      });
    } catch (error) {
      setErrors(formatApiError(error));
    }
  }

  return (
    <Modal title={item ? 'Sửa lịch hẹn' : 'Tạo lịch hẹn'} onClose={onClose}>
      <form className="admin-form" onSubmit={handleSubmit}>
        <FormError messages={errors} />
        <FormError messages={leadLoadError} />
        <div className="form-grid">
          {requiresLeadSelection && (
            <label className="full-span">
              Lead
              <select
                value={payload.lead_id}
                onChange={(event) => setField('lead_id', event.target.value)}
                disabled={loadingLeads}
                aria-required="true"
              >
                <option value="">
                  {loadingLeads ? 'Đang tải danh sách lead…' : 'Chọn lead'}
                </option>
                {accessibleLeads.map((lead) => (
                  <option key={lead.id} value={lead.id}>
                    {lead.code} · {lead.full_name} · {lead.phone_primary}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            Tiêu đề
            <input
              value={payload.title}
              onChange={(event) => setField('title', event.target.value)}
              required
            />
          </label>
          <label>
            Loại
            <select
              value={payload.appointment_type}
              onChange={(event) => setField('appointment_type', event.target.value as AppointmentPayload['appointment_type'])}
            >
              <option value="office_meeting">Họp văn phòng</option>
              <option value="site_visit">Xem dự án</option>
              <option value="phone_call">Gọi điện</option>
              <option value="video_call">Video call</option>
              <option value="contract_meeting">Họp hợp đồng</option>
              <option value="other">Khác</option>
            </select>
          </label>
          <label>
            Bắt đầu
            <input
              type="datetime-local"
              value={payload.start_at}
              onChange={(event) => setField('start_at', event.target.value)}
              required
            />
          </label>
          <label>
            Kết thúc
            <input
              type="datetime-local"
              value={payload.end_at ?? ''}
              onChange={(event) => setField('end_at', event.target.value)}
            />
          </label>
          <label>
            Địa điểm
            <input
              value={payload.location ?? ''}
              onChange={(event) => setField('location', event.target.value)}
            />
          </label>
          <label>
            Link họp
            <input
              value={payload.meeting_link ?? ''}
              onChange={(event) => setField('meeting_link', event.target.value)}
            />
          </label>
          <label className="full-span">
            Mô tả
            <textarea
              value={payload.description ?? ''}
              onChange={(event) => setField('description', event.target.value)}
            />
          </label>
        </div>
        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>
            Đóng
          </button>
          <button type="submit" disabled={loadingLeads}>
            Lưu
          </button>
        </footer>
      </form>
    </Modal>
  );
}
