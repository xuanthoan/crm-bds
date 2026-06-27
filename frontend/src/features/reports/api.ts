import { apiRequest, getAccessToken } from '../../services/apiClient';
import type { CashCollectionReport, FinanceSummary, InvoiceReport, OverduePaymentRow, Paginated, ReceivableRow } from './types';
const qs=(filters:Record<string,string>)=>new URLSearchParams(Object.fromEntries(Object.entries(filters).filter(([,v])=>v))).toString();
export const financeSummary=(f:Record<string,string>)=>apiRequest<FinanceSummary>(`/api/v1/reports/finance/summary?${qs(f)}`);
export const receivables=(f:Record<string,string>)=>apiRequest<Paginated<ReceivableRow>>(`/api/v1/reports/finance/receivables?${qs(f)}`);
export const overduePayments=(f:Record<string,string>)=>apiRequest<Paginated<OverduePaymentRow>>(`/api/v1/reports/finance/overdue-payments?${qs(f)}`);
export const cashCollection=(f:Record<string,string>)=>apiRequest<CashCollectionReport>(`/api/v1/reports/finance/cash-collection?${qs(f)}`);
export const invoiceReport=(f:Record<string,string>)=>apiRequest<InvoiceReport>(`/api/v1/reports/finance/invoices?${qs(f)}`);
export async function downloadFinanceCsv(report:string, filters:Record<string,string>){
  const token=getAccessToken(); const url=`${import.meta.env.VITE_API_URL || ''}/api/v1/reports/finance/${report}/export?${qs(filters)}`;
  const res=await fetch(url,{headers: token ? {Authorization:`Bearer ${token}`} : {}}); if(!res.ok) throw new Error('Không thể xuất CSV. Vui lòng kiểm tra quyền hoặc thử lại.');
  const blob=await res.blob(); const cd=res.headers.get('Content-Disposition')||''; const name=cd.match(/filename="?([^";]+)"?/)?.[1] || 'bao-cao.csv';
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(a.href);
}
