import zipfile
import io
import docx
from datetime import datetime
import base64

def test_full_docx_packaging():
    # 1x1 png image
    sample_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdH1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rIdImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
  <Relationship Id="rIdImg2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.png"/>
  <Relationship Id="rIdImg3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image3.png"/>
  <Relationship Id="rIdImg4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image4.png"/>
  <Relationship Id="rIdImg5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image5.png"/>
  <Relationship Id="rIdImg6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image6.png"/>
</Relationships>"""

    header_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="right"/></w:pPr>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t>BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH</w:t></w:r>
  </w:p>
</w:hdr>"""

    footer_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t>Trang </w:t></w:r>
    <w:fldSimple w:instr="PAGE"/>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t> / </w:t></w:r>
    <w:fldSimple w:instr="NUMPAGES"/>
  </w:p>
</w:ftr>"""

    def make_img_xml(rId, name):
        return f"""<w:p>
  <w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="120"/></w:pPr>
  <w:r>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
        <wp:extent cx="5400000" cy="2700000"/>
        <wp:docPr id="1" name="{name}"/>
        <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
              <pic:nvPicPr>
                <pic:cNvPr id="1" name="{name}.png"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="{rId}"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm><a:off x="0" y="0"/><a:ext cx="5400000" cy="2700000"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>"""

    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <!-- TITLE PAGE -->
    <w:p><w:pPr><w:spacing w:before="720"/></w:pPr></w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="44"/><w:color w:val="1E3A8A"/></w:rPr><w:t>BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="480"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="26"/><w:color w:val="475569"/></w:rPr><w:t>Báo cáo tự động chuẩn hóa từ Không gian phân tích</w:t></w:r>
    </w:p>
    
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="8000" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>Loại hình doanh nghiệp:</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>Bán lẻ</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>Kỳ dữ liệu phân tích:</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>01/10/2018 - 31/10/2019</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>Ngày xuất báo cáo:</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>{datetime.now().strftime('%d/%m/%Y %H:%M')}</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:p><w:r><w:br w:type="page"/></w:r></w:p>

    <!-- SECTION 1 -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>1. TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Trong kỳ đánh giá, tổng doanh thu thuần đạt 20.717.175.575 VND với tổng số 1.366 đơn hàng được hoàn tất. Lợi nhuận HĐKD đạt 4.545.922.957 VND, tương ứng tỷ suất sinh lời trên doanh thu (ROS) đạt 22.0%. Doanh thu tháng hiện tại đạt 1.666.023.008 VND với tốc độ tăng trưởng MoM đạt -3.0%. Nhóm mít và Nhóm xoài là các nhóm sản phẩm dẫn đầu về quy mô và lợi nhuận.</w:t></w:r></w:p>

    <!-- SECTION 2 -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>2. PHẠM VI VÀ DỮ LIỆU (SCOPE &amp; DATA)</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Báo cáo phân tích được thực hiện trên cơ sở bộ dữ liệu giao dịch sạch gồm 1.366 bản ghi với 7 trường thông tin nghiệp vụ. Hệ thống đã tự động thực hiện các thao tác tiền xử lý bao gồm: loại bỏ dòng trùng lặp, chuẩn hóa định dạng số tiền tệ và cắt bỏ khoảng trắng thừa ở các biến định tính. Mọi chỉ số tài chính đều được tính toán từ các trường số liệu kế toán thực tế.</w:t></w:r></w:p>

    <!-- SECTION 3 -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3. PHÂN TÍCH CHI TIẾT THEO BIỂU ĐỒ (DETAILED ANALYSIS)</w:t></w:r></w:p>
    
    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.1. Doanh thu theo nhóm sản phẩm (Kỳ báo cáo T10)</w:t></w:r></w:p>
    {make_img_xml("rIdImg1", "Biểu đồ 1")}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Trong tháng hiện tại, Nhóm mít dẫn đầu về quy mô doanh thu với 418 Millions VND, tiếp theo là Nhóm xoài đạt 398 Millions VND và Nhóm thơm đạt 363 Millions VND. Nhóm chuối ghi nhận mức thấp nhất với 222 Millions VND.</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.2. Lợi nhuận HĐKD theo nhóm sản phẩm</w:t></w:r></w:p>
    {make_img_xml("rIdImg2", "Biểu đồ 2")}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Về mặt lợi nhuận hoạt động kinh doanh, Nhóm xoài vươn lên vị trí số 1 đạt 91 Millions VND, xếp trên Nhóm thơm (88 Millions) và Nhóm mít (85 Millions). Hiệu quả sinh lời của Nhóm xoài vượt trội so với các nhóm còn lại.</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.3. Tỷ suất sinh lời ROS toàn công ty và tăng trưởng MoM</w:t></w:r></w:p>
    {make_img_xml("rIdImg3", "Biểu đồ 3")}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Tỷ suất sinh lời trên doanh thu thuần (ROS) toàn công ty trong tháng T10 đạt 22.0%, duy trì mức sinh lời lành mạnh trong ngành bán lẻ. Tăng trưởng doanh thu MoM so với tháng T09 đạt -3.0%.</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.4. Diễn biến doanh thu 12 tháng của nhóm hàng chủ lực</w:t></w:r></w:p>
    {make_img_xml("rIdImg4", "Biểu đồ 4")}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Doanh thu của Nhóm chuối ghi nhận đà tăng trưởng liên tục từ T01/2019 (284 Millions) đạt đỉnh tại T09/2019 (479 Millions) trước khi suy giảm đột ngột vào T10/2019 (222 Millions).</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.5. Tốc độ tăng trưởng doanh thu từng nhóm hàng theo chu kỳ (%)</w:t></w:r></w:p>
    {make_img_xml("rIdImg5", "Biểu đồ 5")}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Chỉ số tăng trưởng doanh thu so với kỳ gốc đạt 134% tại T09/2019 và giảm xuống 62% tại T10/2019 đối với Nhóm chuối, phản ánh tính biến động mạnh cần theo dõi.</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.6. Biên lợi nhuận ROS của nhóm hàng chủ lực</w:t></w:r></w:p>
    {make_img_xml("rIdImg6", "Biểu đồ 6")}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Biên lợi nhuận ROS của Nhóm chuối đạt 22.0% trong tháng T10, tương đồng với mức sinh lời chung của toàn công ty.</w:t></w:r></w:p>

    <!-- SECTION 4 -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="DC2626"/></w:rPr><w:t>4. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT (ISSUES TO RESOLVE)</w:t></w:r></w:p>
    
    <w:p><w:pPr><w:spacing w:after="80"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="26"/><w:color w:val="DC2626"/></w:rPr><w:t>[CAO] 1. Doanh thu Nhóm chuối sụt giảm mạnh 53.7% trong tháng T10</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Bằng chứng: Trong tháng T10, doanh thu Nhóm chuối đạt 222.000.000 VND, giảm 257.000.000 VND so với tháng T09 (479.000.000 VND).</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Tác động: Thất thoát trực tiếp 257.000.000 VND doanh thu, chiếm tỷ trọng sụt giảm lớn nhất toàn công ty.</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="160"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Hành động đề xuất: Rà soát lại chuỗi cung ứng và tồn kho; đánh giá nhu cầu thị trường; xúc tiến marketing cho các mặt hàng hồi phục nhanh.</w:t></w:r></w:p>

    <!-- SECTION 5 -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>5. KHUYẾN NGHỊ VÀ KẾ HOẠCH HÀNH ĐỘNG (ACTION PLAN)</w:t></w:r></w:p>
    
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="9000" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Hành động đề xuất</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Người phụ trách</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Thời hạn</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2200" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Chỉ số đo lường kỳ vọng</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Kiểm tra chuỗi cung ứng Nhóm chuối</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t></w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>2 tuần</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2200" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Tỷ lệ đủ hàng 98%</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Thúc đẩy truyền thông Nhóm xoài (ROS cao)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t></w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>1 tháng</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2200" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Tăng trưởng 15%</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>

    <!-- SECTION 6 -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>6. PHỤ LỤC (APPENDIX)</w:t></w:r></w:p>
    
    <w:p><w:pPr><w:spacing w:after="80"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="26"/></w:rPr><w:t>6.1. Công thức tính toán tài chính áp dụng:</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Doanh thu thuần = Doanh thu gộp − Chiết khấu − Hàng trả lại − Thuế</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Lợi nhuận HĐKD = Doanh thu thuần − Giá vốn (COGS) − Chi phí vận hành</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Biên lợi nhuận (ROS) = Lợi nhuận HĐKD ÷ Doanh thu thuần × 100%</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="140"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Giá trị đơn hàng trung bình (AOV) = Doanh thu thuần ÷ Tổng số đơn hàng</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:after="80"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="26"/></w:rPr><w:t>6.2. Bảng đối soát ánh xạ cột dữ liệu (Column Mapping):</w:t></w:r></w:p>
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="8500" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="334155"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Vai trò nhận diện nghiệp vụ</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="334155"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Tên cột trong tệp dữ liệu</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="334155"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Trạng thái xác thực</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Doanh thu thuần (Net revenue)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Doanh thu</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Khớp 100%</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Lợi nhuận HĐKD (Profit)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Lợi nhuận</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Khớp 100%</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Nhóm sản phẩm</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Nhóm sản phẩm</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Định danh chuẩn</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/_rels/document.xml.rels', doc_rels)
        z.writestr('word/header1.xml', header_xml)
        z.writestr('word/footer1.xml', footer_xml)
        for i in range(1, 7):
            z.writestr(f'word/media/image{i}.png', sample_png)
        z.writestr('word/document.xml', doc_xml)

    with open('test_client_docx.docx', 'wb') as f:
        f.write(buf.getvalue())
    print("Generated test_client_docx.docx successfully, size:", len(buf.getvalue()), "bytes")
    
    doc = docx.Document('test_client_docx.docx')
    print("Verified test_client_docx.docx - Paragraphs:", len(doc.paragraphs), "Tables:", len(doc.tables), "Shapes:", len(doc.inline_shapes))

test_full_docx_packaging()
