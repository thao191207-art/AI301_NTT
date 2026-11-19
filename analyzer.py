import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

def vi_format_num(val: float) -> str:
    """Format integer/float with dot as thousands separator for Vietnamese convention."""
    if pd.isna(val) or val is None:
        return "N/A"
    return f"{int(round(val)):,}".replace(',', '.')

def clean_numeric_series(series: pd.Series) -> pd.Series:
    """Safely convert series to numeric without corrupting decimals."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce')
        
    def parse_num(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip()
        if not s or s.lower() in ['nan', 'null', 'none', 'n/a']:
            return np.nan
        s = re.sub(r'[\sđ₫$€£]', '', s)
        is_pct = '%' in s
        s = s.replace('%', '')
        if re.match(r'^-?\d{1,3}(\.\d{3})+(,\d+)?$', s):
            s = s.replace('.', '').replace(',', '.')
        elif re.match(r'^-?\d{1,3}(,\d{3})+(\.\d+)?$', s):
            s = s.replace(',', '')
        try:
            val = float(s)
            return val / 100.0 if is_pct else val
        except ValueError:
            return np.nan
            
    return series.apply(parse_num)

class DataAnalyzer:
    def __init__(self, df: pd.DataFrame, roles: Dict[str, str], business_context: Optional[Dict[str, Any]] = None):
        self.df = df.copy()
        self.roles = roles or {}
        self.business_context = business_context or {}
        
        # Ensure all numeric candidate columns are converted
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

    def compute_financial_metrics(self) -> Dict[str, Any]:
        """
        Compute financial metrics strictly according to specification:
        - Net Revenue = Gross revenue − discounts − returns − taxes (state components used)
        - Profit = Net revenue − COGS − operating costs (compare with profit column if present)
        - Profit Margin = Profit ÷ Net revenue × 100%
        - Derived metrics: Gross rev, Orders, Quantity, COGS, AOV, Rows
        - Skipped cards list
        """
        df = self.df
        roles = self.roles
        
        gross_col = roles.get('gross_revenue_col') or roles.get('revenue_col')
        net_col = roles.get('net_revenue_col')
        disc_col = roles.get('discount_col')
        ret_col = roles.get('return_col')
        tax_col = roles.get('tax_col')
        cogs_col = roles.get('cogs_col')
        cost_col = roles.get('operating_cost_col') or roles.get('cost_col')
        profit_col = roles.get('profit_col')
        order_col = roles.get('order_col')
        qty_col = roles.get('quantity_col')
        
        # 1. Gross Revenue
        has_gross = bool(gross_col and gross_col in df.columns)
        gross_series = df[gross_col].fillna(0) if has_gross else pd.Series(0, index=df.index)
        total_gross = float(gross_series.sum()) if has_gross else 0.0

        # 2. Net Revenue components
        components_used = []
        if net_col and net_col in df.columns and net_col != gross_col:
            net_series = df[net_col].fillna(0)
            net_formula = f"Doanh thu thuần lấy trực tiếp từ cột '{net_col}'"
        else:
            net_series = gross_series.copy()
            if disc_col and disc_col in df.columns:
                net_series = net_series - df[disc_col].fillna(0)
                components_used.append(f"Chiết khấu ('{disc_col}')")
            if ret_col and ret_col in df.columns:
                net_series = net_series - df[ret_col].fillna(0)
                components_used.append(f"Hàng trả lại ('{ret_col}')")
            if tax_col and tax_col in df.columns:
                net_series = net_series - df[tax_col].fillna(0)
                components_used.append(f"Thuế ('{tax_col}')")
                
            if components_used:
                net_formula = f"Doanh thu thuần = Doanh thu gộp − {' − '.join(components_used)}"
            else:
                net_formula = "Doanh thu thuần = Doanh thu gộp (không có chiết khấu/trả hàng/thuế)"
                
        total_net = float(net_series.sum())
        
        # 3. Cost and Profit
        has_cogs = bool(cogs_col and cogs_col in df.columns)
        cogs_series = df[cogs_col].fillna(0) if has_cogs else pd.Series(0, index=df.index)
        total_cogs = float(cogs_series.sum()) if has_cogs else 0.0
        
        has_opex = bool(cost_col and cost_col in df.columns and cost_col != cogs_col)
        opex_series = df[cost_col].fillna(0) if has_opex else pd.Series(0, index=df.index)
        total_opex = float(opex_series.sum()) if has_opex else 0.0
        
        mismatch_note = ""
        has_profit_col = bool(profit_col and profit_col in df.columns)
        if has_profit_col:
            profit_series = df[profit_col].fillna(0)
            total_profit = float(profit_series.sum())
            profit_formula = f"Lợi nhuận ghi nhận từ cột '{profit_col}'"
            
            # Check against Net - COGS - Opex
            if has_cogs or has_opex:
                calc_profit = total_net - total_cogs - total_opex
                diff = abs(total_profit - calc_profit)
                if diff > 1000 and total_profit > 0 and (diff / total_profit) > 0.01:
                    mismatch_note = f"Chênh lệch số liệu: Lợi nhuận cột ({total_profit:,.0f} VND) khác công thức tính ({calc_profit:,.0f} VND) một khoảng {diff:,.0f} VND."
        else:
            profit_series = net_series - cogs_series - opex_series
            total_profit = float(profit_series.sum())
            cost_parts = []
            if has_cogs: cost_parts.append(f"Giá vốn ('{cogs_col}')")
            if has_opex: cost_parts.append(f"Chi phí vận hành ('{cost_col}')")
            profit_formula = f"Lợi nhuận = Doanh thu thuần − {' − '.join(cost_parts) if cost_parts else '0'}"
            
        # 4. Profit Margin (Biên lợi nhuận)
        if total_net > 0:
            profit_margin_val = (total_profit / total_net) * 100.0
            profit_margin_formatted = f"{profit_margin_val:.1f}%".replace('.', ',')
            margin_formula = f"Biên lợi nhuận = ({total_profit:,.0f} ÷ {total_net:,.0f}) × 100%".replace(',', '.')
        else:
            profit_margin_val = None
            profit_margin_formatted = "N/A (Doanh thu thuần = 0)"
            margin_formula = "Không thể chia cho 0 do Doanh thu thuần bằng 0."
            
        # 5. Additional totals
        total_orders = len(df[order_col].dropna().unique()) if order_col and order_col in df.columns else len(df)
        has_qty = bool(qty_col and qty_col in df.columns)
        total_quantity = float(df[qty_col].dropna().sum()) if has_qty else 0.0
        
        aov_val = (total_net / total_orders) if total_orders > 0 else 0.0
        
        # 6. Skipped cards list
        skipped_cards = []
        if not disc_col or disc_col not in df.columns:
            skipped_cards.append("Tổng chiết khấu (không có cột chiết khấu)")
        if not ret_col or ret_col not in df.columns:
            skipped_cards.append("Tổng hàng trả lại (không có cột hoàn tiền/trả hàng)")
        if not tax_col or tax_col not in df.columns:
            skipped_cards.append("Tổng thuế (không có cột thuế)")
        if not has_qty:
            skipped_cards.append("Tổng số lượng bán (không có cột số lượng)")
        if not has_cogs:
            skipped_cards.append("Tổng giá vốn (không có cột giá vốn COGS)")

        return {
            'net_revenue': total_net,
            'net_revenue_formatted': vi_format_num(total_net) + " VND",
            'net_revenue_formula': net_formula,
            'profit': total_profit,
            'profit_formatted': vi_format_num(total_profit) + " VND",
            'profit_formula': profit_formula,
            'profit_mismatch_note': mismatch_note,
            'profit_margin': profit_margin_val,
            'profit_margin_formatted': profit_margin_formatted,
            'profit_margin_formula': margin_formula,
            'gross_revenue': total_gross,
            'gross_revenue_formatted': vi_format_num(total_gross) + " VND",
            'gross_revenue_available': has_gross,
            'total_orders': total_orders,
            'total_orders_formatted': f"{total_orders:,}".replace(',', '.'),
            'total_quantity': total_quantity,
            'total_quantity_formatted': f"{int(total_quantity):,}".replace(',', '.') if has_qty else "N/A",
            'has_quantity': has_qty,
            'total_cogs': total_cogs,
            'total_cogs_formatted': vi_format_num(total_cogs) + " VND" if has_cogs else "N/A",
            'has_cogs': has_cogs,
            'aov': aov_val,
            'aov_formatted': vi_format_num(aov_val) + " VND",
            'row_count': len(df),
            'row_count_formatted': f"{len(df):,}".replace(',', '.'),
            'skipped_cards': skipped_cards,
            'components_used': components_used
        }

    def generate_ai_core_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate 3-5 core business questions based strictly on the uploaded file profile
        referencing real columns, product groups, dates, and channels.
        """
        df = self.df
        roles = self.roles
        cat_col = roles.get('category_col')
        chan_col = roles.get('channel_col')
        date_col = roles.get('date_col')
        rev_col = roles.get('net_revenue_col') or roles.get('revenue_col')
        profit_col = roles.get('profit_col')
        
        categories = df[cat_col].dropna().unique().tolist()[:5] if cat_col and cat_col in df.columns else []
        channels = df[chan_col].dropna().unique().tolist()[:4] if chan_col and chan_col in df.columns else []
        
        suggestions = []
        
        # 1. Product Category Question
        if categories:
            cat_list_str = ", ".join([str(c) for c in categories[:3]])
            suggestions.append({
                'id': 'sugg_1',
                'question': f"Doanh thu thuần và biên lợi nhuận giữa các nhóm sản phẩm ({cat_list_str}) chênh lệch ra sao?",
                'category': 'Cơ cấu sản phẩm',
                'context': f"Dựa trên {len(categories)} nhóm hàng trong cột '{cat_col}'"
            })
            
        # 2. Profit Margin Question
        if profit_col:
            suggestions.append({
                'id': 'sugg_2',
                'question': f"Tỷ suất biên lợi nhuận bình quân toàn doanh nghiệp đạt bao nhiêu và nhóm nào có tỷ suất sinh lời vượt trội?",
                'category': 'Hiệu quả lợi nhuận',
                'context': f"Dựa trên chỉ số lợi nhuận từ cột '{profit_col}'"
            })
            
        # 3. Channel Distribution Question
        if channels:
            chan_str = ", ".join([str(c) for c in channels[:3]])
            suggestions.append({
                'id': 'sugg_3',
                'question': f"Kênh bán hàng nào ({chan_str}) mang lại giá trị đơn hàng trung bình (AOV) và doanh thu thuần cao nhất?",
                'category': 'Kênh phân phối',
                'context': f"Dựa trên {len(channels)} kênh trong cột '{chan_col}'"
            })
            
        # 4. Time Trend Question
        if date_col and date_col in df.columns:
            suggestions.append({
                'id': 'sugg_4',
                'question': f"Xu hướng tăng trưởng doanh thu qua các tháng biến động như thế nào, tháng nào đạt đỉnh và tháng nào suy giảm?",
                'category': 'Xu hướng chu kỳ',
                'context': f"Dựa trên dữ liệu thời gian trong cột '{date_col}'"
            })
            
        # 5. Cost & Inventory/Quality Question
        cogs_col = roles.get('cogs_col') or roles.get('cost_col')
        if cogs_col and cogs_col in df.columns:
            suggestions.append({
                'id': 'sugg_5',
                'question': f"Chi phí giá vốn và vận hành đang chiếm tỷ trọng bao nhiêu phần trăm trong tổng doanh thu thuần?",
                'category': 'Cấu trúc chi phí',
                'context': f"Dựa trên số liệu cột chi phí '{cogs_col}'"
            })
            
        return suggestions[:5]

    def compute_issues_to_resolve(self, selected_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute candidate list of prioritized business issues from the raw data:
        1. Trend breaks (sharpest MoM revenue drop)
        2. Concentration of decline (which product group plunged)
        3. Profit margin disparity between groups
        4. Canceled orders or returns (if status/return exists)
        5. Growth opportunities (high margin, low revenue share)
        
        Priority: CAO (red), TRUNG BÌNH (orange), CƠ HỘI (green)
        """
        df = self.df
        roles = self.roles
        issues = []
        skipped_checks = []
        
        date_col = roles.get('date_col')
        rev_col = roles.get('net_revenue_col') or roles.get('revenue_col')
        profit_col = roles.get('profit_col')
        cat_col = roles.get('category_col')
        status_col = roles.get('status_col')
        
        # Prepare date
        if date_col and date_col in df.columns and rev_col and rev_col in df.columns:
            df_t = df.copy()
            df_t['__dt'] = pd.to_datetime(df_t[date_col], errors='coerce')
            df_t['__ym'] = df_t['__dt'].dt.strftime('%Y-%m')
            
            # --- Check 1: Trend Break (Monthly revenue drop) ---
            monthly = df_t.groupby('__ym')[rev_col].sum().sort_index()
            if len(monthly) >= 2:
                mom_growth = monthly.pct_change() * 100
                worst_m = mom_growth.idxmin()
                worst_pct = float(mom_growth.loc[worst_m])
                worst_rev = float(monthly.loc[worst_m])
                prev_m_idx = list(monthly.index).index(worst_m) - 1
                prev_m = list(monthly.index)[prev_m_idx]
                prev_rev = float(monthly.loc[prev_m])
                drop_val = prev_rev - worst_rev
                
                # Peak comparison
                peak_m = monthly.idxmax()
                peak_rev = float(monthly.max())
                drop_vs_peak = peak_rev - worst_rev
                drop_vs_peak_pct = (drop_vs_peak / peak_rev) * 100 if peak_rev > 0 else 0
                
                if drop_val > 0 and (abs(worst_pct) > 2.0 or drop_val > 10_000_000):
                    prio = 'CAO' if (abs(worst_pct) > 10 or drop_val > 50_000_000) else 'TRUNG BÌNH'
                    issues.append({
                        'id': 'issue_trend_break',
                        'priority': prio,
                        'priority_label': prio,
                        'headline': f"Doanh thu tháng {worst_m} sụt giảm {abs(worst_pct):.1f}% so với kỳ trước",
                        'evidence': f"Doanh thu thuần tháng {worst_m} chỉ đạt {vi_format_num(worst_rev)} VND, sụt giảm {vi_format_num(drop_val)} VND ({worst_pct:+.1f}%) so với tháng {prev_m} ({vi_format_num(prev_rev)} VND). So với tháng đỉnh cao {peak_m} ({vi_format_num(peak_rev)} VND), mức giảm lên tới {drop_vs_peak_pct:.1f}%.",
                        'impact': f"Mất trực tiếp {vi_format_num(drop_val)} VND dòng tiền doanh thu trong tháng, gây áp lực trực tiếp lên biên lợi nhuận chung.",
                        'actions': [
                            "(a) Rà soát hiệu quả các chiến dịch tiếp thị và chính sách chiết khấu của tháng suy giảm.",
                            "(b) Tổ chức chương trình khuyến mãi kích cầu dồn vào các tuần cuối chu kỳ kinh doanh.",
                            "(c) Khảo sát ý kiến khách hàng để kiểm tra nguyên nhân giảm tần suất đặt hàng."
                        ],
                        'impact_value': drop_val,
                        'trace_data': {
                            'period': f"Tháng {worst_m} so với {prev_m}",
                            'revenue_current': worst_rev,
                            'revenue_previous': prev_rev,
                            'drop_amount_vnd': drop_val,
                            'drop_percent': worst_pct,
                            'peak_month': peak_m,
                            'peak_revenue': peak_rev
                        }
                    })
                    
            # --- Check 2: Concentration of Decline by Product Group ---
            if cat_col and cat_col in df_t.columns and len(monthly) >= 2:
                # Compare last 2 months for each product group
                last_m = monthly.index[-1]
                prev_m = monthly.index[-2]
                grp_monthly = df_t[df_t['__ym'].isin([prev_m, last_m])].groupby(['__ym', cat_col])[rev_col].sum().unstack(level=0).fillna(0)
                if prev_m in grp_monthly.columns and last_m in grp_monthly.columns:
                    grp_monthly['diff'] = grp_monthly[last_m] - grp_monthly[prev_m]
                    grp_monthly['pct'] = (grp_monthly['diff'] / grp_monthly[prev_m].replace(0, np.nan)) * 100
                    worst_grp = grp_monthly['diff'].idxmin()
                    grp_drop = float(abs(grp_monthly.loc[worst_grp, 'diff']))
                    grp_pct = float(grp_monthly.loc[worst_grp, 'pct'])
                    
                    if grp_drop > 20_000_000 and grp_pct < -5.0:
                        prio = 'CAO' if abs(grp_pct) > 20 else 'TRUNG BÌNH'
                        v_prev = float(grp_monthly.loc[worst_grp, prev_m])
                        v_last = float(grp_monthly.loc[worst_grp, last_m])
                        issues.append({
                            'id': 'issue_group_decline',
                            'priority': prio,
                            'priority_label': prio,
                            'headline': f"Doanh thu {worst_grp} sụt giảm mạnh {abs(grp_pct):.1f}% trong tháng gần nhất",
                            'evidence': f"Trong tháng {last_m}, doanh thu của '{worst_grp}' đạt {vi_format_num(v_last)} VND, sụt giảm {vi_format_num(grp_drop)} VND ({grp_pct:.1f}%) so với tháng {prev_m} ({vi_format_num(v_prev)} VND). Đây là danh mục chịu tổn thất tuyệt đối nặng nhất.",
                            'impact': f"Mất đứt {vi_format_num(grp_drop)} VND doanh thu, chiếm tỷ trọng sụt giảm áp đảo toàn công ty.",
                            'actions': [
                                "(a) Kiểm tra ngay tồn kho và chuỗi cung ứng của nhóm hàng xem có bị thiếu hàng hay chậm giao.",
                                "(b) Phân tích chính sách giá của đối thủ cạnh tranh trực tiếp trong cùng phân khúc.",
                                "(c) Phân bổ lại ngân sách quảng cáo tập trung vào nhóm hàng có nhu cầu hồi phục nhanh hơn."
                            ],
                            'impact_value': grp_drop,
                            'trace_data': {
                                'product_group': worst_grp,
                                'month_previous': prev_m,
                                'revenue_prev_vnd': v_prev,
                                'month_current': last_m,
                                'revenue_curr_vnd': v_last,
                                'loss_vnd': grp_drop,
                                'percent_change': grp_pct
                            }
                        })
        else:
            skipped_checks.append("Kiểm tra chu kỳ thời gian (thiếu cột ngày giao dịch hoặc cột doanh thu)")
            
        # --- Check 3: Profit Margin Disparities across Groups ---
        if cat_col and cat_col in df.columns and rev_col and rev_col in df.columns and profit_col and profit_col in df.columns:
            grp_fin = df.groupby(cat_col).agg({rev_col: 'sum', profit_col: 'sum'})
            grp_fin = grp_fin[grp_fin[rev_col] > 0]
            if len(grp_fin) >= 2:
                grp_fin['margin'] = (grp_fin[profit_col] / grp_fin[rev_col]) * 100
                lowest_grp = grp_fin['margin'].idxmin()
                highest_grp = grp_fin['margin'].idxmax()
                low_margin = float(grp_fin.loc[lowest_grp, 'margin'])
                high_margin = float(grp_fin.loc[highest_grp, 'margin'])
                gap = high_margin - low_margin
                low_rev = float(grp_fin.loc[lowest_grp, rev_col])
                
                if gap > 2.0:
                    potential_gain = low_rev * (gap / 200.0)
                    issues.append({
                        'id': 'issue_margin_disparity',
                        'priority': 'TRUNG BÌNH',
                        'priority_label': 'TRUNG BÌNH',
                        'headline': f"Chênh lệch biên lợi nhuận lớn giữa {lowest_grp} và {highest_grp}",
                        'evidence': f"Nhóm '{lowest_grp}' ghi nhận biên lợi nhuận thấp nhất ở mức {low_margin:.1f}%, trong khi '{highest_grp}' đạt tới {high_margin:.1f}% (chênh lệch {gap:.1f} điểm %). Tổng doanh thu nhóm biên thấp đạt {vi_format_num(low_rev)} VND.",
                        'impact': f"Cơ cấu tiêu thụ tập trung vào nhóm biên thấp làm suy giảm hiệu quả sinh lời chung khoảng {vi_format_num(potential_gain)} VND.",
                        'actions': [
                            "(a) Đàm phán lại chi phí đầu vào và đóng gói với các nhà cung cấp của nhóm biên thấp.",
                            "(b) Đóng gói bán kèm (combo) nhóm biên thấp với nhóm có biên lợi nhuận cao.",
                            "(c) Rà soát lại bảng giá niêm yết để bù đắp các chi phí vận hành gia tăng."
                        ],
                        'impact_value': potential_gain,
                        'trace_data': {
                            'lowest_group': lowest_grp,
                            'lowest_margin_pct': low_margin,
                            'highest_group': highest_grp,
                            'highest_margin_pct': high_margin,
                            'margin_gap_points': gap,
                            'lowest_group_revenue_vnd': low_rev
                        }
                    })
        else:
            skipped_checks.append("Kiểm tra chênh lệch biên lợi nhuận (thiếu cột lợi nhuận hoặc nhóm sản phẩm)")
            
        # --- Check 4: Returns / Cancellations (if status exists) ---
        if status_col and status_col in df.columns and rev_col and rev_col in df.columns:
            status_summary = df.groupby(status_col)[rev_col].agg(['count', 'sum'])
            canceled_names = [s for s in status_summary.index if any(w in str(s).lower() for w in ['hủy', 'huy', 'cancel', 'trả', 'tra'])]
            if canceled_names:
                c_name = canceled_names[0]
                c_count = int(status_summary.loc[c_name, 'count'])
                c_lost_rev = float(status_summary.loc[c_name, 'sum'])
                total_cnt = len(df)
                c_rate = (c_count / total_cnt) * 100 if total_cnt > 0 else 0
                
                if c_rate > 3.0:
                    prio = 'CAO' if c_rate > 10.0 or c_lost_rev > 100_000_000 else 'TRUNG BÌNH'
                    issues.append({
                        'id': 'issue_canceled_orders',
                        'priority': prio,
                        'priority_label': prio,
                        'headline': f"Tỷ lệ đơn hàng trạng thái '{c_name}' chiếm {c_rate:.1f}% tổng giao dịch",
                        'evidence': f"Ghi nhận {c_count:,} đơn hàng rơi vào trạng thái '{c_name}' (tương đương {c_rate:.1f}% tổng số đơn), làm thất thoát tổng cộng {vi_format_num(c_lost_rev)} VND giá trị đơn hàng.",
                        'impact': f"Mất trực tiếp {vi_format_num(c_lost_rev)} VND doanh thu và phát sinh thêm chi phí vận chuyển, đóng gói hàng hóa.",
                        'actions': [
                            "(a) Nâng cấp hệ thống xác nhận đơn hàng tự động để sàng lọc các đơn hàng ảo.",
                            "(b) Rút ngắn thời gian bàn giao bưu tá để giảm thiểu tỷ lệ khách hàng đổi ý hủy đơn.",
                            "(c) Phân tích lý do hoàn đơn chi tiết theo từng khu vực giao nhận."
                        ],
                        'impact_value': c_lost_rev,
                        'trace_data': {
                            'status_name': c_name,
                            'canceled_orders_count': c_count,
                            'canceled_orders_rate_pct': c_rate,
                            'lost_revenue_vnd': c_lost_rev
                        }
                    })
        else:
            skipped_checks.append("Kiểm tra tỷ lệ hủy đơn & hoàn trả (không có cột trạng thái đơn hàng)")
            
        # --- Check 5: Growth Opportunity in High Margin Category ---
        if cat_col and cat_col in df.columns and rev_col and rev_col in df.columns and profit_col and profit_col in df.columns:
            grp_fin = df.groupby(cat_col).agg({rev_col: 'sum', profit_col: 'sum'})
            tot_rev = float(df[rev_col].sum())
            if tot_rev > 0 and len(grp_fin) >= 2:
                grp_fin['margin'] = (grp_fin[profit_col] / grp_fin[rev_col]) * 100
                grp_fin['rev_share'] = (grp_fin[rev_col] / tot_rev) * 100
                best_grp = grp_fin['margin'].idxmax()
                b_margin = float(grp_fin.loc[best_grp, 'margin'])
                b_share = float(grp_fin.loc[best_grp, 'rev_share'])
                b_rev = float(grp_fin.loc[best_grp, rev_col])
                opp_profit = b_rev * 0.2 * (b_margin / 100.0)
                
                issues.append({
                    'id': 'issue_opportunity_margin',
                    'priority': 'CƠ HỘI',
                    'priority_label': 'CƠ HỘI',
                    'headline': f"Cơ hội mở rộng doanh số cho {best_grp} với biên lợi nhuận {b_margin:.1f}%",
                    'evidence': f"Nhóm '{best_grp}' sở hữu tỷ suất sinh lời vượt trội {b_margin:.1f}% nhưng mới chỉ chiếm {b_share:.1f}% tổng doanh thu toàn kỳ ({vi_format_num(b_rev)} VND).",
                    'impact': f"Nếu nâng doanh thu nhóm này thêm 20%, lợi nhuận toàn doanh nghiệp ước tính sẽ tăng thêm khoảng {vi_format_num(opp_profit)} VND.",
                    'actions': [
                        "(a) Gia tăng diện tích trưng bày và thứ hạng xuất hiện của nhóm hàng trên các kênh trực tuyến.",
                        "(b) Xây dựng gói quảng cáo tập trung làm nổi bật điểm mạnh khác biệt của sản phẩm.",
                        "(c) Ban hành chính sách khuyến khích hoa hồng cho đội ngũ bán hàng khi chốt sản phẩm này."
                    ],
                    'impact_value': opp_profit,
                    'trace_data': {
                        'product_group': best_grp,
                        'profit_margin_pct': b_margin,
                        'revenue_share_pct': b_share,
                        'current_revenue_vnd': b_rev,
                        'potential_profit_gain_vnd': opp_profit
                    }
                })
                
        # Sort issues: CAO first, then TRUNG BÌNH, then CƠ HỘI; then by impact_value desc
        priority_rank = {'CAO': 1, 'TRUNG BÌNH': 2, 'CƠ HỘI': 3}
        issues.sort(key=lambda x: (priority_rank.get(x['priority'], 4), -x.get('impact_value', 0)))
        
        # Limit to 3-7 issues
        final_issues = issues[:7]
        
        return {
            'issues': final_issues,
            'total_issues': len(final_issues),
            'skipped_checks': skipped_checks,
            'footnote': "Ngưỡng trọng yếu (Materiality Threshold): Các vấn đề được ghi nhận khi mức sụt giảm MoM > 10%, chênh lệch biên lợi nhuận > 2 điểm %, tỷ lệ đơn hủy > 3%, hoặc nhóm hàng chiếm trên 5% tổng doanh thu. Thứ tự ưu tiên xếp theo tác động tài chính trực tiếp."
        }

    def compute_summary_stats(self) -> Dict[str, Any]:
        """Compute comprehensive statistics for numeric, categorical, and date columns."""
        df = self.df
        numeric_stats = {}
        categorical_stats = {}
        date_stats = {}
        
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for col in num_cols:
            s = df[col].dropna()
            if s.empty: continue
            numeric_stats[col] = {
                'count': int(s.count()),
                'sum': float(s.sum()),
                'mean': float(s.mean()),
                'median': float(s.median()),
                'min': float(s.min()),
                'max': float(s.max()),
                'std': float(s.std()) if len(s) > 1 else 0.0
            }
            
        cat_cols = [c for c in df.columns if c not in num_cols]
        for col in cat_cols:
            s = df[col].dropna().astype(str)
            if s.empty: continue
            val_counts = s.value_counts()
            top_vals = [{'value': str(v), 'count': int(c), 'percentage': round((c / len(s)) * 100, 2)} for v, c in val_counts.head(10).items()]
            categorical_stats[col] = {
                'distinct_count': int(s.nunique()),
                'top_value': str(val_counts.index[0]) if not val_counts.empty else '',
                'top_count': int(val_counts.iloc[0]) if not val_counts.empty else 0,
                'distribution': top_vals
            }
            
        date_col = self.roles.get('date_col')
        if date_col and date_col in df.columns:
            try:
                date_series = pd.to_datetime(df[date_col], errors='coerce').dropna()
                if not date_series.empty:
                    min_date = date_series.min()
                    max_date = date_series.max()
                    date_stats = {
                        'column': date_col,
                        'min_date': min_date.strftime('%Y-%m-%d'),
                        'max_date': max_date.strftime('%Y-%m-%d'),
                        'total_days': (max_date - min_date).days + 1,
                        'total_months': (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1
                    }
            except Exception:
                pass
                
        return {
            'numeric_columns': numeric_stats,
            'categorical_columns': categorical_stats,
            'date_stats': date_stats
        }

    def compute_correlations(self) -> Dict[str, Any]:
        """Compute correlation matrix for numeric columns."""
        df = self.df
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(num_cols) < 2:
            return {'columns': num_cols, 'matrix': []}
            
        corr_df = df[num_cols].corr().fillna(0).round(4)
        matrix = [[float(corr_df.loc[col, c]) for c in num_cols] for col in num_cols]
        return {'columns': num_cols, 'matrix': matrix}

    def compute_anomalies(self) -> List[Dict[str, Any]]:
        """Identify outliers using 3 standard deviations and IQR method."""
        df = self.df
        anomalies = []
        rev_col = self.roles.get('net_revenue_col') or self.roles.get('revenue_col')
        target_cols = [rev_col] if rev_col and rev_col in df.columns else [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:2]
        
        for col in target_cols:
            s = df[col].dropna()
            if len(s) < 10: continue
            mean = s.mean()
            std = s.std()
            q1 = s.quantile(0.25)
            q3 = s.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            for idx, row in outliers.head(5).iterrows():
                val = float(row[col])
                z_score = round((val - mean) / std, 2) if std > 0 else 0
                anomalies.append({
                    'row_index': int(idx) + 1,
                    'column': col,
                    'value': val,
                    'mean': round(float(mean), 2),
                    'z_score': z_score,
                    'type': 'Cao bất thường' if val > mean else 'Thấp bất thường',
                    'order_id': str(row.get(self.roles.get('order_col', ''), f'Row #{idx+1}'))
                })
        return anomalies

    def answer_business_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Map user business questions from Step 1 to exact calculations with concrete numbers."""
        df = self.df
        rev_col = self.roles.get('net_revenue_col') or self.roles.get('revenue_col', '')
        prof_col = self.roles.get('profit_col', '')
        cat_col = self.roles.get('category_col', '')
        chan_col = self.roles.get('channel_col', '')
        date_col = self.roles.get('date_col', '')
        
        answers = []
        for q in questions:
            q_clean = q.strip()
            if not q_clean: continue
            q_lower = q_clean.lower()
            answer_text = ""
            metrics_used = {}
            
            # Channel questions
            if any(k in q_lower for k in ['kênh', 'kenh', 'channel']) and chan_col and rev_col and chan_col in df.columns and rev_col in df.columns:
                grp = df.groupby(chan_col)[rev_col].sum().sort_values(ascending=False)
                if not grp.empty:
                    top_chan = grp.index[0]
                    top_val = float(grp.iloc[0])
                    lowest_chan = grp.index[-1]
                    lowest_val = float(grp.iloc[-1])
                    total_rev = float(df[rev_col].sum())
                    top_pct = round((top_val / total_rev) * 100, 1) if total_rev > 0 else 0
                    answer_text = (
                        f"Kênh bán hàng có doanh thu thuần cao nhất là '{top_chan}' đạt {vi_format_num(top_val)} VND, "
                        f"chiếm {top_pct}% tổng doanh thu toàn bộ ({vi_format_num(total_rev)} VND). "
                        f"Kênh thấp nhất là '{lowest_chan}' với {vi_format_num(lowest_val)} VND."
                    )
                    metrics_used = {'top_channel': top_chan, 'top_revenue': top_val, 'percentage': top_pct}
                
            # Product group questions
            elif any(k in q_lower for k in ['nhóm', 'sản phẩm', 'ngành hàng', 'mặt hàng', 'category']) and cat_col and rev_col and cat_col in df.columns and rev_col in df.columns:
                grp = df.groupby(cat_col)[rev_col].sum().sort_values(ascending=False)
                if not grp.empty:
                    top_cat = grp.index[0]
                    top_val = float(grp.iloc[0])
                    bot_cat = grp.index[-1]
                    bot_val = float(grp.iloc[-1])
                    gap = top_val - bot_val
                    answer_text = (
                        f"Nhóm hàng dẫn đầu về doanh thu thuần là '{top_cat}' với tổng mức {vi_format_num(top_val)} VND. "
                        f"Nhóm đứng cuối là '{bot_cat}' đạt {vi_format_num(bot_val)} VND, "
                        f"chênh lệch giữa nhóm cao nhất và thấp nhất là {vi_format_num(gap)} VND."
                    )
                    metrics_used = {'top_category': top_cat, 'top_revenue': top_val, 'gap': gap}
                
            # Profit / margin questions
            elif any(k in q_lower for k in ['lợi nhuận', 'loi_nhuan', 'ros', 'tỷ suất', 'biên lợi nhuận', 'hiệu quả']) and rev_col and prof_col and rev_col in df.columns and prof_col in df.columns:
                total_rev = float(df[rev_col].sum())
                total_prof = float(df[prof_col].sum())
                ros = round((total_prof / total_rev) * 100, 1) if total_rev > 0 else 0
                
                if cat_col and cat_col in df.columns:
                    grp_p = df.groupby(cat_col).agg({rev_col: 'sum', prof_col: 'sum'})
                    if not grp_p.empty and grp_p[rev_col].sum() > 0:
                        grp_p['ros'] = (grp_p[prof_col] / grp_p[rev_col] * 100).round(1)
                        best_ros_cat = grp_p['ros'].idxmax()
                        best_ros_val = float(grp_p.loc[best_ros_cat, 'ros'])
                        answer_text = (
                            f"Tổng lợi nhuận kinh doanh đạt {vi_format_num(total_prof)} VND trên tổng doanh thu thuần {vi_format_num(total_rev)} VND, "
                            f"tương ứng biên lợi nhuận (ROS) trung bình toàn doanh nghiệp là {ros}%. "
                            f"Nhóm đạt biên lợi nhuận cao nhất là '{best_ros_cat}' với mức {best_ros_val}%."
                        )
                        metrics_used = {'total_profit': total_prof, 'ros': ros, 'best_ros_cat': best_ros_cat}
                    else:
                        answer_text = f"Tổng lợi nhuận kinh doanh đạt {vi_format_num(total_prof)} VND, biên lợi nhuận đạt {ros}%."
                        metrics_used = {'total_profit': total_prof, 'ros': ros}
                else:
                    answer_text = f"Tổng lợi nhuận kinh doanh đạt {vi_format_num(total_prof)} VND, biên lợi nhuận đạt {ros}%."
                    metrics_used = {'total_profit': total_prof, 'ros': ros}
                    
            # Time trends questions
            elif any(k in q_lower for k in ['tháng', 'thời gian', 'xu hướng', 'tăng trưởng', 'chu kỳ']) and date_col and rev_col and date_col in df.columns and rev_col in df.columns:
                df_temp = df.copy()
                df_temp['YM'] = pd.to_datetime(df_temp[date_col], errors='coerce').dt.strftime('%Y-%m')
                monthly = df_temp.groupby('YM')[rev_col].sum()
                if len(monthly) > 1:
                    peak_m = monthly.idxmax()
                    peak_v = float(monthly.max())
                    low_m = monthly.idxmin()
                    low_v = float(monthly.min())
                    answer_text = (
                        f"Trong toàn bộ giai đoạn theo dõi, tháng có doanh thu thuần đỉnh điểm là {peak_m} đạt {vi_format_num(peak_v)} VND. "
                        f"Tháng có doanh thu thấp nhất là {low_m} với {vi_format_num(low_v)} VND."
                    )
                    metrics_used = {'peak_month': peak_m, 'peak_revenue': peak_v, 'low_month': low_m, 'low_revenue': low_v}
                else:
                    answer_text = f"Dữ liệu có tổng doanh thu {vi_format_num(df[rev_col].sum())} VND trải dài trong kỳ."
                    metrics_used = {'total_rev': float(df[rev_col].sum())}
            
            # Default fallback
            if not answer_text:
                if rev_col and rev_col in df.columns:
                    total_r = float(df[rev_col].sum())
                    avg_r = float(df[rev_col].mean())
                    count_r = len(df)
                    answer_text = (
                        f"Dựa trên phân tích toàn bộ {count_r} giao dịch: tổng doanh thu thuần đạt {vi_format_num(total_r)} VND, "
                        f"bình quân mỗi giao dịch đạt {vi_format_num(avg_r)} VND."
                    )
                    metrics_used = {'total_revenue': total_r, 'average_order': avg_r, 'count': count_r}
                else:
                    answer_text = f"Tập dữ liệu ghi nhận tổng cộng {len(df)} dòng dữ liệu hợp lệ được xử lý."
                    metrics_used = {'count': len(df)}
                    
            answers.append({
                'question': q_clean,
                'answer': answer_text,
                'metrics': metrics_used
            })
            
        return answers
