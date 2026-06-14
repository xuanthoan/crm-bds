import {useEffect, useMemo, useRef, useState} from 'react';
import {FormError} from '../../components/FormError';
import {Modal} from '../../components/Modal';
import {formatApiError} from '../../services/apiClient';
import {listCustomers} from '../customers/api';
import type {Customer} from '../customers/types';
import {listProjects} from '../projects/api';
import type {Project} from '../projects/types';
import {INVENTORY_STATUS_LABELS} from '../properties/constants';
import {listProperties} from '../properties/api';
import type {PropertyUnit} from '../properties/types';
import {createDeal, listDealAssignees, updateDeal} from './api';
import {DEAL_PRIORITY_LABELS, DEAL_TYPE_LABELS} from './constants';
import type {Deal, DealPayload, DealUser} from './types';

type Props = {deal?: Deal | null; customer?: Customer | null; onClose: () => void; onSaved: () => void};
const NO_PROJECT = '__no_project__';
const ACTIVE_PROJECT_STATUSES = new Set(['opening', 'selling', 'handover']);
const blank = (value: string) => value.trim() || null;
const numeric = (value: string) => value.trim() === '' ? null : Number(value);
const formatVnd = (value: number | null) => value == null
  ? 'Chưa cập nhật'
  : `${new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 0}).format(value)} đ`;

