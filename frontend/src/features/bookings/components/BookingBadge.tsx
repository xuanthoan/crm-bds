import{BOOKING_STATUS_LABELS}from'../constants';import type{BookingStatus}from'../types';
export function BookingBadge({status}:{status:BookingStatus}){return <span className={`inventory-badge booking-status-${status}`}>{BOOKING_STATUS_LABELS[status]}</span>}
