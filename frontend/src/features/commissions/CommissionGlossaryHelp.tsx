import { useState } from 'react';

import { Modal } from '../../components/Modal';

export function CommissionGlossaryContent() {
  return (
    <div className="commission-glossary-body">
      <section className="commission-glossary-card">
        <h3>A. Hoa hồng công ty</h3>
        <p>Là khoản công ty được nhận từ chủ đầu tư / chủ đất / chủ nhà / đối tác / bên trả hoa hồng.</p>
        <p>Dùng để theo dõi khoản phải thu của công ty: dự kiến, xác nhận, đã nhận, còn phải thu.</p>
      </section>
      <section className="commission-glossary-card">
        <h3>B. Hoa hồng</h3>
        <p>Là khoản công ty trả cho sale nội bộ.</p>
        <p>Dùng để theo dõi khoản công ty phải chi cho sale: đủ điều kiện, đã duyệt, đã chi trả.</p>
      </section>
      <section className="commission-glossary-card commission-glossary-table-card">
        <h3>C. Bảng so sánh ngắn</h3>
        <div className="commission-glossary-table-wrap">
          <table className="commission-glossary-table">
            <thead><tr><th>Tiêu chí</th><th>Hoa hồng công ty</th><th>Hoa hồng</th></tr></thead>
            <tbody>
              <tr><td>Bản chất</td><td>Khoản phải thu của công ty</td><td>Khoản phải chi cho sale</td></tr>
              <tr><td>Người trả</td><td>Chủ đầu tư / chủ đất / chủ nhà / đối tác / bên trả HH</td><td>Công ty</td></tr>
              <tr><td>Người nhận</td><td>Công ty môi giới / phân phối</td><td>Sale nội bộ</td></tr>
              <tr><td>Mã</td><td>CCR-000001</td><td>COM-000001</td></tr>
              <tr><td>Mục đích theo dõi</td><td>Dự kiến, xác nhận, đã nhận, còn phải thu</td><td>Đủ điều kiện, đã duyệt, đã chi trả</td></tr>
            </tbody>
          </table>
        </div>
      </section>
      <section className="commission-glossary-card">
        <h3>D. Ví dụ</h3>
        <ul>
          <li>Chủ đầu tư trả công ty 40 triệu =&gt; <b>Hoa hồng công ty</b>.</li>
          <li>Công ty trả sale 8 triệu =&gt; <b>Hoa hồng</b>.</li>
        </ul>
      </section>
      <section className="commission-glossary-memory">
        <h3>E. Ghi nhớ nhanh</h3>
        <p><b>Hoa hồng công ty = công ty đi thu.</b></p>
        <p><b>Hoa hồng = công ty đi trả.</b></p>
      </section>
    </div>
  );
}

export function CommissionGlossaryHelpButton() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        className="commission-glossary-help-button"
        title="Phân biệt Hoa hồng công ty và Hoa hồng"
        aria-label="Phân biệt Hoa hồng công ty và Hoa hồng"
        onClick={() => setOpen(true)}
      >
        <span className="commission-glossary-help-icon">?</span>
        <span className="commission-glossary-help-text">Phân biệt</span>
      </button>
      {open && (
        <Modal title="Phân biệt Hoa hồng công ty và Hoa hồng" onClose={() => setOpen(false)}>
          <CommissionGlossaryContent />
          <footer className="modal-actions commission-modal-footer"><button type="button" className="secondary-button" onClick={() => setOpen(false)}>Đóng</button></footer>
        </Modal>
      )}
    </>
  );
}
