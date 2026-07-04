export type GlossaryTerm = {
  term: string;
  group: string;
  description: string;
  example?: string;
  modules?: string[];
};
export type HelpSection = {
  title: string;
  items: string[];
  groups?: { title: string; items: string[] }[];
};

export const tooltipTexts = {
  eligibleCommission:
    "Hoa hồng đủ điều kiện tính theo hợp đồng và khoản khách đã thanh toán.",
  approvedCommission: "Số tiền hoa hồng sale đã được quản lý duyệt.",
  paidAmount: "Tổng tiền đã chi qua phiếu chi đã xác nhận.",
  remainingSalesCommission: "Số tiền còn lại chưa chi cho sale.",
  commissionStatus:
    "Trạng thái xử lý hoa hồng sale trong quy trình duyệt và chi.",
  createPaymentVoucher: "Tạo chứng từ cho một lần chi hoa hồng sale.",
  payoutPolicy:
    "Quy tắc xác định khi nào được chi hoa hồng sale và được chi tối đa bao nhiêu.",
  remainingPayableCapacity:
    "Số tiền tối đa còn được chi tại thời điểm hiện tại theo chính sách.",
  companyConfirmed:
    "Số tiền hoa hồng công ty dự kiến hoặc đã xác nhận sẽ nhận.",
  companyReceived: "Số tiền công ty đã thực nhận.",
  companyRemaining: "Số tiền công ty còn chưa nhận.",
  commissionPayer:
    "Bên có trách nhiệm trả hoa hồng cho công ty: chủ đầu tư, chủ nhà, chủ đất hoặc đối tác.",
  receiveCompanyCommission: "Ghi nhận số tiền hoa hồng công ty đã thực nhận.",
  draftVoucher:
    "Phiếu đã tạo nhưng chưa xác nhận chi tiền, chưa cộng vào số đã chi sale.",
  paidVoucher: "Phiếu đã xác nhận chi tiền và được cộng vào số đã chi sale.",
  cancelVoucher: "Hủy phiếu không còn hợp lệ theo quy trình được phép.",
  documentLink: "Đường dẫn tới chứng từ hoặc file đính kèm phục vụ đối soát.",
  paymentReference: "Mã giao dịch hoặc mã chứng từ dùng để tra cứu lần chi.",
  reconciliationStatus:
    "Tình trạng tổng hợp của hợp đồng/hoa hồng dựa trên tiền công ty nhận, hoa hồng sale và phiếu chi.",
  blockedByPolicy:
    "Còn tiền sale phải chi nhưng hiện chưa đủ điều kiện chi tiếp.",
  hasDraftVoucher: "Đang có phiếu chi ở trạng thái nháp cần xác nhận hoặc hủy.",
  policyOption1: "Sale được chi trong phạm vi tiền hoa hồng công ty đã nhận.",
  policyOption2:
    "Sale được chi theo tỷ lệ tương ứng với phần hoa hồng công ty đã thu.",
  systemFallback:
    "Chính sách dùng khi dự án/hoa hồng chưa có chính sách riêng.",
  projectDefault:
    "Chính sách mặc định áp dụng cho các hoa hồng thuộc dự án này.",
  approvalOverride:
    "Chính sách riêng được chọn khi duyệt hoa hồng, nếu hệ thống cho phép.",
};

