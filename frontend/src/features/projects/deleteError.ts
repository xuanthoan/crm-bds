import { formatApiError } from '../../services/apiClient';

export function formatProjectDeleteError(error: unknown): string {
  const detail = formatApiError(error, 'Không thể xóa dự án.').join('\n');
  return `${detail}\nVui lòng chuyển dự án hoặc xóa các bất động sản trước.`;
}
