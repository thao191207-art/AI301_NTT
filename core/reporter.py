import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

def format_vnd(val: float, is_currency: bool = True) -> str:
    """Format number in Vietnamese convention (dot for thousands, comma for decimals)."""
    if pd.isna(val) or val is None:
        return "N/A"
    val = round(val, 2)
    if val.is_integer():
        formatted = f"{int(val):,}".replace(',', '.')
    else:
        parts = f"{val:,.2f}".split('.')
        formatted = parts[0].replace(',', '.') + ',' + parts[1]
    return f"{formatted} VND" if is_currency else formatted

class ReportEngine:
    def __init__(self, df: pd.DataFrame, roles: Dict[str, str], business_context: Optional[Dict[str, Any]] = None):
        self.df = df.copy()
        self.roles = roles or {}
        self.business_context = business_context or {}
        
        # Import cleaner helpers
        try:
            from core.analyzer import clean_numeric_series, vi_format_num, DataAnalyzer
        except ImportError:
            from analyzer import clean_numeric_series, vi_format_num, DataAnalyzer
            
        self.DataAnalyzer = DataAnalyzer
        
        # Ensure numeric columns are properly converted
        numeric_roles = [
            'gross_revenue_col', 'net_revenue_col', 'revenue_col',
            'discount_col', 'return_col', 'tax_col',
            'cogs_col', 'operating_cost_col', 'cost_col',
            'profit_col', 'quantity_col', 'delivery_days_col'
        ]
        for role_key in numeric_roles:
            col_name = self.roles.get(role_key)
            if col_name and col_name in self.df.columns:
                self.df[col_name] = clean_numeric_series(self.df[col_name])
                
        self._prepare_data()

    def _prepare_data(self):
        """Prepare date columns, YearMonth, MonthLabel."""
        df = self.df
        date_col = self.roles.get('date_col')
        if date_col and date_col in df.columns:
            df['__parsed_date'] = pd.to_datetime(df[date_col], errors='coerce')
            df['__year'] = df['__parsed_date'].dt.year
            df['__month'] = df['__parsed_date'].dt.month
            df['__ym'] = df['__parsed_date'].dt.strftime('%Y-%m')
            df['__month_label'] = df['__parsed_date'].apply(
                lambda d: f"T{d.month:02d}-{d.year}" if pd.notna(d) else "N/A"
            )
            df['__short_label'] = df['__parsed_date'].apply(
                lambda d: f"T{d.month:02d}" if pd.notna(d) else "N/A"
            )
        else:
            df['__ym'] = '2019-10'
            df['__year'] = 2019
            df['__month'] = 10
            df['__month_label'] = 'T10-2019'
            df['__short_label'] = 'T10'

    def get_filter_options(self) -> Dict[str, Any]:
        """Get available months and product groups for dropdown selectors."""
        df = self.df
        if '__ym' in df.columns:
            valid_yms = df.dropna(subset=['__ym'])['__ym'].unique()
            ym_list = sorted(list(valid_yms))
            month_options = []
            for ym in ym_list:
                rows = df[df['__ym'] == ym]
                label = rows['__month_label'].iloc[0]
                short = rows['__short_label'].iloc[0]
                year = int(rows['__year'].iloc[0])
                month_options.append({
                    'ym': ym,
                    'short_label': short,
                    'full_label': label,
                    'year': year
                })
        else:
            month_options = [{'ym': '2019-10', 'short_label': 'T10', 'full_label': 'T10-2019', 'year': 2019}]

        cat_col = self.roles.get('category_col')
        if cat_col and cat_col in df.columns:
            groups = sorted([str(x) for x in df[cat_col].dropna().unique()])
        else:
            groups = ['Mặc định']

        return {
            'months': month_options,
            'default_month': month_options[-1]['ym'] if month_options else '',
            'groups': groups,
            'default_group': groups[0] if groups else ''
        }

    def compute_summary_strip(self) -> Dict[str, Any]:
        """Compute the expanded horizontal summary strip with new financial metrics & formulas."""
        analyzer = self.DataAnalyzer(self.df, self.roles, self.business_context)
        fin = analyzer.compute_financial_metrics()
        
        cat_col = self.roles.get('category_col')
        rev_col = self.roles.get('net_revenue_col') or self.roles.get('revenue_col')
        top_cat = ""
        if cat_col and cat_col in self.df.columns and rev_col and rev_col in self.df.columns:
            top_series = self.df.groupby(cat_col)[rev_col].sum()
            if not top_series.empty:
                top_cat = str(top_series.idxmax())

        s_rev = self.df[rev_col].dropna() if rev_col and rev_col in self.df.columns else pd.Series([0])
        
        cards = [
            {
                'id': 'net_revenue',
                'label': 'DOANH THU THUẦN',
                'value_formatted': fin['net_revenue_formatted'],
                'formula': fin['net_revenue_formula'],
                'is_na': False,
                'na_reason': None
            },
            {
                'id': 'profit',
                'label': 'LỢI NHUẬN HĐKD',
                'value_formatted': fin['profit_formatted'],
                'formula': fin['profit_formula'],
                'is_na': False,
                'na_reason': None
            },
            {
                'id': 'profit_margin',
                'label': 'BIÊN LỢI NHUẬN (ROS)',
                'value_formatted': fin['profit_margin_formatted'],
                'formula': fin['profit_margin_formula'],
                'is_na': fin['net_revenue'] <= 0,
                'na_reason': 'Doanh thu thuần = 0' if fin['net_revenue'] <= 0 else None
            },
        ]
        if fin['gross_revenue_available']:
            cards.append({
                'id': 'gross_revenue',
                'label': 'DOANH THU GỘP',
                'value_formatted': fin['gross_revenue_formatted'],
                'formula': 'Tổng giá trị hóa đơn trước giảm trừ',
                'is_na': False
            })
        cards.append({
            'id': 'total_orders',
            'label': 'TỔNG ĐƠN HÀNG',
            'value_formatted': fin['total_orders_formatted'],
            'formula': 'Số lượng mã đơn duy nhất (hoặc số dòng dữ liệu)',
            'is_na': False
        })
        if fin['has_quantity']:
            cards.append({
                'id': 'total_quantity',
                'label': 'TỔNG SẢN LƯỢNG',
                'value_formatted': fin['total_quantity_formatted'],
                'formula': 'Tổng số lượng sản phẩm bán ra',
                'is_na': False
            })
        if fin['has_cogs']:
            cards.append({
                'id': 'total_cogs',
                'label': 'GIÁ VỐN (COGS)',
                'value_formatted': fin['total_cogs_formatted'],
                'formula': 'Tổng chi phí vốn hàng bán',
                'is_na': False
            })
        cards.append({
            'id': 'aov',
            'label': 'GIÁ TRỊ ĐƠN TB (AOV)',
            'value_formatted': fin['aov_formatted'],
            'formula': 'Doanh thu thuần ÷ Tổng số đơn hàng',
            'is_na': False
        })
        cards.append({
            'id': 'row_count',
            'label': 'SỐ DÒNG DỮ LIỆU',
            'value_formatted': fin['row_count_formatted'],
            'formula': 'Tổng số bản ghi trong tệp đã làm sạch',
            'is_na': False
        })

        return {
            'cards': cards,
            'total_revenue': fin['net_revenue'],
            'total_formatted': fin['net_revenue_formatted'],
            'net_revenue': fin['net_revenue'],
            'net_revenue_formatted': fin['net_revenue_formatted'],
            'profit': fin['profit'],
            'profit_formatted': fin['profit_formatted'],
            'profit_margin': fin['profit_margin'],
            'profit_margin_formatted': fin['profit_margin_formatted'],
            'gross_revenue': fin['gross_revenue'],
            'gross_revenue_formatted': fin['gross_revenue_formatted'],
            'gross_revenue_available': fin['gross_revenue_available'],
            'total_orders': fin['total_orders'],
            'total_orders_formatted': fin['total_orders_formatted'],
            'total_quantity': fin['total_quantity'],
            'total_quantity_formatted': fin['total_quantity_formatted'],
            'has_quantity': fin['has_quantity'],
            'total_cogs': fin['total_cogs'],
            'total_cogs_formatted': fin['total_cogs_formatted'],
            'has_cogs': fin['has_cogs'],
            'aov': fin['aov'],
            'aov_formatted': fin['aov_formatted'],
            'row_count': fin['row_count'],
            'row_count_formatted': fin['row_count_formatted'],
            'average_revenue': float(s_rev.mean()),
            'average_formatted': format_vnd(float(s_rev.mean())),
            'median_revenue': float(s_rev.median()),
            'median_formatted': format_vnd(float(s_rev.median())),
            'min_revenue': float(s_rev.min()),
            'min_formatted': format_vnd(float(s_rev.min())),
            'max_revenue': float(s_rev.max()),
            'max_formatted': format_vnd(float(s_rev.max())),
            'top_category': top_cat,
            'formulas': {
                'net_revenue': fin['net_revenue_formula'],
                'profit': fin['profit_formula'],
                'profit_margin': fin['profit_margin_formula']
            },
            'profit_mismatch_note': fin['profit_mismatch_note'],
            'skipped_cards': fin['skipped_cards']
        }

    def compute_dashboard(self, selected_ym: Optional[str] = None, selected_group: Optional[str] = None) -> Dict[str, Any]:
        """Compute all KPIs, charts, and analysis paragraphs for the executive dashboard layout."""
        df = self.df
        options = self.get_filter_options()
        
        if not selected_ym or not any(m['ym'] == selected_ym for m in options['months']):
            selected_ym = options['default_month']
            
        selected_month_meta = next((m for m in options['months'] if m['ym'] == selected_ym), options['months'][-1])
        selected_year = selected_month_meta['year']
        selected_short = selected_month_meta['short_label']
        
        if not selected_group or selected_group not in options['groups']:
            selected_group = options['default_group']
            
        rev_col = self.roles.get('net_revenue_col') or self.roles.get('revenue_col', '')
        prof_col = self.roles.get('profit_col', '')
        order_col = self.roles.get('order_col', '')
        cat_col = self.roles.get('category_col', '')

        # 1. Total Company KPIs (whole period vs selected month)
        total_revenue_all = float(df[rev_col].sum()) if rev_col in df.columns else 0.0
        total_profit_all = float(df[prof_col].sum()) if prof_col in df.columns else 0.0
        overall_margin = round((total_profit_all / total_revenue_all * 100), 1) if total_revenue_all > 0 else 0.0
        total_orders_all = len(df[order_col].unique()) if order_col in df.columns else len(df)
        
        # Filter for selected month
        df_month = df[df['__ym'] == selected_ym]
        month_revenue = float(df_month[rev_col].sum()) if rev_col in df_month.columns else 0.0
        month_profit = float(df_month[prof_col].sum()) if prof_col in df_month.columns else 0.0
        month_orders = len(df_month[order_col].unique()) if order_col in df_month.columns else len(df_month)
        
        # Company Profit Margin for selected month
        company_ros = round((month_profit / month_revenue * 100), 0) if month_revenue > 0 else 0.0
        
        # MoM Revenue Growth
        all_yms = [m['ym'] for m in options['months']]
        curr_idx = all_yms.index(selected_ym) if selected_ym in all_yms else -1
        prev_rev = 0.0
        mom_growth = 0.0
        if curr_idx > 0:
            prev_ym = all_yms[curr_idx - 1]
            df_prev = df[df['__ym'] == prev_ym]
            prev_rev = float(df_prev[rev_col].sum()) if rev_col in df_prev.columns else 0.0
            if prev_rev > 0:
                mom_growth = round(((month_revenue - prev_rev) / prev_rev) * 100, 1)

        # 2. Row 1 Charts:
        palette = ['#2563EB', '#16A34A', '#EAB308', '#EA580C', '#D946EF', '#06B6D4', '#8B5CF6']
        
        chart1_data = []
        chart2_data = []
        margin_by_group = []
        
        if cat_col in df_month.columns and rev_col in df_month.columns:
            grp_month = df_month.groupby(cat_col).agg({
                rev_col: 'sum',
                prof_col: 'sum' if prof_col in df_month.columns else lambda x: 0
            }).reset_index().sort_values(by=cat_col)
            
            for idx, row in grp_month.iterrows():
                c_name = str(row[cat_col])
                r_val = float(row[rev_col])
                p_val = float(row[prof_col]) if prof_col in df_month.columns else 0.0
                color = palette[idx % len(palette)]
                m_pct = round((p_val / r_val * 100), 1) if r_val > 0 else 0.0
                
                chart1_data.append({
                    'category': c_name,
                    'revenue': r_val,
                    'millions': round(r_val / 1e6, 0),
                    'color': color
                })
                chart2_data.append({
                    'category': c_name,
                    'profit': p_val,
                    'millions': round(p_val / 1e6, 0),
                    'color': color
                })
                margin_by_group.append({
                    'category': c_name,
                    'margin_pct': m_pct,
                    'color': color
                })
                
        # Sort margin descending
        margin_by_group.sort(key=lambda x: x['margin_pct'], reverse=True)

        # 3. Row 2 Charts (for selected group across 12 months)
        df_group = df[df[cat_col] == selected_group] if cat_col in df.columns else df
        
        monthly_grp = df_group.groupby('__ym').agg({
            rev_col: 'sum',
            prof_col: 'sum' if prof_col in df_group.columns else lambda x: 0,
            '__month_label': 'first'
        }).reset_index().sort_values(by='__ym')
        
        chart4_labels = []
        chart4_values = []
        chart4_raw_values = []
        chart5_indices = []
        
        base_rev = float(monthly_grp[rev_col].iloc[0]) if not monthly_grp.empty else 1.0
        if base_rev <= 0: base_rev = 1.0
            
        for _, row in monthly_grp.iterrows():
            m_label = str(row['__month_label'])
            r_val = float(row[rev_col])
            chart4_labels.append(m_label)
            chart4_raw_values.append(r_val)
            chart4_values.append(round(r_val / 1e6, 0))
            idx_pct = round((r_val / base_rev) * 100, 0)
            chart5_indices.append(int(idx_pct))

        # ROS for selected group in selected month
        df_group_month = df_group[df_group['__ym'] == selected_ym]
        grp_m_rev = float(df_group_month[rev_col].sum()) if rev_col in df_group_month.columns else 0.0
        grp_m_prof = float(df_group_month[prof_col].sum()) if prof_col in df_group_month.columns else 0.0
        group_ros = round((grp_m_prof / grp_m_rev * 100), 0) if grp_m_rev > 0 else 0.0

        # 4. Generate written analysis text under each chart
        if chart1_data:
            c1_max = max(chart1_data, key=lambda x: x['revenue'])
            c1_min = min(chart1_data, key=lambda x: x['revenue'])
            gap1_m = int(round((c1_max['revenue'] - c1_min['revenue']) / 1e6, 0))
            m_rev_formatted = f"{int(round(month_revenue)):,}".replace(',', '.')
            c1_max_formatted = f"{int(c1_max['millions']):,}".replace(',', '.')
            c1_text = (
                f"Trong tháng {selected_short}-{selected_year}, tổng doanh thu thuần toàn bộ 5 nhóm hàng đạt {m_rev_formatted} VND. "
                f"Dẫn đầu là '{c1_max['category']}' với mức doanh thu đạt {c1_max_formatted}.000.000 VND (tương đương {int(c1_max['millions'])} Millions). "
                f"Nhóm có doanh thu thấp nhất là '{c1_min['category']}' đạt {int(c1_min['millions'])} Millions, "
                f"tạo ra khoảng cách chênh lệch {gap1_m} Millions giữa nhóm cao nhất và thấp nhất."
            )
        else:
            c1_text = f"Không đủ dữ liệu nhóm hàng trong tháng {selected_short}."

        if chart2_data:
            c2_max = max(chart2_data, key=lambda x: x['profit'])
            c2_min = min(chart2_data, key=lambda x: x['profit'])
            gap2_m = int(round((c2_max['profit'] - c2_min['profit']) / 1e6, 0))
            m_prof_formatted = f"{int(round(month_profit)):,}".replace(',', '.')
            c2_text = (
                f"Tổng lợi nhuận kinh doanh trong tháng {selected_short} ghi nhận đạt {m_prof_formatted} VND. "
                f"Trong đó, '{c2_max['category']}' mang lại mức lợi nhuận cao nhất đạt {int(c2_max['millions'])} Millions, "
                f"trong khi '{c2_min['category']}' đóng góp {int(c2_min['millions'])} Millions (chênh lệch {gap2_m} Millions). "
                f"Tất cả các nhóm sản phẩm đều duy trì lợi nhuận dương ổn định."
            )
        else:
            c2_text = f"Không đủ dữ liệu lợi nhuận trong tháng {selected_short}."

        ros_text = (
            f"Tỷ suất biên lợi nhuận (ROS) toàn công ty trong tháng {selected_short}-{selected_year} đạt {int(company_ros)}%. "
            f"Chỉ số này phản ánh hiệu quả vận hành khi doanh nghiệp giữ lại được {int(company_ros)} đồng lợi nhuận trên mỗi 100 đồng doanh thu thuần tạo ra."
        )

        if chart4_values:
            max_c4 = max(chart4_values)
            min_c4 = min(chart4_values)
            max_m_label = chart4_labels[chart4_values.index(max_c4)]
            min_m_label = chart4_labels[chart4_values.index(min_c4)]
            gap_c4 = int(max_c4 - min_c4)
            c4_text = (
                f"Doanh thu thuần của '{selected_group}' qua chu kỳ 12 tháng dao động từ mức thấp nhất {int(min_c4)} Millions ({min_m_label}) "
                f"đến đỉnh điểm {int(max_c4)} Millions ({max_m_label}), chênh lệch {gap_c4} Millions. "
                f"Ở tháng {selected_short}-{selected_year}, doanh thu thuần của nhóm đạt {int(chart4_values[-1])} Millions."
            )
        else:
            c4_text = f"Không có dữ liệu 12 tháng cho nhóm '{selected_group}'."

        if chart5_indices:
            peak_idx = max(chart5_indices)
            peak_m = chart4_labels[chart5_indices.index(peak_idx)]
            low_idx = min(chart5_indices)
            low_m = chart4_labels[chart5_indices.index(low_idx)]
            current_idx = chart5_indices[-1]
            c5_text = (
                f"Chỉ số tăng trưởng doanh thu của '{selected_group}' lấy mốc tháng đầu tiên {chart4_labels[0]} làm gốc quy ước 100%. "
                f"Chỉ số đạt mức cao kỷ lục {peak_idx}% vào {peak_m}, chạm đáy {low_idx}% vào {low_m}, "
                f"và tại tháng kết thúc chu kỳ đạt {current_idx}%."
            )
        else:
            c5_text = f"Không đủ dữ liệu tính chu kỳ tăng trưởng cho '{selected_group}'."

        c6_text = (
            f"Tỷ suất biên lợi nhuận riêng của '{selected_group}' trong tháng {selected_short}-{selected_year} đạt mức {int(group_ros)}%. "
            f"Tỷ suất này tương đồng với hiệu suất chung toàn doanh nghiệp ({int(company_ros)}%), khẳng định tính ổn định về biên lợi nhuận của danh mục."
        )

        # 5. Compute AI Issues To Resolve (Section 4 Block I)
        analyzer = self.DataAnalyzer(self.df, self.roles, self.business_context)
        issues_data = analyzer.compute_issues_to_resolve(selected_month=selected_ym)

        # 6. Top Findings
        top_findings = [
            {
                'finding': 'Doanh thu thuần tháng báo cáo',
                'metric': 'Doanh thu thuần',
                'value': format_vnd(month_revenue),
                'comparison': f"Tăng trưởng {mom_growth:+0.1f}% so với tháng trước" if curr_idx > 0 else "Kỳ đầu tiên",
                'action': 'Tối ưu danh mục để duy trì đà tăng trưởng và mở rộng nhóm biên lợi nhuận cao.'
            },
            {
                'finding': 'Biên lợi nhuận trên doanh thu (ROS)',
                'metric': 'ROS Toàn công ty',
                'value': f"{int(company_ros)}%",
                'comparison': f"Nhóm {selected_group} đạt {int(group_ros)}%",
                'action': 'Giữ vững cấu trúc giá bán và kiểm soát chi phí vận hành ở ngưỡng an toàn.'
            },
            {
                'finding': 'Nhóm hàng chủ lực về doanh thu',
                'metric': c1_max['category'] if chart1_data else 'N/A',
                'value': f"{int(c1_max['millions'])} Millions" if chart1_data else '0',
                'comparison': f"Vượt nhóm thấp nhất {gap1_m} Millions" if chart1_data else 'N/A',
                'action': 'Tập trung nguồn lực tiếp thị và lưu kho ưu tiên cho các nhóm sản phẩm dẫn đầu.'
            },
            {
                'finding': 'Hiệu suất nhóm hàng được chọn',
                'metric': selected_group,
                'value': f"{int(chart4_values[-1])} Millions" if chart4_values else '0',
                'comparison': f"Chỉ số gốc đạt {current_idx}%" if chart5_indices else 'N/A',
                'action': 'Theo dõi biến động nhu cầu định kỳ để chủ động kế hoạch tồn kho.'
            }
        ]

        return {
            'selected_month': selected_ym,
            'selected_year': selected_year,
            'selected_short': selected_short,
            'selected_group': selected_group,
            'kpis': {
                'total_revenue': total_revenue_all,
                'total_revenue_formatted': format_vnd(total_revenue_all, is_currency=False),
                'total_profit': total_profit_all,
                'total_profit_formatted': format_vnd(total_profit_all, is_currency=False),
                'overall_margin': overall_margin,
                'overall_margin_formatted': f"{overall_margin:.1f}%",
                'month_revenue': month_revenue,
                'month_revenue_formatted': format_vnd(month_revenue, is_currency=False),
                'total_orders': total_orders_all,
                'total_orders_formatted': f"{total_orders_all:,}".replace(',', '.'),
                'month_orders': month_orders,
                'month_orders_formatted': f"{month_orders:,}".replace(',', '.'),
                'mom_growth': mom_growth,
                'mom_growth_formatted': f"{mom_growth:+0.0f}%" if mom_growth != 0 else "0%",
                'company_ros': company_ros,
                'company_ros_formatted': f"{int(company_ros)}%",
                'group_ros': group_ros,
                'group_ros_formatted': f"{int(group_ros)}%"
            },
            'charts': {
                'chart1_revenue_by_group': {
                    'title': 'DOANH THU THUẦN THEO NHÓM SP',
                    'unit': 'Millions',
                    'type': 'column',
                    'data': chart1_data,
                    'analysis': c1_text
                },
                'chart2_profit_by_group': {
                    'title': 'LỢI NHUẬN HĐKD THEO NHÓM SP',
                    'unit': 'Millions',
                    'type': 'column',
                    'data': chart2_data,
                    'analysis': c2_text
                },
                'chart3_company_ros': {
                    'title': 'BIÊN LỢI NHUẬN (ROS) TOÀN CÔNG TY',
                    'unit': '%',
                    'type': 'doughnut',
                    'value': int(company_ros),
                    'analysis': ros_text
                },
                'chart4_group_monthly_revenue': {
                    'title': 'DOANH THU THUẦN CỦA NHÓM HÀNG',
                    'unit': 'Millions',
                    'type': 'column',
                    'labels': chart4_labels,
                    'values': chart4_values,
                    'raw_values': chart4_raw_values,
                    'analysis': c4_text
                },
                'chart5_group_growth_index': {
                    'title': 'TĂNG TRƯỞNG DOANH THU TỪNG NHÓM HÀNG',
                    'unit': '%',
                    'type': 'line',
                    'labels': chart4_labels,
                    'values': chart5_indices,
                    'footnote': 'Quy ước kỳ gốc: Tháng đầu tiên (T11-2018) = 100%, các tháng tiếp theo biểu thị tỷ lệ tương đối so với kỳ gốc.',
                    'analysis': c5_text
                },
                'chart6_group_ros': {
                    'title': 'BIÊN LỢI NHUẬN CỦA NHÓM HÀNG',
                    'unit': '%',
                    'type': 'doughnut',
                    'value': int(group_ros),
                    'analysis': c6_text
                },
                'margin_by_group': margin_by_group
            },
            'issues_to_resolve': issues_data,
            'top_findings': top_findings
        }
