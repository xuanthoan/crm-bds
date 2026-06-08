import { CUSTOMER_STATUS_LABELS, CUSTOMER_TYPE_LABELS } from '../constants';
import type { CustomerStatus, CustomerType } from '../types';
export function CustomerBadge({status,type}:{status?:CustomerStatus;type?:CustomerType}){const value=status??type!;const label=status?CUSTOMER_STATUS_LABELS[status]:CUSTOMER_TYPE_LABELS[type!];return <span className={`badge customer-${value}`}>{label}</span>}
