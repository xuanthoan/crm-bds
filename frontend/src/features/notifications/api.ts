import {apiRequest} from '../../services/apiClient';import type {NotificationItem} from './types';
export const listNotifications=()=>apiRequest<NotificationItem[]>('/api/v1/notifications');
export const unreadCount=()=>apiRequest<{unread_count:number}>('/api/v1/notifications/unread-count');
export const markRead=(id:string)=>apiRequest<NotificationItem>(`/api/v1/notifications/${id}/read`,{method:'POST'});
export const markAllRead=()=>apiRequest<null>('/api/v1/notifications/read-all',{method:'POST'});
