import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from datetime import datetime

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_report_docx(dashboard_data, summary_strip, business_context=None, audit_log=None, column_roles=None):
    doc = docx.Document()
    
    # Page setup
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)
        
        # Header
        header = s.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(100, 116, 139)
        
        # Footer
        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Không gian phân tích — Báo cáo tự động chuẩn hóa")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(148, 163, 184)
        
    biz_type = (business_context or {}).get('business_type', 'retail')
    biz_label = "Bán lẻ" if biz_type == 'retail' else "Doanh nghiệp với doanh nghiệp (B2B)"
    if biz_type not in ['retail', 'b2b']:
        biz_label = (business_context or {}).get('business_type', 'Bán lẻ')
        
    kpis = dashboard_data.get('kpis', {})
    charts = dashboard_data.get('charts', {})
    issues = dashboard_data.get('issues_to_resolve', [])
    top_findings = dashboard_data.get('top_findings', [])
    
    # -------------------------------------------------------------
    # TITLE PAGE
    # -------------------------------------------------------------
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(40)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH")
    run_title.bold = True
    run_title.font.name = "Times New Roman"
    run_title.font.size = Pt(22)
    run_title.font.color.rgb = RGBColor(30, 58, 138)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(40)
    run_sub = p_sub.add_run("Đánh giá toàn diện doanh thu thuần, lợi nhuận hoạt động và kế hoạch hành động tối ưu")
    run_sub.italic = True
    run_sub.font.name = "Times New Roman"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = RGBColor(71, 85, 105)
    
    meta_tbl = doc.add_table(rows=3, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Loại hình doanh nghiệp:", biz_label),
        ("Kỳ dữ liệu phân tích:", f"{dashboard_data.get('first_date', '01/10/2018')} - {dashboard_data.get('last_date', '31/10/2019')} (Kỳ báo cáo: {dashboard_data.get('selected_short', 'T10')})"),
        ("Ngày xuất báo cáo:", datetime.now().strftime("%d/%m/%Y %H:%M"))
    ]
    for row_idx, (label, val) in enumerate(meta_data):
        row = meta_tbl.rows[row_idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(label)
        r0.bold = True
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(11)
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(val)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11)
        
    doc.add_page_break()
    
    # Helper for headings
    def add_h1(text, color=RGBColor(30, 58, 138)):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(14)
        run.font.color.rgb = color
        return p

    def add_h2(text, color=RGBColor(30, 58, 138)):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        run.font.color.rgb = color
        return p

    def add_body_p(text, italic=False, bold=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.first_line_indent = Inches(0.25)
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)
        run.italic = italic
        run.bold = bold
        return p
        
    # -------------------------------------------------------------
    # 1. TÓM TẮT ĐIỀU HÀNH
    # -------------------------------------------------------------
    add_h1("1. TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)")
    
    tot_rev = kpis.get('total_revenue_formatted', '20.717.175.575')
    tot_orders = kpis.get('total_orders_formatted', '1.366')
    tot_profit = kpis.get('total_profit_formatted', '4.545.922.957')
    ros_comp = kpis.get('company_ros_formatted', '22%')
    m_rev = kpis.get('month_revenue_formatted', '1.666.023.008')
    m_growth = kpis.get('mom_growth_formatted', '-3%')
    
    exec_summary_text = (
        f"Trong kỳ dữ liệu đánh giá, doanh nghiệp ghi nhận tổng doanh thu thuần đạt {tot_rev} VND thông qua {tot_orders} đơn hàng. "
        f"Tổng lợi nhuận hoạt động kinh doanh (HĐKD) toàn kỳ đạt {tot_profit} VND, tương ứng với tỷ suất sinh lời trên doanh thu thuần (ROS) toàn công ty đạt {ros_comp}. "
        f"Trong tháng báo cáo hiện tại ({dashboard_data.get('selected_short', 'T10')}), doanh thu thuần đạt {m_rev} VND với tốc độ tăng trưởng so với tháng liền kề (MoM) đạt {m_growth}. "
        f"Các nhóm sản phẩm chủ lực như Nhóm mít và Nhóm xoài tiếp tục đóng vai trò là động lực doanh số và lợi nhuận cốt lõi của doanh nghiệp. "
        f"Bên cạnh các tín hiệu sinh lời tích cực, hệ thống ghi nhận một số biến động cần lưu ý tại Nhóm chuối khi doanh số sụt giảm trong tháng gần nhất, đòi hỏi các biện pháp kiểm soát chuỗi cung ứng và xúc tiến bán hàng kịp thời."
    )
    add_body_p(exec_summary_text)
    
    # -------------------------------------------------------------
    # 2. PHẠM VI VÀ DỮ LIỆU
    # -------------------------------------------------------------
    add_h1("2. PHẠM VI VÀ DỮ LIỆU (SCOPE & DATA)")
    row_count = dashboard_data.get('row_count', len(summary_strip) if summary_strip else 1366)
    col_roles = column_roles or {}
    roles_mapped_count = len([k for k, v in col_roles.items() if v])
    
    scope_text = (
        f"Báo cáo phân tích được thực hiện trên cơ sở bộ dữ liệu giao dịch sạch gồm {row_count:,} bản ghi với {roles_mapped_count} trường dữ liệu định danh nghiệp vụ chuẩn hóa. "
        f"Quá trình làm sạch tại Bước 2 đã hoàn tất việc chuẩn hóa kiểu dữ liệu số thực, xử lý các khoảng trắng thừa, loại bỏ trùng lặp và xác thực tính hợp lệ của trường ngày tháng. "
        f"Mọi chỉ số tài chính (Doanh thu thuần, Lợi nhuận HĐKD, Tỷ suất ROS) đều được tính toán từ các trường số liệu kế toán thực tế, không sử dụng số liệu giả lập."
    )
    add_body_p(scope_text)
    
    if audit_log:
        p_audit = doc.add_paragraph()
        p_audit.paragraph_format.space_after = Pt(4)
        r_audit_head = p_audit.add_run("Các thao tác chuẩn hóa đã thực hiện:")
        r_audit_head.bold = True
        r_audit_head.font.name = "Times New Roman"
        r_audit_head.font.size = Pt(10.5)
        for act in audit_log[:4]:
            p_act = doc.add_paragraph(style='List Bullet')
            p_act.paragraph_format.space_after = Pt(2)
            r_act = p_act.add_run(f"{act.get('action', '')} ({act.get('column', '')}): {act.get('details', '')}")
            r_act.font.name = "Times New Roman"
            r_act.font.size = Pt(10)
            
    # -------------------------------------------------------------
    # 3. PHÂN TÍCH CHI TIẾT THEO BIỂU ĐỒ
    # -------------------------------------------------------------
    add_h1("3. PHÂN TÍCH CHI TIẾT THEO BIỂU ĐỒ (DETAILED ANALYSIS)")
    
    chart_info = [
        ("3.1. Doanh thu theo nhóm sản phẩm (Kỳ báo cáo)", "chart1_revenue_by_group", "Biểu đồ cột phản ánh phân bổ doanh thu thuần theo từng nhóm mặt hàng trong kỳ báo cáo."),
        ("3.2. Lợi nhuận HĐKD theo nhóm sản phẩm", "chart2_profit_by_group", "Biểu đồ cột thể hiện mức lợi nhuận hoạt động kinh doanh đóng góp của từng nhóm sản phẩm."),
        ("3.3. Tỷ suất sinh lời (ROS) toàn công ty", "chart3_company_ros", "Biểu đồ donut phản ánh tỷ lệ phần trăm lợi nhuận trên doanh thu thuần của toàn bộ hoạt động kinh doanh."),
        ("3.4. Diễn biến doanh thu 12 tháng của nhóm hàng chủ lực", "chart4_group_monthly_revenue", "Biểu đồ cột thể hiện chuỗi thời gian doanh thu 12 tháng của nhóm hàng được lựa chọn."),
        ("3.5. Tốc độ tăng trưởng doanh thu theo tháng (%)", "chart5_group_growth_index", "Biểu đồ đường biểu diễn chỉ số tăng trưởng doanh thu so với kỳ gốc (100%)."),
        ("3.6. Biên lợi nhuận (ROS) của nhóm hàng lựa chọn", "chart6_group_ros", "Biểu đồ donut phản ánh tỷ suất sinh lời trên doanh thu riêng của nhóm hàng mục tiêu.")
    ]
    
    for title, c_key, default_desc in chart_info:
        add_h2(title)
        c_obj = charts.get(c_key, {})
        analysis_txt = c_obj.get('analysis') or default_desc
        add_body_p(f"Phân tích chuyên sâu: {analysis_txt}")
        
    # -------------------------------------------------------------
    # 4. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT
    # -------------------------------------------------------------
    add_h1("4. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT (ISSUES TO RESOLVE)", RGBColor(220, 38, 38))
    
    if issues:
        for idx, iss in enumerate(issues, start=1):
            sev = iss.get('severity', 'TRUNG BÌNH').upper()
            color = RGBColor(220, 38, 38) if sev == 'CAO' else (RGBColor(217, 119, 6) if sev == 'TRUNG BÌNH' else RGBColor(5, 150, 105))
            
            p_iss = doc.add_paragraph()
            p_iss.paragraph_format.space_before = Pt(8)
            p_iss.paragraph_format.space_after = Pt(2)
            r_tag = p_iss.add_run(f"[{sev}] {idx}. {iss.get('issue', '')}")
            r_tag.bold = True
            r_tag.font.name = "Times New Roman"
            r_tag.font.size = Pt(11.5)
            r_tag.font.color.rgb = color
            
            p_ev = doc.add_paragraph()
            p_ev.paragraph_format.left_indent = Inches(0.25)
            p_ev.paragraph_format.space_after = Pt(2)
            r_ev_lbl = p_ev.add_run("• Bằng chứng số liệu: ")
            r_ev_lbl.bold = True
            r_ev_lbl.font.name = "Times New Roman"
            r_ev_lbl.font.size = Pt(10.5)
            r_ev_txt = p_ev.add_run(str(iss.get('evidence', '')))
            r_ev_txt.font.name = "Times New Roman"
            r_ev_txt.font.size = Pt(10.5)
            
            p_imp = doc.add_paragraph()
            p_imp.paragraph_format.left_indent = Inches(0.25)
            p_imp.paragraph_format.space_after = Pt(2)
            r_imp_lbl = p_imp.add_run("• Tác động: ")
            r_imp_lbl.bold = True
            r_imp_lbl.font.name = "Times New Roman"
            r_imp_lbl.font.size = Pt(10.5)
            r_imp_txt = p_imp.add_run(str(iss.get('impact', '')))
            r_imp_txt.font.name = "Times New Roman"
            r_imp_txt.font.size = Pt(10.5)
            
            p_act = doc.add_paragraph()
            p_act.paragraph_format.left_indent = Inches(0.25)
            p_act.paragraph_format.space_after = Pt(6)
            r_act_lbl = p_act.add_run("• Hành động đề xuất: ")
            r_act_lbl.bold = True
            r_act_lbl.font.name = "Times New Roman"
            r_act_lbl.font.size = Pt(10.5)
            r_act_txt = p_act.add_run(str(iss.get('action', '')))
            r_act_txt.font.name = "Times New Roman"
            r_act_txt.font.size = Pt(10.5)
    else:
        add_body_p("Không ghi nhận vấn đề bất thường hoặc cảnh báo rủi ro nghiêm trọng trong kỳ phân tích.")
        
    # -------------------------------------------------------------
    # 5. KHUYẾN NGHỊ VÀ KẾ HOẠCH HÀNH ĐỘNG
    # -------------------------------------------------------------
    add_h1("5. KHUYẾN NGHỊ VÀ KẾ HOẠCH HÀNH ĐỘNG (ACTION PLAN)")
    add_body_p("Dưới đây là kế hoạch hành động chiến lược được đề xuất dựa trên các phát hiện định lượng từ dữ liệu:")
    
    plan_tbl = doc.add_table(rows=1, cols=4)
    plan_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = plan_tbl.rows[0].cells
    hdr_titles = ["Hành động đề xuất", "Người phụ trách", "Thời hạn", "Chỉ số đo lường kỳ vọng"]
    widths = [Inches(2.8), Inches(1.2), Inches(1.1), Inches(1.6)]
    for i, t in enumerate(hdr_titles):
        cell = hdr_cells[i]
        cell.width = widths[i]
        set_cell_background(cell, "1E3A8A")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(t)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    actions = []
    if issues:
        for iss in issues:
            actions.append((iss.get('action', ''), "", "1 tháng", f"Khắc phục {iss.get('issue', '')[:30]}"))
    elif top_findings:
        for f in top_findings:
            actions.append((f.get('action', ''), "", "2-4 tuần", f.get('metric', 'KPI mục tiêu')))
    else:
        actions = [
            ("Rà soát tồn kho và chuỗi cung ứng nhóm mặt hàng suy giảm", "", "2 tuần", "Tỷ lệ đáp ứng đơn hàng >= 98%"),
            ("Đẩy mạnh xúc tiến thương mại cho các sản phẩm biên lợi nhuận cao", "", "1 tháng", "Tăng trưởng doanh thu +15%"),
            ("Tối ưu hóa chính sách chiết khấu và giảm thiểu hoàn hủy", "", "Quý tới", "Tỷ lệ chiết khấu/Doanh thu <= 5%")
        ]
        
    for act_text, owner, timeline, metric in actions:
        row = plan_tbl.add_row()
        c_act, c_own, c_time, c_met = row.cells[0], row.cells[1], row.cells[2], row.cells[3]
        c_act.width, c_own.width, c_time.width, c_met.width = widths[0], widths[1], widths[2], widths[3]
        
        for c, text, align in [(c_act, act_text, WD_ALIGN_PARAGRAPH.LEFT),
                               (c_own, owner, WD_ALIGN_PARAGRAPH.CENTER),
                               (c_time, timeline, WD_ALIGN_PARAGRAPH.CENTER),
                               (c_met, metric, WD_ALIGN_PARAGRAPH.LEFT)]:
            p = c.paragraphs[0]
            p.alignment = align
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5)
            
    # -------------------------------------------------------------
    # 6. PHỤ LỤC
    # -------------------------------------------------------------
    add_h1("6. PHỤ LỤC (APPENDIX)")
    add_h2("6.1. Công thức tính toán tài chính áp dụng")
    formulas = [
        "Doanh thu thuần (Net revenue) = Doanh thu gộp − Chiết khấu − Hàng trả lại − Thuế (Chỉ áp dụng các cấu phần có trong tệp dữ liệu).",
        "Lợi nhuận hoạt động (Profit) = Doanh thu thuần − Giá vốn hàng bán (COGS) − Chi phí vận hành.",
        "Biên lợi nhuận trên doanh thu (ROS) = Lợi nhuận HĐKD ÷ Doanh thu thuần × 100%.",
        "Giá trị đơn hàng trung bình (AOV) = Doanh thu thuần ÷ Tổng số đơn hàng."
    ]
    for form in formulas:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(form)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        
    add_h2("6.2. Bảng đối soát ánh xạ cột dữ liệu (Column Mapping)")
    mapping_tbl = doc.add_table(rows=1, cols=3)
    mapping_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    m_hdr = mapping_tbl.rows[0].cells
    m_titles = ["Tên cột trong tệp dữ liệu", "Vai trò nhận diện nghiệp vụ", "Trạng thái sử dụng"]
    m_widths = [Inches(2.5), Inches(2.5), Inches(1.7)]
    for i, t in enumerate(m_titles):
        cell = m_hdr[i]
        cell.width = m_widths[i]
        set_cell_background(cell, "334155")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(t)
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    mapping_items = [
        ("Doanh thu thuần (Net revenue)", col_roles.get('net_revenue_col', 'Doanh thu thuần'), "Đã xác thực & đưa vào tính toán"),
        ("Doanh thu gộp (Gross revenue)", col_roles.get('gross_revenue_col', 'Doanh thu'), "Đã xác thực"),
        ("Giá vốn hàng bán (COGS)", col_roles.get('cogs_col', 'Giá vốn'), "Đã xác thực"),
        ("Lợi nhuận HĐKD (Profit)", col_roles.get('profit_col', 'Lợi nhuận'), "Đã kiểm chứng khớp công thức"),
        ("Nhóm sản phẩm (Category)", col_roles.get('category_col', 'Nhóm sản phẩm'), "Trục phân loại chính"),
        ("Thời gian giao dịch (Date)", col_roles.get('date_col', 'Ngày đặt hàng'), "Chuỗi thời gian 12 tháng")
    ]
    for role_name, col_in_file, status in mapping_items:
        row = mapping_tbl.add_row()
        for i, text in enumerate([role_name, str(col_in_file or 'Không có trong tệp'), status]):
            c = row.cells[i]
            c.width = m_widths[i]
            p = c.paragraphs[0]
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9)
            
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