export const glossaryTerms: GlossaryTerm[] = [
  [
    "Lead",
    "Khách hàng & Lead",
    "Khách hàng tiềm năng, có thể đến từ quảng cáo, giới thiệu, telesale hoặc nguồn khác.",
  ],
  [
    "Khách hàng",
    "Khách hàng & Lead",
    "Người đã có thông tin rõ ràng trong hệ thống và có thể phát sinh giao dịch.",
  ],
  [
    "Booking / Giữ chỗ",
    "Booking & Hợp đồng",
    "Bước khách hàng đặt giữ sản phẩm/căn/hồ sơ trước khi ký hợp đồng chính thức.",
  ],
  [
    "Hợp đồng",
    "Booking & Hợp đồng",
    "Giao dịch chính thức giữa khách hàng và bên bán/chủ đầu tư/chủ nhà, là cơ sở để tính doanh thu và hoa hồng.",
  ],
  [
    "Thanh toán",
    "Thanh toán & Hóa đơn",
    "Khoản tiền khách hàng phải trả hoặc đã trả theo hợp đồng.",
  ],
  [
    "Phiếu thu",
    "Thanh toán & Hóa đơn",
    "Chứng từ ghi nhận công ty đã thu tiền từ khách hàng.",
  ],
  [
    "Hóa đơn",
    "Thanh toán & Hóa đơn",
    "Chứng từ xuất cho khoản phải thu/thanh toán, không đồng nghĩa tự động đã thu tiền.",
  ],
  [
    "Hoa hồng công ty",
    "Hoa hồng",
    "Khoản hoa hồng/doanh thu công ty được nhận từ chủ đầu tư, chủ nhà, chủ đất hoặc đối tác.",
  ],
  [
    "Hoa hồng công ty xác nhận",
    "Hoa hồng",
    "Số tiền hoa hồng công ty được xác nhận sẽ nhận hoặc phải thu.",
  ],
  [
    "Hoa hồng công ty đã nhận",
    "Hoa hồng",
    "Số tiền hoa hồng công ty đã thực nhận.",
  ],
  [
    "Hoa hồng công ty còn phải thu",
    "Hoa hồng",
    "Số tiền hoa hồng công ty còn chưa nhận, thường bằng hoa hồng xác nhận trừ hoa hồng đã nhận.",
  ],
  [
    "Hoa hồng sale",
    "Hoa hồng",
    "Khoản tiền công ty dự kiến hoặc đã duyệt để chi cho sale theo hợp đồng/giao dịch.",
  ],
  [
    "Hoa hồng sale đã duyệt",
    "Hoa hồng",
    "Số tiền hoa hồng sale đã được quản lý duyệt.",
  ],
  [
    "Đã chi sale",
    "Phiếu chi",
    "Tổng tiền hoa hồng đã chi cho sale qua phiếu chi đã xác nhận.",
  ],
  [
    "Còn phải chi sale",
    "Phiếu chi",
    "Số tiền hoa hồng sale còn lại chưa chi, thường bằng hoa hồng sale đã duyệt trừ số đã chi.",
  ],
  [
    "Chính sách chi hoa hồng",
    "Hoa hồng",
    "Quy tắc xác định khi nào được chi hoa hồng sale và được chi tối đa bao nhiêu.",
  ],
  [
    "Chi theo hạn mức tiền HH công ty đã nhận",
    "Hoa hồng",
    "Sale được chi tối đa trong phạm vi tiền hoa hồng công ty đã thực nhận.",
  ],
  [
    "Chi theo tỷ lệ HH công ty đã thu",
    "Hoa hồng",
    "Sale được chi theo tỷ lệ tương ứng với phần hoa hồng công ty đã thu được.",
  ],
  [
    "Hạn mức còn có thể chi",
    "Hoa hồng",
    "Số tiền tối đa còn được phép chi cho sale tại thời điểm hiện tại theo chính sách.",
  ],
  [
    "Bị chặn theo chính sách",
    "Báo cáo",
    "Hoa hồng sale còn phải chi nhưng hiện chưa đủ điều kiện chi tiếp do chính sách hoặc tiền hoa hồng công ty đã nhận chưa đủ.",
  ],
  [
    "Phiếu chi hoa hồng",
    "Phiếu chi",
    "Chứng từ ghi nhận một lần chi hoa hồng cho sale.",
  ],
  [
    "Phiếu chi nháp",
    "Phiếu chi",
    "Phiếu chi đã tạo nhưng chưa xác nhận đã chi tiền, chưa được tính vào số đã chi sale.",
  ],
  [
    "Phiếu đã chi",
    "Phiếu chi",
    "Phiếu chi đã xác nhận chi tiền, được tính vào số đã chi sale.",
  ],
  [
    "Đối soát hoa hồng",
    "Báo cáo",
    "Quá trình so sánh hoa hồng công ty, hoa hồng sale, phiếu chi và số tiền còn phải thu/chi để kiểm tra sai lệch.",
  ],
  [
    "Sale đã chi đủ",
    "Báo cáo",
    "Hoa hồng sale đã được chi đủ theo số tiền đã duyệt.",
  ],
  [
    "Sale đã chi một phần",
    "Báo cáo",
    "Hoa hồng sale đã được chi một phần nhưng vẫn còn tiền chưa chi.",
  ],
  [
    "Sale chưa được chi",
    "Báo cáo",
    "Hoa hồng sale đã duyệt nhưng chưa có phiếu chi đã xác nhận.",
  ],
  [
    "Có phiếu nháp",
    "Báo cáo",
    "Đang có phiếu chi ở trạng thái nháp cần xác nhận hoặc hủy.",
  ],
  [
    "Thu vượt",
    "Báo cáo",
    "Số tiền hoa hồng công ty đã nhận lớn hơn số xác nhận, cần kiểm tra lại dữ liệu.",
  ],
  [
    "Chi vượt",
    "Báo cáo",
    "Số tiền đã chi sale lớn hơn số hoa hồng sale đã duyệt, là cảnh báo nghiêm trọng cần kiểm tra.",
  ],

  [
    "Chủ đầu tư",
    "Bất động sản",
    "Đơn vị phát triển dự án, chịu trách nhiệm triển khai, pháp lý, xây dựng và bàn giao sản phẩm.",
  ],
  [
    "Chủ nhà / Chủ đất",
    "Bất động sản",
    "Cá nhân hoặc tổ chức sở hữu bất động sản đang bán/cho thuê/chuyển nhượng.",
  ],
  [
    "Sổ đỏ",
    "Bất động sản",
    "Tên gọi phổ biến của giấy chứng nhận quyền sử dụng đất.",
  ],
  [
    "Sổ hồng",
    "Bất động sản",
    "Tên gọi phổ biến của giấy chứng nhận quyền sở hữu nhà ở và quyền sử dụng đất ở.",
  ],
  [
    "Hợp đồng đặt cọc",
    "Bất động sản",
    "Thỏa thuận ghi nhận việc khách đặt cọc để đảm bảo giao dịch mua bán/chuyển nhượng.",
  ],
  [
    "Hợp đồng mua bán",
    "Bất động sản",
    "Hợp đồng chính thức ghi nhận giao dịch mua bán bất động sản giữa các bên.",
  ],
  [
    "Pháp lý dự án",
    "Bất động sản",
    "Tình trạng hồ sơ pháp lý của dự án, như quyền sử dụng đất, giấy phép xây dựng, quy hoạch, điều kiện bán hàng.",
  ],
  [
    "Tiến độ thanh toán",
    "Bất động sản",
    "Lịch các đợt khách hàng cần thanh toán theo thỏa thuận hoặc hợp đồng.",
  ],
  [
    "Chính sách bán hàng",
    "Bất động sản",
    "Các ưu đãi, chiết khấu, lịch thanh toán, hỗ trợ vay hoặc quà tặng áp dụng cho sản phẩm/dự án.",
  ],
  [
    "Chiết khấu",
    "Bất động sản",
    "Khoản giảm trừ giá bán hoặc ưu đãi tài chính cho khách hàng theo chính sách bán hàng.",
  ],
  [
    "Vay ngân hàng",
    "Bất động sản",
    "Hình thức khách hàng vay vốn ngân hàng để thanh toán một phần giá trị bất động sản.",
  ],
  [
    "Lãi suất ưu đãi",
    "Bất động sản",
    "Mức lãi suất thấp hơn thông thường được ngân hàng áp dụng trong thời gian đầu khoản vay.",
  ],
  [
    "Ân hạn nợ gốc",
    "Bất động sản",
    "Thời gian khách hàng chưa phải trả gốc vay, thường chỉ trả lãi hoặc được hỗ trợ theo chính sách.",
  ],
  [
    "Diện tích thông thủy",
    "Bất động sản",
    "Diện tích sử dụng thực tế bên trong căn hộ, tính theo phần có thể sử dụng.",
  ],
  [
    "Diện tích tim tường",
    "Bất động sản",
    "Diện tích tính từ tim tường bao, tường ngăn căn hộ; thường lớn hơn diện tích thông thủy.",
  ],
  [
    "Phí bảo trì",
    "Bất động sản",
    "Khoản phí thường thu khi mua căn hộ để bảo trì phần sở hữu chung của tòa nhà.",
  ],
  [
    "Phí quản lý",
    "Bất động sản",
    "Khoản phí cư dân/người sử dụng đóng định kỳ để vận hành, quản lý tòa nhà/khu đô thị.",
  ],
  [
    "Bàn giao thô",
    "Bất động sản",
    "Hình thức bàn giao nhà/căn hộ chưa hoàn thiện đầy đủ nội thất, khách cần tự hoàn thiện thêm.",
  ],
  [
    "Bàn giao hoàn thiện",
    "Bất động sản",
    "Hình thức bàn giao đã hoàn thiện cơ bản như sàn, tường, trần, thiết bị vệ sinh hoặc theo tiêu chuẩn dự án.",
  ],
  [
    "Shophouse",
    "Bất động sản",
    "Sản phẩm nhà phố thương mại, thường dùng để vừa ở vừa kinh doanh hoặc cho thuê.",
  ],
  [
    "Căn hộ",
    "Bất động sản",
    "Sản phẩm nhà ở trong tòa chung cư, thường có diện tích, số phòng ngủ, tầng, view cụ thể.",
  ],
  [
    "Nhà phố",
    "Bất động sản",
    "Nhà ở thấp tầng thường nằm trong khu dân cư hoặc khu đô thị, có thể dùng để ở hoặc kinh doanh.",
  ],
  [
    "Biệt thự",
    "Bất động sản",
    "Sản phẩm nhà ở cao cấp, thường có diện tích đất lớn hơn, không gian riêng và giá trị cao.",
  ],
  [
    "Đất nền",
    "Bất động sản",
    "Lô đất chưa xây dựng nhà ở, thường được mua để đầu tư, xây dựng hoặc chuyển nhượng.",
  ],
  [
    "Khách nóng",
    "Chăm sóc khách hàng",
    "Khách có nhu cầu rõ, tài chính tương đối rõ, thời gian mua gần và phản hồi tốt.",
  ],
  [
    "Khách ấm",
    "Chăm sóc khách hàng",
    "Khách có quan tâm nhưng cần thêm thời gian, thông tin hoặc so sánh thêm trước khi quyết định.",
  ],
  [
    "Khách lạnh",
    "Chăm sóc khách hàng",
    "Khách chỉ tham khảo, chưa có nhu cầu rõ hoặc chưa có kế hoạch mua gần.",
  ],
  [
    "Follow-up",
    "Chăm sóc khách hàng",
    "Hoạt động chăm sóc lại khách sau lần liên hệ trước, như gọi lại, nhắn tin, gửi thông tin hoặc hẹn gặp.",
  ],
  [
    "Lịch hẹn",
    "Chăm sóc khách hàng",
    "Lịch làm việc với khách, ví dụ gọi lại, gặp trực tiếp, xem nhà, xem dự án hoặc ký hồ sơ.",
  ],
  [
    "Lead quá hạn",
    "Chăm sóc khách hàng",
    "Lead đã được giao nhưng quá thời gian quy định chưa có hoạt động chăm sóc mới.",
  ],
  [
    "Nguồn lead",
    "Chăm sóc khách hàng",
    "Kênh tạo ra khách hàng tiềm năng, ví dụ quảng cáo, giới thiệu, telesale, website, Facebook, Zalo.",
  ],
  [
    "Lead rác",
    "Chăm sóc khách hàng",
    "Lead không có nhu cầu thật, sai số, không đúng phân khúc hoặc không thể chăm sóc hiệu quả.",
  ],
  [
    "Trùng khách",
    "Chăm sóc khách hàng",
    "Khách hàng có số điện thoại/email/Zalo/Facebook trùng với bản ghi đã tồn tại trong hệ thống.",
  ],
  [
    "Người quyết định chính",
    "Chăm sóc khách hàng",
    "Người có quyền quyết định mua hoặc không mua bất động sản trong giao dịch.",
  ],
  [
    "Nhu cầu ở thực",
    "Chăm sóc khách hàng",
    "Khách mua bất động sản để sinh sống, ưu tiên tiện ích, vị trí, môi trường và khả năng tài chính.",
  ],
  [
    "Nhu cầu đầu tư",
    "Chăm sóc khách hàng",
    "Khách mua bất động sản với mục tiêu tăng giá, cho thuê hoặc giữ tài sản.",
  ],
  [
    "Chi phí quảng cáo",
    "Marketing & nguồn lead",
    "Số tiền bỏ ra cho các kênh quảng cáo để tạo lead hoặc tăng nhận diện dự án/sản phẩm.",
  ],
  [
    "CPL",
    "Marketing & nguồn lead",
    "Cost per Lead, chi phí trung bình để tạo ra một lead.",
  ],
  [
    "Tỷ lệ chuyển đổi",
    "Marketing & nguồn lead",
    "Tỷ lệ lead chuyển sang bước tiếp theo như lịch hẹn, booking hoặc hợp đồng.",
  ],
  [
    "ROI quảng cáo",
    "Marketing & nguồn lead",
    "Chỉ số so sánh kết quả thu được với chi phí quảng cáo đã bỏ ra.",
  ],
].map(([term, group, description]) => ({
  term,
  group,
  description,
  modules:
    group === "Hoa hồng" ? ["Hoa hồng sale", "Hoa hồng công ty"] : [group],
}));

