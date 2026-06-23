import type { Deal, DealStage, DealStatus } from './types';

export const EFFECTIVE_CONTRACT_STATUSES = ['signed', 'active', 'completed'] as const;
export const DEAL_CONTRACT_LOCK_MESSAGE = 'Không thể hủy/thất bại giao dịch vì đang có hợp đồng hiệu lực. Vui lòng hủy hợp đồng trước.';
export const CONTRACT_LOCK_ALLOWED_STAGES: DealStage[] = ['contract', 'contract_signed', 'completed'];
export const CONTRACT_LOCK_ALLOWED_STATUSES: DealStatus[] = ['contracted', 'payment_in_progress', 'completed', 'won'];

export function hasEffectiveContract(deal: Deal) {
  return !!deal.contracts?.some((contract) => EFFECTIVE_CONTRACT_STATUSES.includes(contract.status as typeof EFFECTIVE_CONTRACT_STATUSES[number]));
}

export function dealStageOptionsForContractLock(deal: Deal, entries: [string, string][]) {
  if (!hasEffectiveContract(deal)) return entries;
  return entries.filter(([value]) => CONTRACT_LOCK_ALLOWED_STAGES.includes(value as DealStage));
}

export function dealStatusOptionsForContractLock(deal: Deal, entries: [string, string][]) {
  if (!hasEffectiveContract(deal)) return entries;
  return entries.filter(([value]) => CONTRACT_LOCK_ALLOWED_STATUSES.includes(value as DealStatus));
}