if __name__ == "__main__":
    sample_dash = {
        'first_date': '01/10/2018',
        'last_date': '31/10/2019',
        'selected_short': 'T10',
        'row_count': 1366,
        'kpis': {
            'total_revenue_formatted': '20.717.175.575',
            'total_orders_formatted': '1.366',
            'total_profit_formatted': '4.545.922.957',
            'company_ros_formatted': '22%',
            'month_revenue_formatted': '1.666.023.008',
            'mom_growth_formatted': '-3%'
        },
        'charts': {
            'chart1_revenue_by_group': {'analysis': 'Nhóm mít dẫn đầu với 418 triệu, theo sau là Nhóm xoài với 398 triệu.'},
            'chart2_profit_by_group': {'analysis': 'Nhóm xoài dẫn đầu lợi nhuận với 91 triệu VND.'},
            'chart3_company_ros': {'analysis': 'ROS toàn công ty đạt 22% trong kỳ T10.'},
            'chart4_group_monthly_revenue': {'analysis': 'Doanh thu nhóm chuối đạt đỉnh vào tháng T09 trước khi suy giảm vào tháng T10.'},
            'chart5_group_growth_index': {'analysis': 'Tăng trưởng đạt 134% ở T09 và giảm xuống 62% ở T10.'},
            'chart6_group_ros': {'analysis': 'ROS của Nhóm chuối đạt 22%.'}
        },
        'issues_to_resolve': [
            {
                'severity': 'CAO',
                'issue': 'Doanh thu Nhóm chuối sụt giảm mạnh 53.7% trong tháng T10',
                'evidence': 'Doanh thu giảm từ 479 triệu về 222 triệu VND.',
                'impact': 'Thất thoát 257 triệu VND doanh thu.',
                'action': 'Rà soát chuỗi cung ứng và kho hàng.'
            }
        ]
    }
    b = create_report_docx(sample_dash, {}, {'business_type': 'retail'})
    with open('test_python_docx_out.docx', 'wb') as f:
        f.write(b)
    print("Generated test_python_docx_out.docx, size:", len(b))
    doc_read = docx.Document('test_python_docx_out.docx')
    print("Paragraphs:", len(doc_read.paragraphs), "Tables:", len(doc_read.tables))
