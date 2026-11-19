import os
import pytest
from fastapi.testclient import TestClient
from app import app, session

client = TestClient(app)

def test_full_e2e_pipeline():
    # 1. Reset
    res_reset = client.post("/api/reset")
    assert res_reset.status_code == 200

    # 2. Check initial state (Step 1 active, 2-4 locked)
    res_state = client.get("/api/state")
    assert res_state.status_code == 200
    state = res_state.json()
    assert state['current_step'] == 1
    assert state['step_unlocked']['2'] is False
    assert state['step_unlocked']['3'] is False
    assert state['step_unlocked']['4'] is False

    # 3. Fill Business Form
    form_payload = {
        'business_type': 'Bán lẻ nông sản & chế biến',
        'additional_info': 'Kênh phân phối toàn quốc',
        'questions': [
            "Doanh thu theo nhóm sản phẩm nào cao nhất?",
            "Tỷ suất lợi nhuận trên doanh thu (ROS) đạt bao nhiêu?",
            "Xu hướng tăng trưởng qua các kỳ biến động ra sao?"
        ]
    }
    res_form = client.post("/api/connect/form", json=form_payload)
    assert res_form.status_code == 200

    # 4. Load Sample Dataset
    res_sample = client.post("/api/connect/sample", json={'key': 'marketing_sales'})
    assert res_sample.status_code == 200
    sample_data = res_sample.json()
    assert sample_data['success'] is True
    assert sample_data['metadata']['row_count'] == 1366

    # 5. Complete Step 1 -> Should unlock Step 2
    res_c1 = client.post("/api/connect/complete")
    assert res_c1.status_code == 200
    assert res_c1.json()['current_step'] == 2

    # 6. Step 2: Clean & Normalize
    res_issues = client.get("/api/clean/issues")
    assert res_issues.status_code == 200
    issues = res_issues.json()['issues']

    # Auto clean
    res_clean = client.post("/api/clean/auto")
    assert res_clean.status_code == 200

    # Complete Step 2 -> Should unlock Step 3
    res_c2 = client.post("/api/clean/complete")
    assert res_c2.status_code == 200
    assert res_c2.json()['current_step'] == 3

    # 7. Step 3: Run Analysis
    res_an = client.post("/api/analyze/run")
    assert res_an.status_code == 200
    an_res = res_an.json()
    assert an_res['success'] is True
    assert len(an_res['analysis_results']['answers']) == 3
    assert an_res['current_step'] == 4

    # 8. Step 4: Executive Dashboard
    res_dash = client.get("/api/report/dashboard?month=2019-10&group=Nhóm%20chuối")
    assert res_dash.status_code == 200
    dash = res_dash.json()
    assert dash['kpis']['total_revenue'] == 20717175575.0
    assert dash['kpis']['month_revenue'] == 1666023008.0
    assert dash['kpis']['total_orders'] == 1366
    assert dash['kpis']['month_orders'] == 107
    assert dash['kpis']['company_ros'] == 22.0
    assert round(dash['kpis']['mom_growth']) == -3.0

    # Check written analysis text presence under charts
    assert dash['charts']['chart1_revenue_by_group']['analysis'] != ""
    assert dash['charts']['chart2_profit_by_group']['analysis'] != ""
    assert dash['charts']['chart3_company_ros']['analysis'] != ""
    assert dash['charts']['chart4_group_monthly_revenue']['analysis'] != ""
    assert dash['charts']['chart5_group_growth_index']['analysis'] != ""
    assert dash['charts']['chart6_group_ros']['analysis'] != ""

    # 9. Test Exports
    # CSV Export
    res_csv = client.get("/api/export/csv")
    assert res_csv.status_code == 200
    assert len(res_csv.content) > 1000

    # Excel Export
    res_excel = client.get("/api/export/excel")
    assert res_excel.status_code == 200
    assert len(res_excel.content) > 2000

    # PDF Export
    res_pdf = client.get("/api/export/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.content.startswith(b'%PDF')