export function DealFormModal({deal, customer, onClose, onSaved}: Props) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [owners, setOwners] = useState<DealUser[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [properties, setProperties] = useState<PropertyUnit[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [loadingInventory, setLoadingInventory] = useState(true);
  const expectedValueEdited = useRef(deal?.expected_value != null);
  const [form, setForm] = useState({
    customer_id: customer?.id || deal?.customer_id || '',
    owner_id: customer?.owner?.id || deal?.owner.id || '',
    title: deal?.title || '',
    description: deal?.description || '',
    deal_type: deal?.deal_type || 'apartment',
    priority: deal?.priority || 'medium',
    project_id: deal?.project_id || '',
    property_unit_id: deal?.property_unit_id || '',
    property_type: deal?.property_type || '',
    area: deal?.area || customer?.interested_area || '',
    expected_value: String(deal?.expected_value ?? ''),
    deposit_amount: String(deal?.deposit_amount ?? ''),
    contract_value: String(deal?.contract_value ?? ''),
    commission_expected: String(deal?.commission_expected ?? ''),
    expected_close_date: deal?.expected_close_date?.slice(0, 16) || '',
  });

  useEffect(() => {
    void Promise.all([
      listCustomers({page_size: 100}),
      listDealAssignees(),
      listProjects({page_size: 100}),
      listProperties({page_size: 100}),
    ]).then(([customerResponse, ownerResponse, projectResponse, propertyResponse]) => {
      setCustomers(customerResponse.data);
      setOwners(ownerResponse.data);
      setProjects(projectResponse.data);
      setProperties(propertyResponse.data);
      setForm(current => {
        const matchedLegacyProperty = !current.property_unit_id && deal?.property_code
          ? propertyResponse.data.find(item => item.property_code === deal.property_code)
          : undefined;
        const property = propertyResponse.data.find(item => item.id === current.property_unit_id) || matchedLegacyProperty;
        return {
          ...current,
          owner_id: current.owner_id || (ownerResponse.data.length === 1 ? ownerResponse.data[0].id : ''),
          property_unit_id: property?.id || current.property_unit_id,
          project_id: property ? (property.project_id || NO_PROJECT) : current.project_id,
        };
      });
    }).catch(error => setErrors(formatApiError(error)))
      .finally(() => setLoadingInventory(false));
  }, [deal?.property_code]);

  const selectedProperty = properties.find(item => item.id === form.property_unit_id);
  const legacyPropertyUnmatched = Boolean(
    deal?.property_code && !deal.property_unit_id && !properties.some(item => item.property_code === deal.property_code),
  );
  const activeProjects = useMemo(
    () => projects.filter(project => ACTIVE_PROJECT_STATUSES.has(project.status) || project.id === deal?.project_id),
    [projects, deal?.project_id],
  );
  const selectableProperties = useMemo(() => properties.filter(property => {
    const isCurrent = property.id === deal?.property_unit_id || property.property_code === deal?.property_code;
    if (property.inventory_status !== 'available' && !isCurrent) return false;
    if (form.project_id === NO_PROJECT) return !property.project_id;
    if (form.project_id) return property.project_id === form.project_id;
    return true;
  }), [properties, form.project_id, deal?.property_unit_id, deal?.property_code]);

  const set = (key: string, value: string) => setForm(current => ({...current, [key]: value}));
  const selectProject = (projectId: string) => {
    setForm(current => {
      const currentProperty = properties.find(item => item.id === current.property_unit_id);
      const propertyMatches = !currentProperty
        || (projectId === NO_PROJECT ? !currentProperty.project_id : !projectId || currentProperty.project_id === projectId);
      return {...current, project_id: projectId, ...(propertyMatches ? {} : {property_unit_id: '', property_type: '', area: ''})};
    });
  };
  const selectProperty = (propertyId: string) => {
    const property = properties.find(item => item.id === propertyId);
    if (!property) {
      setForm(current => ({...current, property_unit_id: '', property_type: '', area: ''}));
      return;
    }
    setForm(current => ({
      ...current,
      property_unit_id: property.id,
      project_id: property.project_id || NO_PROJECT,
      property_type: property.property_type,
      area: String(property.area_net ?? property.area_gross ?? ''),
      expected_value: !expectedValueEdited.current && current.expected_value.trim() === '' && property.listed_price != null
        ? String(property.listed_price)
        : current.expected_value,
    }));
  };

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.customer_id) {
      setErrors(['Vui lòng chọn khách hàng']);
      return;
    }
    const values = [form.expected_value, form.deposit_amount, form.contract_value, form.commission_expected];
    if (values.some(value => value.trim() !== '' && (!Number.isFinite(Number(value)) || Number(value) < 0))) {
      setErrors(['Giá trị tiền không hợp lệ']);
      return;
    }
    if (numeric(form.contract_value) != null && numeric(form.deposit_amount) != null
      && numeric(form.contract_value)! < numeric(form.deposit_amount)!) {
      setErrors(['Giá trị hợp đồng phải lớn hơn hoặc bằng tiền đặt cọc']);
      return;
    }
    const selectedProject = projects.find(item => item.id === form.project_id);
    const preserveUnmatchedLegacyProperty = Boolean(deal && legacyPropertyUnmatched && !selectedProperty);
    const payload: DealPayload = {
      customer_id: form.customer_id,
      owner_id: form.owner_id,
      title: form.title.trim(),
      description: blank(form.description),
      deal_type: form.deal_type as DealPayload['deal_type'],
      priority: form.priority as DealPayload['priority'],
      property_unit_id: preserveUnmatchedLegacyProperty ? undefined : form.property_unit_id || null,
      project_id: preserveUnmatchedLegacyProperty ? undefined : form.project_id && form.project_id !== NO_PROJECT ? form.project_id : null,
      project_name: preserveUnmatchedLegacyProperty ? deal?.project_name : selectedProject?.name || null,
      property_code: preserveUnmatchedLegacyProperty ? deal?.property_code : selectedProperty?.property_code || null,
      property_type: preserveUnmatchedLegacyProperty ? deal?.property_type : selectedProperty?.property_type || null,
      area: preserveUnmatchedLegacyProperty ? deal?.area : selectedProperty ? String(selectedProperty.area_net ?? selectedProperty.area_gross ?? '') || null : null,
      expected_value: numeric(form.expected_value),
      deposit_amount: numeric(form.deposit_amount),
      contract_value: numeric(form.contract_value),
      commission_expected: numeric(form.commission_expected),
      expected_close_date: form.expected_close_date ? new Date(form.expected_close_date).toISOString() : null,
      source_lead_id: customer?.source_lead_id,
    };
    try {
      setSaving(true);
      if (deal) {
        const {customer_id, owner_id, source_lead_id, ...update} = payload;
        await updateDeal(deal.id, update);
      } else await createDeal(payload);
      onSaved();
    } catch (error) {
      setErrors(formatApiError(error));
    } finally {
      setSaving(false);
    }
  }

  return <Modal title={deal ? 'Chỉnh sửa giao dịch' : 'Tạo giao dịch'} onClose={onClose}>
    <form className="lead-form deal-form" onSubmit={submit}>
      <FormError messages={errors}/>
      <div className="form-grid">
        {customer
          ? <label className="full-span">Khách hàng<input value={`${customer.customer_code} — ${customer.full_name} — ${customer.primary_phone}`} readOnly/></label>
          : <label className="full-span">Khách hàng *<select required value={form.customer_id} onChange={event => {
            set('customer_id', event.target.value);
            const selectedCustomer = customers.find(item => item.id === event.target.value);
            if (selectedCustomer?.owner) set('owner_id', selectedCustomer.owner.id);
          }}><option value="">Vui lòng chọn khách hàng</option>{customers.map(item => <option key={item.id} value={item.id}>{item.customer_code} — {item.full_name} — {item.primary_phone}</option>)}</select></label>}
        <label>Tên giao dịch *<input required value={form.title} onChange={event => set('title', event.target.value)}/></label>
        <label>Người phụ trách *<select required value={form.owner_id} onChange={event => set('owner_id', event.target.value)}><option value="">Chọn người phụ trách</option>{owners.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select></label>
        <label>Loại giao dịch<select value={form.deal_type} onChange={event => set('deal_type', event.target.value)}>{Object.entries(DEAL_TYPE_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <label>Ưu tiên<select value={form.priority} onChange={event => set('priority', event.target.value)}>{Object.entries(DEAL_PRIORITY_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <label>Dự án<select value={form.project_id} disabled={loadingInventory} onChange={event => selectProject(event.target.value)}>
          <option value="">Không chọn / Tất cả dự án</option><option value={NO_PROJECT}>Không thuộc dự án</option>
          {activeProjects.map(item => <option key={item.id} value={item.id}>{item.project_code} — {item.name}</option>)}
        </select></label>
        <label>Bất động sản<select value={form.property_unit_id} disabled={loadingInventory || selectableProperties.length === 0} onChange={event => selectProperty(event.target.value)}>
          <option value="">{selectableProperties.length === 0 ? 'Không có bất động sản phù hợp' : form.project_id ? 'Chọn bất động sản thuộc dự án này' : 'Chọn bất động sản'}</option>
          {selectableProperties.map(item => <option key={item.id} value={item.id}>{item.property_code} — {item.title} — {item.project?.name || 'Không thuộc dự án'} — {formatVnd(item.listed_price)}</option>)}
        </select></label>
        {legacyPropertyUnmatched && <p className="form-warning full-span">Mã BĐS cũ <strong>{deal?.property_code}</strong> chưa liên kết với kho hàng. Vui lòng chọn bất động sản hợp lệ.</p>}
        {selectedProperty && <section className="deal-property-preview full-span"><strong>BĐS đã chọn</strong><dl>
          <div><dt>Mã</dt><dd>{selectedProperty.property_code}</dd></div><div><dt>Tên</dt><dd>{selectedProperty.title}</dd></div>
          <div><dt>Dự án</dt><dd>{selectedProperty.project?.name || 'Không thuộc dự án'}</dd></div>
          <div><dt>Trạng thái</dt><dd>{selectedProperty.inventory_status_label || INVENTORY_STATUS_LABELS[selectedProperty.inventory_status]}</dd></div>
          <div><dt>Giá niêm yết</dt><dd>{formatVnd(selectedProperty.listed_price)}</dd></div>
        </dl></section>}
        <label>Loại hình<input value={selectedProperty?.property_type_label || form.property_type} readOnly/></label>
        <label>Diện tích<input value={form.area} readOnly/></label>
        <label>Giá trị dự kiến<input type="number" min="0" value={form.expected_value} onChange={event => {expectedValueEdited.current = true; set('expected_value', event.target.value)}}/>{selectedProperty?.listed_price != null && <small>Giá trị dự kiến lấy từ giá niêm yết BĐS khi trường này còn trống.</small>}</label>
        <label>Tiền đặt cọc<input type="number" min="0" value={form.deposit_amount} onChange={event => set('deposit_amount', event.target.value)}/></label>
        <label>Giá trị hợp đồng<input type="number" min="0" value={form.contract_value} onChange={event => set('contract_value', event.target.value)}/></label>
        <label>Hoa hồng dự kiến<input type="number" min="0" value={form.commission_expected} onChange={event => set('commission_expected', event.target.value)}/></label>
        <label>Dự kiến chốt<input type="datetime-local" value={form.expected_close_date} onChange={event => set('expected_close_date', event.target.value)}/></label>
        <label className="full-span">Mô tả<textarea value={form.description} onChange={event => set('description', event.target.value)}/></label>
      </div>
      <footer className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>Hủy</button><button disabled={saving}>{saving ? 'Đang lưu…' : 'Lưu giao dịch'}</button></footer>
    </form>
  </Modal>;
}
