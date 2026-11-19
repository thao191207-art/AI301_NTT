import pytest
import pandas as pd
import numpy as np
from core.cleaner import DataCleaner
from core.data_loader import detect_delimiter, detect_encoding, detect_column_types

def test_data_loader_utilities():
    csv_sample = "Mã đơn hàng,Ngày đặt hàng,Doanh thu\nDH-01,2023-01-01,1000000"
    delim = detect_delimiter(csv_sample)
    assert delim == ','

    tsv_sample = "Mã\tNgày\tDoanhThu\n1\t2023-01-01\t500"
    delim_tsv = detect_delimiter(tsv_sample)
    assert delim_tsv == '\t'

    raw_utf8 = "Xin chào Việt Nam".encode('utf-8')
    assert detect_encoding(raw_utf8) == 'utf-8'

def test_cleaner_detect_issues():
    df = pd.DataFrame({
        'id': [1, 2, 2, 4],
        'name': [' Hà Nội ', 'HÀ NỘI', 'HÀ NỘI', 'Đà Nẵng'],
        'revenue': ['1.000.000 đ', '2,500,000', '2,500,000', ' 500.000 ₫ '],
        'date': ['2023-01-01', '02/01/2023', '02/01/2023', '2023-01-04'],
        'notes': ['ok', None, None, '']
    })

    cleaner = DataCleaner(df)
    issues = cleaner.detect_issues()

    assert issues['duplicates_count'] == 1
    assert 'notes' in issues['missing_values']
    assert 'revenue' in issues['numeric_as_text']
    assert 'name' in issues['casing_inconsistencies']

def test_cleaner_actions():
    df = pd.DataFrame({
        'id': [1, 2, 2, 3],
        'category': ['  Chuối ', 'Chuối', 'Chuối', 'Khoai'],
        'revenue': ['222.000.000 đ', '264.000.000 đ', '264.000.000 đ', '418.000.000 đ'],
        'profit': [49.0, np.nan, np.nan, 85.0]
    })

    cleaner = DataCleaner(df)
    
    # 1. Drop duplicates
    log1 = cleaner.apply_action('drop_duplicates')
    assert len(cleaner.df) == 3
    assert log1['rows_changed'] == 1

    # 2. Fill missing
    log2 = cleaner.apply_action('fill_missing', column='profit', params={'method': 'zero'})
    assert cleaner.df['profit'].isna().sum() == 0
    assert cleaner.df.loc[1, 'profit'] == 0

    # 3. Standardize numeric
    log3 = cleaner.apply_action('standardize_numeric', column='revenue')
    assert cleaner.df['revenue'].iloc[0] == 222000000.0

    # 4. Trim casing
    log4 = cleaner.apply_action('trim_and_case', column='category', params={'case': 'title'})
    assert cleaner.df['category'].iloc[0] == 'Chuối'

    # Check audit log length
    assert len(cleaner.audit_log) == 4

def test_cleaner_role_detection():
    df = pd.DataFrame({
        'Mã đơn hàng': ['DH-1', 'DH-2'],
        'Ngày đặt hàng': ['2019-10-01', '2019-10-02'],
        'Nhóm sản phẩm': ['Nhóm chuối', 'Nhóm khoai'],
        'Kênh bán hàng': ['Đại lý', 'Shopee'],
        'Doanh thu': [222000000, 264000000],
        'Lợi nhuận HĐKD': [49000000, 61000000]
    })
    cleaner = DataCleaner(df)
    roles = cleaner.detect_column_roles()

    assert roles['revenue_col'] == 'Doanh thu'
    assert roles['category_col'] == 'Nhóm sản phẩm'
    assert roles['date_col'] == 'Ngày đặt hàng'
    assert roles['profit_col'] == 'Lợi nhuận HĐKD'
    assert roles['channel_col'] == 'Kênh bán hàng'
    assert roles['order_col'] == 'Mã đơn hàng'