export const helpSections: HelpSection[] = [
  {
    title: "Tổng quan quy trình CRM BĐS",
    items: [
      "Lead được tạo từ nguồn quảng cáo, telesale hoặc nhập tay.",
      "Sale chăm sóc lead bằng task, lịch hẹn, ghi chú.",
      "Khi khách hàng quan tâm thực sự, có thể tạo booking/giữ chỗ.",
      "Khi giao dịch chính thức, tạo hợp đồng.",
      "Theo hợp đồng, hệ thống theo dõi thanh toán, phiếu thu, hóa đơn.",
      "Khi đủ điều kiện, hệ thống tạo và duyệt hoa hồng sale.",
      "Công ty ghi nhận hoa hồng công ty phải thu và đã nhận.",
      "Kế toán/sếp lập phiếu chi hoa hồng sale.",
      "Báo cáo đối soát giúp kiểm tra tổng thể.",
    ],
  },
  {
    title: "Phân biệt Hoa hồng công ty và Hoa hồng sale",
    items: [],
    groups: [
      {
        title: "Hoa hồng công ty",
        items: [
          "Là tiền công ty được nhận từ chủ đầu tư/chủ nhà/đối tác.",
          "Là nguồn tiền/điều kiện để xét chi hoa hồng sale.",
        ],
      },
      {
        title: "Hoa hồng sale",
        items: [
          "Là tiền công ty chi cho sale.",
          "Cần được duyệt trước khi chi.",
          "Việc chi có thể bị chặn nếu chưa đủ điều kiện theo chính sách.",
        ],
      },
    ],
  },
  {
    title: "Quy trình hoa hồng sale",
    items: [
      "Tạo hoa hồng sale từ hợp đồng.",
      "Duyệt số tiền hoa hồng sale.",
      "Hệ thống kiểm tra chính sách chi.",
      "Lập phiếu chi hoa hồng.",
      "Có thể lưu nháp hoặc xác nhận đã chi.",
      "Phiếu nháp chưa tính vào đã chi.",
      "Phiếu đã chi mới tính vào đã chi sale.",
    ],
  },
  {
    title: "Quy trình hoa hồng công ty",
    items: [
      "Tạo hoa hồng công ty từ hợp đồng.",
      "Xác nhận số tiền công ty phải thu.",
      "Ghi nhận số tiền công ty đã nhận.",
      "Số tiền đã nhận ảnh hưởng đến hạn mức chi sale.",
    ],
  },
  {
    title: "Khi nào sale bị chặn chi?",
    items: [
      "Hoa hồng công ty chưa nhận đủ.",
      "Chính sách dự án yêu cầu chi theo tỷ lệ tiền đã thu.",
      "COM đang bị tạm giữ.",
      "Hoa hồng sale chưa được duyệt.",
      "Đã chi đủ hoa hồng sale.",
      "Không có quyền thao tác.",
    ],
  },
  {
    title: "Phiếu chi hoa hồng",
    items: [
      "Mỗi lần chi hoa hồng tạo một phiếu chi riêng.",
      "Một COM có thể có nhiều phiếu chi.",
      "Phiếu nháp không cộng vào đã chi.",
      "Phiếu đã chi mới cộng vào đã chi.",
      "Hủy phiếu đã chi sẽ làm giảm số đã chi nếu hệ thống cho phép.",
    ],
  },
  {
    title: "Báo cáo đối soát hoa hồng",
    items: [
      "Công ty đã thu bao nhiêu hoa hồng.",
      "Còn phải thu bao nhiêu.",
      "Sale đã được duyệt bao nhiêu.",
      "Đã chi sale bao nhiêu.",
      "Còn phải chi sale bao nhiêu.",
      "Dòng nào bị chặn theo chính sách.",
      "Dòng nào có phiếu nháp.",
      "Có dữ liệu thu vượt/chi vượt không.",
    ],
  },
  {
    title: "Ý nghĩa các trạng thái đối soát",
    items: [
      "Bình thường: không có cảnh báo nghiêm trọng.",
      "Công ty chưa thu đủ: hoa hồng công ty còn phải thu.",
      "Sale chưa được chi: hoa hồng sale đã duyệt nhưng chưa chi.",
      "Sale đã chi một phần: đã chi một phần, còn lại chưa chi.",
      "Sale đã chi đủ: đã chi đủ theo số duyệt.",
      "Có phiếu nháp: có phiếu chi chưa xác nhận.",
      "Bị chặn theo chính sách: chưa đủ điều kiện chi tiếp.",
      "Thu vượt: công ty nhận nhiều hơn số xác nhận.",
      "Chi vượt: sale được chi nhiều hơn số duyệt.",
    ],
  },
  {
    title: "Cẩm nang sale BĐS",
    items: [
      "Bộ hướng dẫn nhanh giúp sale chăm sóc khách hàng bất động sản bài bản hơn.",
      "Bao gồm: checklist tư vấn khách, phân loại khách nóng/ấm/lạnh, nguyên tắc follow-up, mẫu ghi chú sale, lý do mất khách và các lỗi sale cần tránh.",
      "Lưu ý: Nội dung này là hướng dẫn nghiệp vụ phổ thông trong CRM, không phải tư vấn pháp lý chính thức.",
    ],
  },
  {
    title: "Checklist tư vấn khách hàng",
    items: [
      "Mục đích mua: ở thực, đầu tư, cho thuê, giữ tiền, mua cho người thân.",
      "Khu vực quan tâm.",
      "Ngân sách dự kiến.",
      "Số tiền có sẵn.",
      "Có cần vay ngân hàng không.",
      "Thời gian dự kiến mua.",
      "Loại sản phẩm quan tâm: căn hộ, nhà phố, đất nền, biệt thự, shophouse.",
      "Diện tích hoặc số phòng ngủ mong muốn.",
      "Tầng/hướng/view mong muốn nếu là căn hộ.",
      "Ai là người quyết định chính.",
      "Khách đã xem dự án/sản phẩm nào khác chưa.",
      "Điều khách thích nhất.",
      "Điều khách còn phân vân.",
      "Thời điểm có thể đi xem nhà/dự án.",
      "Kênh liên hệ thuận tiện: điện thoại, Zalo, Facebook, email.",
      "Nếu thiếu các thông tin này, sale rất khó tư vấn đúng sản phẩm và khó chốt lịch hẹn.",
    ],
  },
  {
    title: "Cách phân loại khách hàng",
    items: [],
    groups: [
      {
        title: "Khách nóng",
        items: [
          "Có nhu cầu rõ ràng.",
          "Có ngân sách/tài chính tương đối rõ.",
          "Có thời gian mua gần.",
          "Phản hồi tốt khi sale liên hệ.",
          "Sẵn sàng đi xem nhà/dự án hoặc trao đổi sâu.",
        ],
      },
      {
        title: "Khách ấm",
        items: [
          "Có quan tâm nhưng chưa quyết ngay.",
          "Đang so sánh nhiều lựa chọn.",
          "Cần thêm thông tin về giá, chính sách, pháp lý, vay ngân hàng.",
          "Cần chăm sóc định kỳ.",
        ],
      },
      {
        title: "Khách lạnh",
        items: [
          "Chỉ tham khảo.",
          "Chưa có tài chính rõ.",
          "Không có thời gian mua gần.",
          "Ít phản hồi hoặc phản hồi rất chậm.",
        ],
      },
      {
        title: "Khách không tiềm năng",
        items: [
          "Sai số.",
          "Không có nhu cầu.",
          "Không đúng phân khúc.",
          "Không đủ tài chính.",
          "Không muốn bị liên hệ lại.",
        ],
      },
      {
        title: "Gợi ý",
        items: [
          "Không nên đánh dấu khách là “mất” quá sớm nếu chưa khai thác đủ nhu cầu.",
          "Không nên giữ khách “nóng” nhưng không có lịch chăm sóc tiếp theo.",
        ],
      },
    ],
  },
  {
    title: "Nguyên tắc follow-up khách hàng",
    items: [
      "Lead mới nên được gọi càng sớm càng tốt.",
      "Sau mỗi lần gọi phải ghi chú kết quả.",
      "Nếu khách chưa quyết, phải tạo lịch chăm sóc tiếp theo.",
      "Khách đã xem nhà/dự án nên follow lại trong 24 giờ.",
      "Khách đang đàm phán cần cập nhật thường xuyên về giá, chính sách, giỏ hàng.",
      "Không để lead quá lâu không có hoạt động.",
      "Nếu khách không nghe máy, nên thử lại vào khung giờ khác và ghi chú rõ.",
      "Nếu khách hẹn gọi lại, phải tạo task/lịch hẹn.",
      "Nếu khách từ chối, nên ghi rõ lý do để leader/marketing phân tích.",
    ],
    groups: [
      {
        title: "Ưu tiên việc trong ngày",
        items: [
          "Khách hẹn gọi lại hôm nay.",
          "Khách đã xem nhà/dự án.",
          "Khách đang đàm phán.",
          "Lead mới chưa gọi.",
          "Lead lâu ngày chưa chăm sóc.",
          "Khách lạnh cần nuôi dưỡng.",
        ],
      },
    ],
  },
  {
    title: "Mẫu ghi chú sale chuẩn",
    items: [
      "Không nên ghi chú quá ngắn kiểu: “Đã gọi”, “Khách quan tâm”, “Hẹn lại”.",
      "Nhu cầu:",
      "Mục đích mua:",
      "Tài chính/ngân sách:",
      "Khu vực quan tâm:",
      "Sản phẩm đã tư vấn:",
      "Phản hồi của khách:",
      "Điều khách còn phân vân:",
      "Việc cần làm tiếp theo:",
      "Thời gian hẹn lại:",
      "Ví dụ ghi chú tốt: Khách mua ở thực, cần căn 2PN khu Hải Phòng, ngân sách 4–5 tỷ, có sẵn khoảng 2 tỷ và cần vay thêm. Đã tư vấn dự án Him Lam Green Park, khách quan tâm tầng trung, muốn xem nhà mẫu cuối tuần. Hẹn gọi lại 9h sáng thứ Bảy để chốt lịch xem.",
      "Ghi chú càng rõ, leader càng dễ hỗ trợ chốt deal.",
      "Ghi chú tốt giúp sale khác hiểu lịch sử nếu cần bàn giao khách.",
    ],
  },
  {
    title: "Lý do mất khách thường gặp",
    items: [
      "Sai số điện thoại.",
      "Không nghe máy nhiều lần.",
      "Không có nhu cầu.",
      "Chỉ tham khảo.",
      "Không đúng phân khúc.",
      "Chưa đủ tài chính.",
      "Giá quá cao.",
      "Không thích vị trí.",
      "Không thích thiết kế/mặt bằng.",
      "Không thích pháp lý.",
      "Không thích tiến độ thanh toán.",
      "Không vay được ngân hàng.",
      "Đã mua bên khác.",
      "Đã làm việc với sale/môi giới khác.",
      "Trùng khách.",
      "Khách yêu cầu không liên hệ lại.",
    ],
    groups: [
      {
        title: "Mục đích",
        items: [
          "Giúp leader biết lý do mất khách thật.",
          "Giúp marketing biết chất lượng lead.",
          "Giúp công ty tối ưu quảng cáo, sản phẩm, chính sách bán hàng.",
        ],
      },
    ],
  },
  {
    title: "Lỗi thường gặp của sale",
    items: [
      "Không gọi lead mới kịp thời.",
      "Gọi xong nhưng không ghi chú.",
      "Không tạo lịch chăm sóc tiếp theo.",
      "Để lead quá hạn.",
      "Không khai thác tài chính/ngân sách.",
      "Không hỏi ai là người quyết định chính.",
      "Không ghi lý do mất khách.",
      "Tạo trùng khách.",
      "Chuyển trạng thái khách nhưng không có hoạt động.",
      "Không kiểm tra lịch sử chăm sóc trước khi gọi.",
      "Không cập nhật kết quả sau khi khách đi xem nhà/dự án.",
      "Không báo leader khi khách đang đàm phán sâu.",
      "Nhầm khách chỉ tham khảo với khách có nhu cầu thật.",
    ],
  },
  {
    title: "Quy trình từ lead đến hợp đồng",
    items: [
      "Lead mới → Liên hệ → Khai thác nhu cầu → Tư vấn sản phẩm → Hẹn xem nhà/dự án → Booking/Giữ chỗ → Hợp đồng → Thanh toán → Phiếu thu/Hóa đơn → Hoa hồng → Đối soát",
    ],
    groups: [
      {
        title: "Giải thích từng bước",
        items: [
          "Lead mới: cần liên hệ nhanh.",
          "Khai thác nhu cầu: hỏi mục đích, tài chính, khu vực, thời gian mua.",
          "Tư vấn sản phẩm: chọn sản phẩm phù hợp với nhu cầu và ngân sách.",
          "Hẹn xem: tạo lịch hẹn rõ thời gian/địa điểm.",
          "Booking: ghi nhận khách giữ chỗ.",
          "Hợp đồng: giao dịch chính thức.",
          "Thanh toán: theo dõi tiền khách phải trả/đã trả.",
          "Hoa hồng: tính và duyệt hoa hồng theo hợp đồng.",
          "Đối soát: kiểm tra tiền công ty nhận, tiền sale được chi.",
        ],
      },
    ],
  },
];
