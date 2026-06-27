import { Modal } from '../../components/Modal';

type FinanceReportGuideModalProps = {
  onClose: () => void;
};

function Formula({ children }: { children: string }) {
  return <p className="form-warning"><strong>Công thức:</strong> {children}</p>;
}

export function FinanceReportGuideModal({ onClose }: FinanceReportGuideModalProps) {
  return (
    <Modal title="Hướng dẫn sử dụng Báo cáo tài chính" onClose={onClose}>
      <div className="admin-form">
        <section>
          <h3>A. Mục đích màn hình</h3>
          <p>Báo cáo tài chính giúp theo dõi tổng giá trị hợp đồng, tiền cọc, số tiền đã thu, công nợ còn phải thu, các đợt thanh toán quá hạn, dòng tiền từ phiếu thu và tình trạng hóa đơn.</p>
        </section>

        <section>
          <h3>B. Ý nghĩa các chỉ số tổng quan</h3>
          <ul>
            <li><strong>Tổng giá trị hợp đồng:</strong> Tổng giá trị của các hợp đồng trong phạm vi bộ lọc.</li>
            <li><strong>Tổng tiền cọc:</strong> Tổng số tiền cọc đã ghi nhận trên hợp đồng.</li>
            <li><strong>Tổng đã thu gồm cọc:</strong> Tổng tiền đã thu gồm tiền cọc + các phiếu thu đã xác nhận.</li>
          </ul>
          <Formula>Tổng đã thu = Tiền cọc + Phiếu thu đã xác nhận.</Formula>
          <ul>
            <li><strong>Tổng còn phải thu:</strong> Số tiền còn phải thu từ khách.</li>
          </ul>
          <Formula>Còn phải thu = Giá trị hợp đồng - Tiền cọc - Phiếu thu đã xác nhận.</Formula>
          <ul>
            <li><strong>HĐ thanh toán đủ:</strong> Số hợp đồng có tổng đã thu lớn hơn hoặc bằng giá trị hợp đồng.</li>
            <li><strong>HĐ còn công nợ:</strong> Số hợp đồng vẫn còn số tiền phải thu.</li>
            <li><strong>PMT quá hạn:</strong> Số đợt thanh toán đã quá ngày đến hạn nhưng chưa thu đủ.</li>
            <li><strong>Tiền quá hạn:</strong> Tổng số tiền còn lại của các đợt thanh toán quá hạn.</li>
            <li><strong>Phiếu thu xác nhận:</strong> Số phiếu thu đang ở trạng thái đã xác nhận.</li>
            <li><strong>Tiền phiếu thu xác nhận:</strong> Tổng tiền của các phiếu thu đã xác nhận. Phiếu thu đã hủy không được tính.</li>
            <li><strong>Hóa đơn phát hành:</strong> Số hóa đơn đang ở trạng thái đã phát hành.</li>
            <li><strong>Giá trị hóa đơn phát hành:</strong> Tổng giá trị hóa đơn đã phát hành. Hóa đơn bản nháp và hóa đơn đã hủy không được tính.</li>
          </ul>
        </section>

        <section>
          <h3>C. Giải thích các tab</h3>
          <ul>
            <li><strong>Tổng quan:</strong> Dùng để xem nhanh các chỉ số tổng hợp. Không phải bảng chi tiết.</li>
            <li><strong>Công nợ hợp đồng:</strong> Cho biết từng hợp đồng còn phải thu bao nhiêu. Cột “Đã thu” = tiền cọc + phiếu thu đã xác nhận. Cột “Còn lại” = số tiền khách còn phải thanh toán. Cột “Nhóm tuổi nợ” cho biết công nợ đã quá hạn bao lâu.</li>
            <li><strong>PMT quá hạn:</strong> PMT là đợt/lịch thanh toán của hợp đồng. Một PMT được coi là quá hạn khi ngày đến hạn nhỏ hơn hôm nay và vẫn còn tiền chưa thu. PMT đã thanh toán đủ không xuất hiện trong danh sách quá hạn.</li>
            <li><strong>Dòng tiền đã thu:</strong> Hiển thị các phiếu thu. Phiếu thu đã xác nhận được tính vào số tiền đã thu. Phiếu thu đã hủy vẫn có thể hiển thị để đối chiếu, nhưng không được tính vào tổng tiền đã thu.</li>
            <li><strong>Hóa đơn:</strong> Hiển thị hóa đơn bản nháp, đã phát hành, đã hủy. Chỉ hóa đơn đã phát hành mới được tính vào tổng giá trị hóa đơn phát hành. Hóa đơn bản nháp và đã hủy không được tính vào tổng phát hành.</li>
          </ul>
        </section>

        <section>
          <h3>D. Giải thích bộ lọc</h3>
          <ul>
            <li><strong>Từ ngày / Đến ngày:</strong> Lọc dữ liệu theo khoảng thời gian phù hợp với từng loại báo cáo.</li>
            <li><strong>Tìm khách hàng:</strong> Tìm theo tên hoặc thông tin khách hàng nếu hệ thống hỗ trợ.</li>
            <li><strong>Mã hợp đồng:</strong> Tìm nhanh theo mã hợp đồng, ví dụ HD-000040.</li>
            <li><strong>Trạng thái HĐ:</strong> Lọc theo trạng thái hợp đồng.</li>
            <li><strong>Lọc:</strong> Áp dụng điều kiện lọc.</li>
            <li><strong>Xóa lọc:</strong> Xóa điều kiện lọc và tải lại dữ liệu mặc định.</li>
          </ul>
        </section>

        <section>
          <h3>E. Giải thích xuất CSV</h3>
          <p>Nút Xuất CSV dùng để tải dữ liệu của tab hiện tại về máy. File CSV có thể mở bằng Excel. Dữ liệu xuất ra phụ thuộc vào bộ lọc đang áp dụng.</p>
        </section>

        <section>
          <h3>F. Lưu ý nghiệp vụ quan trọng</h3>
          <ul>
            <li>Phiếu thu đã hủy không được tính vào tiền đã thu.</li>
            <li>Hóa đơn bản nháp không được tính vào giá trị hóa đơn phát hành.</li>
            <li>Hóa đơn đã hủy không được tính vào giá trị hóa đơn phát hành.</li>
            <li>Tiền cọc được tính vào tổng đã thu của hợp đồng.</li>
            <li>Một hợp đồng chỉ nên hoàn tất khi đã thu đủ tiền.</li>
            <li>Số liệu báo cáo phụ thuộc vào quyền truy cập của người dùng.</li>
            <li>Nếu không có quyền xuất báo cáo thì sẽ không thấy nút Xuất CSV.</li>
          </ul>
        </section>

        <footer className="modal-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Đóng</button>
        </footer>
      </div>
    </Modal>
  );
}
