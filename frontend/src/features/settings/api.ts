import { apiRequest } from '../../services/apiClient';

export type CommissionPayoutPolicyCode = 'received_amount_capacity' | 'received_ratio';
export type CommissionPayoutPolicyOption = { policy_code: CommissionPayoutPolicyCode; policy_label: string; policy_description: string };
export type CommissionPayoutPolicySetting = { key: string; policy_code: CommissionPayoutPolicyCode; policy_label: string; policy_description: string; options: CommissionPayoutPolicyOption[] };

export const getCommissionPayoutPolicy = () => apiRequest<CommissionPayoutPolicySetting>('/api/v1/settings/commission-payout-policy');
export const updateCommissionPayoutPolicy = (policy_code: CommissionPayoutPolicyCode) => apiRequest<CommissionPayoutPolicySetting>('/api/v1/settings/commission-payout-policy', { method: 'PUT', body: JSON.stringify({ policy_code }) });
