import pytest
import io
import docx
from fastapi.testclient import TestClient
from app import app, session
from core.exporter import export_to_docx
from core.data_loader import load_data_from_bytes
from core.cleaner import DataCleaner
from core.reporter import ReportEngine

client = TestClient(app)

def test_export_to_docx_structure():
    dashboard_data = {
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
            'chart1_revenue_by_group': {'analysis': 'Nhóm mít dẫn đầu doanh thu với 418 triệu VND.'},
            'chart2_profit_by_group': {'analysis': 'Nhóm xoài đạt lợi nhuận cao nhất với 91 triệu VND.'},
            'chart3_company_ros': {'analysis': 'ROS toàn công ty đạt 22%.'},
            'chart4_group_monthly_revenue': {'analysis': 'Diễn biến doanh thu nhóm chuối đạt đỉnh tại T09.'},
            'chart5_group_growth_index': {'analysis': 'Tăng trưởng doanh thu 134% tại T09.'},
            'chart6_group_ros': {'analysis': 'ROS của nhóm chuối đạt 22%.'}
        },
        'issues_to_resolve': [
            {
                'severity': 'CAO',
                'issue': 'Doanh thu Nhóm chuối sụt giảm 53.7%',
                'evidence': 'Giảm từ 479 triệu về 222 triệu VND.',
                'impact': 'Thất thoát 257 triệu VND.',
                'action': 'Rà soát chuỗi cung ứng.'
            }
        ]
    }
    
    docx_bytes = export_to_docx(dashboard_data, {}, {'business_type': 'retail'})
    assert len(docx_bytes) > 0
    
    doc = docx.Document(io.BytesIO(docx_bytes))
    paragraphs_text = [p.text for p in doc.paragraphs]
    full_text = "\n".join(paragraphs_text)
    
    # Verify Document Structure
    assert "BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH" in full_text
    assert "1. TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)" in full_text
    assert "2. PHẠM VI VÀ DỮ LIỆU (SCOPE & DATA)" in full_text
    assert "3. PHÂN TÍCH CHI TIẾT THEO BIỂU ĐỒ (DETAILED ANALYSIS)" in full_text
    assert "4. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT (ISSUES TO RESOLVE)" in full_text
    assert "5. KHUYẾN NGHỊ VÀ KẾ HOẠCH HÀNH ĐỘNG (ACTION PLAN)" in full_text
    assert "6. PHỤ LỤC (APPENDIX)" in full_text
    
    # Verify numbers
    assert "20.717.175.575" in full_text
    assert "1.366" in full_text
    assert "4.545.922.957" in full_text
    assert "22%" in full_text
    
    # Verify tables
    assert len(doc.tables) >= 3

def test_api_export_docx_endpoint():
    # Load sample data into session
    with open('doanh_thu_marketing.csv', 'rb') as f:
        csv_bytes = f.read()
    df, _ = load_data_from_bytes(csv_bytes, 'doanh_thu_marketing.csv')
    cleaner = DataCleaner(df)
    cleaner.auto_clean_all()
    roles = cleaner.detect_column_roles()
    clean_df = cleaner.df
    session.cleaned_df = clean_df
    session.cleaner = cleaner
    session.business_context = {'business_type': 'b2b'}
    session.report_engine = ReportEngine(clean_df, roles)
    session.last_dashboard_cache = session.report_engine.compute_dashboard('2019-10', 'Nhóm chuối')
    
    res = client.get("/api/export/docx")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "BaoCao_B2B_" in res.headers["content-disposition"]
    assert res.headers["content-disposition"].endswith('.docx"')

def test_standalone_index_html_contracts():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    # 1. Dropdown with exactly 2 options
    assert '<select id="input-biz-type"' in html
    assert '<option value="retail">Bán lẻ</option>' in html
    assert '<option value="b2b">Doanh nghiệp với doanh nghiệp (B2B)</option>' in html
    assert 'Chọn loại hình doanh nghiệp' in html
    
    # User cannot type custom value
    assert '<input type="text" id="input-biz-type"' not in html
    
    # 2. Export Word button
    assert "Xuất Báo cáo Word (.docx)" in html
    assert "app.exportFile('word')" in html
    
    # 3. JSZip inlined
    assert "JSZip" in html
    assert "exportWordDocx" in html
