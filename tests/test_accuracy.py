import os
import pytest
import pandas as pd
import numpy as np
from core.data_loader import load_data_from_bytes
from core.reporter import ReportEngine

def test_independent_accuracy_verification():
    """
    Addendum 1 Requirement:
    Recompute each KPI independently from the raw sample file
    and assert exact equality with the ReportEngine dashboard output.
    """
    csv_path = os.path.join('data', 'doanh_thu_marketing.csv')
    assert os.path.exists(csv_path), "Sample dataset doanh_thu_marketing.csv must exist."

    # Load raw data with pandas independently
    raw_df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # Independent Manual Calculations:
    # 1. Total revenue for the whole period
    expected_total_revenue = float(raw_df['Doanh thu'].sum())
    assert expected_total_revenue == 20717175575.0, f"Expected 20,717,175,575 but got {expected_total_revenue}"

    # 2. Total order count
    expected_total_orders = len(raw_df['Mã đơn hàng'].unique())
    assert expected_total_orders == 1366, f"Expected 1,366 but got {expected_total_orders}"

    # 3. Filter for month T10-2019 (2019-10)
    raw_df['YM'] = raw_df['Ngày đặt hàng'].str.slice(0, 7)
    t10_df = raw_df[raw_df['YM'] == '2019-10']

    expected_t10_revenue = float(t10_df['Doanh thu'].sum())
    assert expected_t10_revenue == 1666023008.0, f"Expected 1,666,023,008 but got {expected_t10_revenue}"

    expected_t10_orders = len(t10_df['Mã đơn hàng'].unique())
    assert expected_t10_orders == 107, f"Expected 107 but got {expected_t10_orders}"

    # 4. Total company profit and ROS in T10
    expected_t10_profit = float(t10_df['Lợi nhuận HĐKD'].sum())
    expected_t10_ros = round((expected_t10_profit / expected_t10_revenue) * 100, 0)
    assert expected_t10_ros == 22.0, f"Expected 22% but got {expected_t10_ros}"

    # 5. Month-over-month growth from T09-2019 to T10-2019
    t09_df = raw_df[raw_df['YM'] == '2019-09']
    t09_revenue = float(t09_df['Doanh thu'].sum())
    expected_mom_growth = round(((expected_t10_revenue - t09_revenue) / t09_revenue) * 100, 1)
    assert round(expected_mom_growth) == -3.0, f"Expected -3% growth but got {expected_mom_growth}"

    # 6. Group by product group in T10
    grp_t10 = t10_df.groupby('Nhóm sản phẩm')['Doanh thu'].sum() / 1e6
    assert round(grp_t10['Nhóm chuối']) == 222
    assert round(grp_t10['Nhóm khoai']) == 264
    assert round(grp_t10['Nhóm mít']) == 418
    assert round(grp_t10['Nhóm thơm']) == 363
    assert round(grp_t10['Nhóm xoài']) == 399

    # Now verify with ReportEngine
    roles = {
        'date_col': 'Ngày đặt hàng',
        'category_col': 'Nhóm sản phẩm',
        'revenue_col': 'Doanh thu',
        'profit_col': 'Lợi nhuận HĐKD',
        'order_col': 'Mã đơn hàng',
        'channel_col': 'Kênh bán hàng'
    }
    engine = ReportEngine(raw_df, roles)
    dash = engine.compute_dashboard(selected_ym='2019-10', selected_group='Nhóm chuối')
    kpis = dash['kpis']

    # Assert strict equality between independently computed values and ReportEngine
    assert kpis['total_revenue'] == expected_total_revenue
    assert kpis['month_revenue'] == expected_t10_revenue
    assert kpis['total_orders'] == expected_total_orders
    assert kpis['month_orders'] == expected_t10_orders
    assert kpis['company_ros'] == expected_t10_ros
    assert round(kpis['mom_growth']) == -3.0

    # Summary strip test
    strip = engine.compute_summary_strip()
    assert strip['total_revenue'] == expected_total_revenue
    assert strip['row_count'] == len(raw_df)
    assert strip['top_category'] != ""
