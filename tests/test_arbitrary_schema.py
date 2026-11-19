import os
import pytest
import pandas as pd
from core.data_loader import load_sample_dataset
from core.cleaner import DataCleaner
from core.analyzer import DataAnalyzer
from core.reporter import ReportEngine

def test_arbitrary_schema_retail_logistics():
    """
    Addendum 7 Acceptance Test:
    Upload a raw CSV with a completely different schema (ban_le_logistics.csv).
    Verify that the system detects/maps roles and produces the exact executive dashboard layout
    with verified numbers and without errors.
    """
    df, meta = load_sample_dataset('retail_logistics')
    assert len(df) == 1502
    assert 'Tong_Tien' in df.columns
    assert 'Nganh_Hang' in df.columns

    # 1. Cleaner role detection
    cleaner = DataCleaner(df)
    cleaner.auto_clean_all()
    roles = cleaner.detect_column_roles()

    assert roles['revenue_col'] == 'Tong_Tien'
    assert roles['category_col'] == 'Nganh_Hang'
    assert roles['date_col'] == 'Ngay_Giao_Dich'
    assert roles['profit_col'] == 'Loi_Nhuan_Rong'
    assert roles['order_col'] == 'Ma_Van_Don'

    # 2. Analyze
    biz_context = {
        'business_type': 'Bán lẻ đa kênh',
        'questions': ["Ngành hàng nào có tổng tiền cao nhất?"]
    }
    analyzer = DataAnalyzer(cleaner.df, roles, biz_context)
    stats = analyzer.compute_summary_stats()
    answers = analyzer.answer_business_questions(biz_context['questions'])
    assert len(answers) == 1
    assert answers[0]['answer'] != ""

    # 3. Report Engine dashboard generation
    engine = ReportEngine(cleaner.df, roles, biz_context)
    strip = engine.compute_summary_strip()
    assert strip['total_revenue'] > 0
    assert strip['row_count'] == len(cleaner.df)

    dash = engine.compute_dashboard()
    assert dash['kpis']['total_revenue'] == strip['total_revenue']
    assert dash['charts']['chart1_revenue_by_group']['data'] != []
    assert dash['charts']['chart2_profit_by_group']['data'] != []
    assert dash['charts']['chart4_group_monthly_revenue']['values'] != []
    assert dash['charts']['chart5_group_growth_index']['values'] != []
    assert dash['top_findings'] != []
