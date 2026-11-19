import pytest
import pandas as pd
import numpy as np
from core.analyzer import DataAnalyzer

def test_analyzer_statistics():
    df = pd.DataFrame({
        'Ngày': ['2019-10-01', '2019-10-02', '2019-10-03', '2019-10-04'],
        'Nhóm': ['A', 'B', 'A', 'C'],
        'Doanh thu': [100.0, 200.0, 300.0, 400.0],
        'Lợi nhuận': [20.0, 40.0, 60.0, 80.0]
    })
    roles = {
        'date_col': 'Ngày',
        'category_col': 'Nhóm',
        'revenue_col': 'Doanh thu',
        'profit_col': 'Lợi nhuận'
    }
    analyzer = DataAnalyzer(df, roles)
    stats = analyzer.compute_summary_stats()

    num_stats = stats['numeric_columns']
    assert num_stats['Doanh thu']['sum'] == 1000.0
    assert num_stats['Doanh thu']['mean'] == 250.0
    assert num_stats['Doanh thu']['min'] == 100.0
    assert num_stats['Doanh thu']['max'] == 400.0

    cat_stats = stats['categorical_columns']
    assert cat_stats['Nhóm']['distinct_count'] == 3
    assert cat_stats['Nhóm']['top_value'] == 'A'

def test_analyzer_correlations():
    df = pd.DataFrame({
        'Doanh thu': [100.0, 200.0, 300.0, 400.0],
        'Lợi nhuận': [20.0, 40.0, 60.0, 80.0],
        'Chi phí': [80.0, 160.0, 240.0, 320.0]
    })
    analyzer = DataAnalyzer(df, {})
    corr = analyzer.compute_correlations()
    assert len(corr['columns']) == 3
    assert corr['matrix'][0][0] == 1.0
    # Revenue and Profit are perfectly correlated
    assert abs(corr['matrix'][0][1] - 1.0) < 1e-4

def test_analyzer_business_questions():
    df = pd.DataFrame({
        'Kênh bán hàng': ['Đại lý', 'Shopee', 'Đại lý'],
        'Doanh thu': [50000000.0, 30000000.0, 20000000.0],
        'Lợi nhuận HĐKD': [10000000.0, 6000000.0, 4000000.0]
    })
    roles = {
        'channel_col': 'Kênh bán hàng',
        'revenue_col': 'Doanh thu',
        'profit_col': 'Lợi nhuận HĐKD'
    }
    analyzer = DataAnalyzer(df, roles)
    questions = ["Doanh thu theo kênh nào cao nhất?"]
    answers = analyzer.answer_business_questions(questions)

    assert len(answers) == 1
    assert "Đại lý" in answers[0]['answer']
    assert "70.000.000" in answers[0]['answer']
