import pytest
import os
import pandas as pd
import numpy as np

try:
    from core.cleaner import DataCleaner
    from core.analyzer import DataAnalyzer
    from core.reporter import ReportEngine
except ImportError:
    from cleaner import DataCleaner
    from analyzer import DataAnalyzer
    from reporter import ReportEngine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_MARKETING = os.path.join(BASE_DIR, "data", "doanh_thu_marketing.csv")
CSV_LOGISTICS = os.path.join(BASE_DIR, "data", "ban_le_logistics.csv")

if not os.path.exists(CSV_MARKETING):
    CSV_MARKETING = os.path.join(BASE_DIR, "doanh_thu_marketing.csv")
if not os.path.exists(CSV_LOGISTICS):
    CSV_LOGISTICS = os.path.join(BASE_DIR, "ban_le_logistics.csv")

def test_raw_file_integrity_marketing():
    assert os.path.exists(CSV_MARKETING), "Marketing CSV must exist"
    df_raw = pd.read_csv(CSV_MARKETING)
    assert len(df_raw) == 1366, f"Expected 1,366 rows, got {len(df_raw)}"
    
    # Check revenue column exists
    rev_col = "Doanh thu" if "Doanh thu" in df_raw.columns else None
    assert rev_col is not None, "Doanh thu column must exist"
    raw_sum = df_raw[rev_col].sum()
    raw_mean = df_raw[rev_col].mean()
    assert raw_sum == 20717175575, f"Sum mismatch: {raw_sum}"
    assert abs(raw_mean - 15166307.1559) < 0.01, f"Mean mismatch: {raw_mean}"

def test_independent_financial_kpi_computation():
    """
    Independently recomputes Net Revenue, Profit, Profit Margin from raw file
    and asserts equality with ReportEngine output.
    """
    df_raw = pd.read_csv(CSV_MARKETING)
    
    # 1. Independent calculation
    # Formula: Net revenue = Gross revenue - discounts - returns - taxes
    # In marketing dataset: Gross revenue = Doanh thu, discounts = 0, returns = 0, taxes = 0
    indep_gross = float(df_raw["Doanh thu"].sum())
    indep_net = indep_gross
    
    # Profit = Net revenue - COGS - operating costs
    profit_col = "Lợi nhuận HĐKD" if "Lợi nhuận HĐKD" in df_raw.columns else "Lợi nhuận"
    indep_profit = float(df_raw[profit_col].sum())
    indep_margin = (indep_profit / indep_net) * 100.0 if indep_net > 0 else 0.0
    indep_orders = len(df_raw)
    indep_aov = indep_net / indep_orders if indep_orders > 0 else 0.0

    # 2. App calculation
    cleaner = DataCleaner(df_raw)
    roles = cleaner.detect_column_roles()
    analyzer = DataAnalyzer(cleaner.df, roles)
    metrics = analyzer.compute_financial_metrics()
    
    # Assert exact match
    assert metrics["gross_revenue"] == indep_gross
    assert metrics["net_revenue"] == indep_net
    assert metrics["profit"] == indep_profit
    assert abs(metrics["profit_margin"] - indep_margin) < 1e-6
    assert metrics["total_orders"] == indep_orders
    assert abs(metrics["aov"] - indep_aov) < 1e-4

def test_issues_to_resolve_generation():
    """
    Verifies that AI-generated Issues to Resolve table is backed by real data,
    has priority badges (CAO, TRUNG BÌNH, CƠ HỘI), concrete evidence with numbers,
    and numbered actions (a, b, c).
    """
    df_raw = pd.read_csv(CSV_MARKETING)
    cleaner = DataCleaner(df_raw)
    roles = cleaner.detect_column_roles()
    analyzer = DataAnalyzer(cleaner.df, roles)
    res = analyzer.compute_issues_to_resolve()
    
    issues = res.get("issues", [])
    assert len(issues) > 0, "Should generate at least one issue"
    priorities = {iss["priority"] for iss in issues}
    assert any(p in priorities for p in ["CAO", "TRUNG BÌNH", "CƠ HỘI"])
    
    for iss in issues:
        assert iss["priority"] in ["CAO", "TRUNG BÌNH", "CƠ HỘI"]
        headline = iss.get("headline") or iss.get("issue")
        assert len(headline.split()) >= 4, "Issue headline should be descriptive"
        assert len(iss["evidence"]) > 10, "Evidence must be concrete"
        assert "actions" in iss and len(iss["actions"]) >= 2, "Must have numbered actions"
        trace = iss.get("trace_data") or iss.get("underlying_data")
        assert trace is not None and isinstance(trace, dict)

def test_column_mapping_taxonomy():
    """
    Verifies column mapping details returns roles, confidence, sample values, and formula role.
    """
    df_raw = pd.read_csv(CSV_MARKETING)
    cleaner = DataCleaner(df_raw)
    roles = cleaner.detect_column_roles()
    mapping = cleaner.get_column_mapping_details(roles)
    
    assert len(mapping) >= 10, "Taxonomy must cover all required financial roles"
    role_keys = {m["role_key"] for m in mapping}
    assert "gross_revenue_col" in role_keys
    assert "net_revenue_col" in role_keys
    assert "profit_col" in role_keys
    assert "category_col" in role_keys
    assert "date_col" in role_keys

def test_logistics_sample_integrity():
    """
    Verifies the second sample dataset (ban_le_logistics.csv) loads and computes cleanly.
    """
    assert os.path.exists(CSV_LOGISTICS), "Logistics CSV must exist"
    df_raw = pd.read_csv(CSV_LOGISTICS)
    assert len(df_raw) == 1502, f"Expected 1,502 rows, got {len(df_raw)}"
    
    cleaner = DataCleaner(df_raw)
    roles = cleaner.detect_column_roles()
    analyzer = DataAnalyzer(cleaner.df, roles)
    metrics = analyzer.compute_financial_metrics()
    assert metrics["net_revenue"] > 0
    assert metrics["row_count"] == 1502
