export const CUSTOMER_VIEW_PERMISSIONS=['customers.view.own','customers.view.team','customers.view.department','customers.view.all'];
export const CUSTOMER_UPDATE_PERMISSIONS=['customers.update.own','customers.update.team','customers.update.department','customers.update.all'];
export const CUSTOMER_ASSIGN_PERMISSIONS=['customers.assign.own','customers.assign.team','customers.assign.department','customers.assign.all'];
export const CUSTOMER_ACTIVITY_PERMISSIONS=['customers.add_activity.own','customers.add_activity.team','customers.add_activity.department','customers.add_activity.all'];
export const CUSTOMER_TYPE_LABELS={individual:'Cá nhân',company:'Doanh nghiệp',investor:'Nhà đầu tư',agent:'Môi giới',other:'Khác'} as const;
export const CUSTOMER_STATUS_LABELS={active:'Đang hoạt động',inactive:'Ngừng hoạt động',potential:'Tiềm năng',vip:'VIP',blacklisted:'Danh sách đen'} as const;
export const PURPOSE_LABELS={buy_to_live:'Mua để ở',investment:'Đầu tư',rent:'Thuê',rent_out:'Cho thuê',other:'Khác'} as const;
