import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.audit_log: List[Dict[str, Any]] = []
        
    def detect_issues(self) -> Dict[str, Any]:
        """Detect all data quality issues: missing values, duplicates, dates, numeric in text, casing."""
        df = self.df
        total_rows = len(df)
        issues = {
            'total_rows': total_rows,
            'total_columns': len(df.columns),
            'missing_values': {},
            'duplicates_count': int(df.duplicated().sum()),
            'numeric_as_text': {},
            'date_inconsistencies': {},
            'casing_inconsistencies': {},
            'summary_count': 0
        }
        
        # 1. Missing values
        for col in df.columns:
            is_empty_str = df[col].astype(str).str.strip().isin(['', 'nan', 'null', 'None', 'NA', 'N/A'])
            missing_count = int(df[col].isna().sum() + is_empty_str.sum())
            if missing_count > 0:
                issues['missing_values'][col] = {
                    'count': missing_count,
                    'percentage': round((missing_count / total_rows) * 100, 2)
                }
                issues['summary_count'] += 1
                
        if issues['duplicates_count'] > 0:
            issues['summary_count'] += 1
            
        # 2. Check each column
        for col in df.columns:
            series = df[col].dropna().astype(str).str.strip()
            if series.empty:
                continue
                
            # Check numeric as text with currency/symbols
            num_pattern_count = 0
            sample_non_num = 0
            for val in series.head(100):
                v = val.strip()
                if not v:
                    continue
                cleaned_v = re.sub(r'[\sđ₫$€£%]', '', v)
                if re.match(r'^-?\d{1,3}([.,]\d{3})+([.,]\d+)?$', cleaned_v) or \
                   re.match(r'^-?\d+([.,]\d+)?%$', v) or \
                   (any(sym in v for sym in ['đ', '₫', '$', '€']) and re.search(r'\d', v)):
                    num_pattern_count += 1
                elif not v.replace('.', '', 1).replace('-', '', 1).isdigit():
                    sample_non_num += 1
                    
            if num_pattern_count > 0 and num_pattern_count >= sample_non_num * 0.3:
                issues['numeric_as_text'][col] = {
                    'detected_count': num_pattern_count,
                    'examples': series.head(3).tolist()
                }
                issues['summary_count'] += 1
                
            # Check date formats
            date_matches = 0
            formats_found = set()
            for val in series.head(50):
                v = val.strip()
                if re.match(r'^\d{4}-\d{1,2}-\d{1,2}', v):
                    formats_found.add('YYYY-MM-DD')
                    date_matches += 1
                elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}', v):
                    formats_found.add('DD/MM/YYYY')
                    date_matches += 1
                elif re.match(r'^\d{1,2}-\d{1,2}-\d{4}', v):
                    formats_found.add('DD-MM-YYYY')
                    date_matches += 1
                    
            if len(formats_found) > 1 or (date_matches > 10 and 'YYYY-MM-DD' not in formats_found):
                issues['date_inconsistencies'][col] = {
                    'formats_detected': list(formats_found),
                    'examples': series.head(3).tolist()
                }
                issues['summary_count'] += 1
                
            # Check whitespace and casing in text columns
            if col not in issues['numeric_as_text'] and date_matches < 10:
                has_whitespace = series.str.contains(r'^\s+|\s+$|\s{2,}', regex=True).sum()
                unique_vals = series.unique()
                lower_map = {}
                casing_duplicates = 0
                for u in unique_vals:
                    norm = u.strip().lower()
                    if norm in lower_map and lower_map[norm] != u.strip():
                        casing_duplicates += 1
                    else:
                        lower_map[norm] = u.strip()
                        
                if has_whitespace > 0 or casing_duplicates > 0:
                    issues['casing_inconsistencies'][col] = {
                        'whitespace_count': int(has_whitespace),
                        'casing_variations_count': casing_duplicates,
                        'examples': series.head(3).tolist()
                    }
                    issues['summary_count'] += 1
                    
        return issues

    def apply_action(self, action_type: str, column: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply a cleaning action with before/after tracking and audit logging."""
        params = params or {}
        before_rows = len(self.df)
        before_cols = len(self.df.columns)
        action_name_vi = ""
        details_vi = ""
        
        if action_type == 'drop_duplicates':
            dup_count = int(self.df.duplicated().sum())
            self.df = self.df.drop_duplicates().reset_index(drop=True)
            action_name_vi = "Xóa dòng trùng lặp"
            details_vi = f"Đã loại bỏ {dup_count} dòng trùng lặp hoàn toàn."
            
        elif action_type == 'drop_missing_rows':
            if column and column in self.df.columns:
                mask = self.df[column].isna() | self.df[column].astype(str).str.strip().isin(['', 'nan', 'null', 'None', 'NA', 'N/A'])
                dropped = int(mask.sum())
                self.df = self.df[~mask].reset_index(drop=True)
                action_name_vi = f"Xóa dòng thiếu ở cột '{column}'"
                details_vi = f"Đã xóa {dropped} dòng có giá trị trống."
            else:
                before = len(self.df)
                self.df = self.df.dropna().reset_index(drop=True)
                dropped = before - len(self.df)
                action_name_vi = "Xóa tất cả dòng chứa giá trị trống"
                details_vi = f"Đã xóa {dropped} dòng chứa ô trống."
                
        elif action_type == 'fill_missing':
            method = params.get('method', 'zero')
            custom_val = params.get('value', 0)
            if column and column in self.df.columns:
                series = self.df[column].replace(['', 'nan', 'null', 'None', 'NA', 'N/A'], np.nan)
                fill_val = 0
                numeric_series = pd.to_numeric(series.astype(str).str.replace(r'[\sđ₫$€£%,]', '', regex=True), errors='coerce')
                
                if method == 'mean' and not numeric_series.dropna().empty:
                    fill_val = round(numeric_series.mean(), 2)
                elif method == 'median' and not numeric_series.dropna().empty:
                    fill_val = round(numeric_series.median(), 2)
                elif method == 'mode':
                    mode_val = series.mode()
                    fill_val = mode_val[0] if not mode_val.empty else "N/A"
                elif method == 'zero':
                    fill_val = 0
                elif method == 'custom':
                    fill_val = custom_val
                    
                missing_cnt = int(series.isna().sum())
                self.df[column] = series.fillna(fill_val)
                action_name_vi = f"Điền giá trị thiếu ở cột '{column}'"
                details_vi = f"Đã điền {missing_cnt} giá trị trống bằng phương pháp '{method}' (giá trị: {fill_val})."
                
        elif action_type == 'drop_column':
            if column and column in self.df.columns:
                self.df = self.df.drop(columns=[column])
                action_name_vi = f"Xóa cột '{column}'"
                details_vi = f"Đã loại bỏ cột '{column}' khỏi tập dữ liệu."
                
        elif action_type == 'standardize_numeric':
            if column and column in self.df.columns:
                def clean_num(val):
                    if pd.isna(val):
                        return np.nan
                    v = str(val).strip()
                    if not v or v.lower() in ['nan', 'null', 'none']:
                        return np.nan
                    is_pct = '%' in v
                    v = re.sub(r'[\sđ₫$€£]', '', v)
                    v = v.replace('%', '')
                    if re.match(r'^-?\d{1,3}(\.\d{3})+(,\d+)?$', v):
                        v = v.replace('.', '').replace(',', '.')
                    elif re.match(r'^-?\d{1,3}(,\d{3})+(\.\d+)?$', v):
                        v = v.replace(',', '')
                    try:
                        num = float(v)
                        return num / 100.0 if is_pct else num
                    except ValueError:
                        return np.nan
                        
                self.df[column] = self.df[column].apply(clean_num)
                action_name_vi = f"Chuẩn hóa số ở cột '{column}'"
                details_vi = f"Đã chuyển đổi văn bản sang số, loại bỏ ký hiệu tiền tệ và phân cách hàng nghìn."
                
        elif action_type == 'standardize_date':
            target_fmt = params.get('format', '%Y-%m-%d')
            if column and column in self.df.columns:
                def parse_date(val):
                    if pd.isna(val):
                        return np.nan
                    v = str(val).strip()
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                        try:
                            dt = datetime.strptime(v.split(' ')[0], fmt)
                            return dt.strftime(target_fmt)
                        except ValueError:
                            continue
                    try:
                        return pd.to_datetime(v).strftime(target_fmt)
                    except Exception:
                        return v
                        
                self.df[column] = self.df[column].apply(parse_date)
                action_name_vi = f"Chuẩn hóa ngày ở cột '{column}'"
                details_vi = f"Đã thống nhất định dạng ngày về chuẩn {target_fmt}."
                
        elif action_type == 'trim_and_case':
            case_type = params.get('case', 'trim')
            if column and column in self.df.columns:
                s = self.df[column].astype(str).str.strip()
                s = s.str.replace(r'\s+', ' ', regex=True)
                if case_type == 'title':
                    s = s.str.title()
                elif case_type == 'upper':
                    s = s.str.upper()
                elif case_type == 'lower':
                    s = s.str.lower()
                self.df[column] = s
                action_name_vi = f"Chuẩn hóa khoảng trắng & chữ viết cột '{column}'"
                details_vi = f"Đã cắt bỏ khoảng trắng thừa và chuyển đổi kiểu chữ ({case_type})."
        else:
            raise ValueError(f"Hành động không xác định: {action_type}")
            
        after_rows = len(self.df)
        after_cols = len(self.df.columns)
        
        log_entry = {
            'id': len(self.audit_log) + 1,
            'timestamp': datetime.now().strftime('%H:%M:%S %d/%m/%Y'),
            'action_type': action_type,
            'column': column or 'Tất cả',
            'action_name': action_name_vi,
            'details': details_vi,
            'before_rows': before_rows,
            'after_rows': after_rows,
            'before_cols': before_cols,
            'after_cols': after_cols,
            'rows_changed': abs(before_rows - after_rows)
        }
        self.audit_log.append(log_entry)
        return log_entry

    def auto_clean_all(self) -> List[Dict[str, Any]]:
        """Automatically clean common obvious issues: remove duplicates, trim whitespace, standardize numbers/dates."""
        logs = []
        if self.df.duplicated().sum() > 0:
            logs.append(self.apply_action('drop_duplicates'))
            
        for col in self.df.columns:
            series = self.df[col].dropna().astype(str).str.strip()
            if series.empty:
                continue
            has_currency_symbols = series.str.contains(r'[đ₫$€£%]', regex=True) & series.str.contains(r'\d', regex=True)
            if has_currency_symbols.sum() > len(series) * 0.3:
                logs.append(self.apply_action('standardize_numeric', column=col))
            elif pd.to_numeric(series, errors='coerce').notna().mean() > 0.8:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                
        for col in self.df.columns:
            if self.df[col].dtype == object:
                sample = self.df[col].dropna().astype(str)
                if sample.str.contains(r'^\s+|\s+$|\s{2,}', regex=True).sum() > 0:
                    logs.append(self.apply_action('trim_and_case', column=col, params={'case': 'trim'}))
                    
        return logs

    def detect_column_roles(self) -> Dict[str, str]:
        """
        Auto-detect semantic column roles with expanded taxonomy:
        gross_revenue_col, net_revenue_col, discount_col, return_col, tax_col,
        cogs_col, operating_cost_col, profit_col, quantity_col, order_col,
        date_col, category_col, channel_col, delivery_days_col, status_col.
        """
        df = self.df
        roles: Dict[str, str] = {
            'date_col': '',
            'order_col': '',
            'category_col': '',
            'channel_col': '',
            'quantity_col': '',
            'gross_revenue_col': '',
            'net_revenue_col': '',
            'discount_col': '',
            'return_col': '',
            'tax_col': '',
            'cogs_col': '',
            'operating_cost_col': '',
            'profit_col': '',
            'delivery_days_col': '',
            'status_col': '',
            # Backward-compatibility alias
            'revenue_col': '',
            'cost_col': ''
        }
        
        assigned_cols = set()
        
        # 1. Date
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['ngày đặt', 'ngày giao', 'ngày', 'ngay_giao_dich', 'ngay', 'date', 'order_date', 'thời gian', 'time']) and col not in assigned_cols:
                roles['date_col'] = col
                assigned_cols.add(col)
                break
                
        # 2. Order ID
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['mã đơn', 'ma_don', 'vận đơn', 'van_don', 'order_id', 'order id', 'mã', 'id']) and col not in assigned_cols:
                roles['order_col'] = col
                assigned_cols.add(col)
                break
                
        # 3. Category / Product Group
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['nhóm sản phẩm', 'nhom_san_pham', 'ngành hàng', 'nganh_hang', 'sản phẩm', 'category', 'product group', 'mặt hàng', 'nhóm']) and col not in assigned_cols:
                roles['category_col'] = col
                assigned_cols.add(col)
                break
                
        # 4. Channel / Region
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['kênh bán hàng', 'kênh phân phối', 'kênh', 'kenh', 'channel', 'khu vực', 'khu_vuc', 'region']) and col not in assigned_cols:
                roles['channel_col'] = col
                assigned_cols.add(col)
                break
                
        # 5. Quantity
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['số lượng', 'so_luong', 'quantity', 'qty']) and col not in assigned_cols:
                roles['quantity_col'] = col
                assigned_cols.add(col)
                break

        # 6. Discounts, Returns, Taxes
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['chiết khấu', 'giảm giá', 'chiet_khau', 'giam_gia', 'discount', 'voucher']) and col not in assigned_cols:
                roles['discount_col'] = col
                assigned_cols.add(col)
                break
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['hàng trả lại', 'trả hàng', 'hoàn tiền', 'tra_hang', 'return', 'refund']) and col not in assigned_cols:
                roles['return_col'] = col
                assigned_cols.add(col)
                break
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['thuế', 'thue', 'vat', 'tax']) and col not in assigned_cols:
                roles['tax_col'] = col
                assigned_cols.add(col)
                break

        # 7. Net Revenue vs Gross Revenue
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['doanh thu thuần', 'doanh_thu_thuan', 'net revenue', 'net_revenue']) and col not in assigned_cols:
                roles['net_revenue_col'] = col
                assigned_cols.add(col)
                break
                
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['doanh thu gộp', 'doanh thu bán hàng', 'gross revenue', 'tổng tiền', 'tong_tien', 'thành tiền', 'doanh thu', 'doanh_thu', 'sales']) and col not in assigned_cols:
                roles['gross_revenue_col'] = col
                assigned_cols.add(col)
                break
                
        # If neither is found or only one:
        if not roles['net_revenue_col'] and roles['gross_revenue_col']:
            roles['net_revenue_col'] = roles['gross_revenue_col']
        elif not roles['gross_revenue_col'] and roles['net_revenue_col']:
            roles['gross_revenue_col'] = roles['net_revenue_col']
            
        roles['revenue_col'] = roles['net_revenue_col'] or roles['gross_revenue_col']

        # 8. COGS (Giá vốn hàng bán) and Operating Costs
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['giá vốn', 'gia_von', 'cogs', 'chi_phi_von', 'cost of goods']) and col not in assigned_cols:
                roles['cogs_col'] = col
                assigned_cols.add(col)
                break
                
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['chi phí bán hàng', 'chi phí quản lý', 'chi phí vận hành', 'chi phí', 'chi_phi', 'phi_van_chuyen', 'operating cost', 'opex']) and col not in assigned_cols:
                roles['operating_cost_col'] = col
                assigned_cols.add(col)
                break
                
        roles['cost_col'] = roles['cogs_col'] or roles['operating_cost_col']

        # 9. Profit
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['lợi nhuận', 'loi_nhuan', 'profit', 'lãi', 'lợi nhuận thuần', 'lợi nhuận ròng', 'lợi nhuận hđkd']) and col not in assigned_cols:
                roles['profit_col'] = col
                assigned_cols.add(col)
                break

        # 10. Delivery days & Status
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['thời gian giao hàng', 'ngày giao', 'delivery', 'giao_hang']) and col not in assigned_cols:
                roles['delivery_days_col'] = col
                assigned_cols.add(col)
                break
                
        for col in df.columns:
            c_low = col.lower().strip()
            if any(k in c_low for k in ['trạng thái', 'tình trạng', 'status', 'trang_thai']) and col not in assigned_cols:
                roles['status_col'] = col
                assigned_cols.add(col)
                break

        # Fallbacks for critical missing roles
        if not roles['net_revenue_col']:
            num_cols = [c for c in df.columns if pd.to_numeric(df[c].astype(str).str.replace(r'[\sđ₫$€£%,.]', '', regex=True), errors='coerce').notna().mean() > 0.7]
            if num_cols:
                roles['net_revenue_col'] = num_cols[0]
                roles['gross_revenue_col'] = num_cols[0]
                roles['revenue_col'] = num_cols[0]
                
        if not roles['category_col']:
            cat_candidates = [c for c in df.columns if c not in assigned_cols and df[c].dtype == object and 2 <= df[c].nunique() <= 30]
            if cat_candidates:
                roles['category_col'] = cat_candidates[0]

        return roles

    def get_column_mapping_details(self, roles: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Produce a structured table of column mappings with role, confidence, sample value, and formula role.
        """
        df = self.df
        active_roles = roles or self.detect_column_roles()
        
        schema_definitions = [
            {'key': 'net_revenue_col', 'name': 'Doanh thu thuần (Net revenue)', 'required': True, 'formula': 'Doanh thu gộp − Chiết khấu − Trả hàng − Thuế'},
            {'key': 'gross_revenue_col', 'name': 'Doanh thu gộp (Gross revenue)', 'required': False, 'formula': 'Tổng giá trị bán trước giảm trừ'},
            {'key': 'profit_col', 'name': 'Lợi nhuận (Profit)', 'required': False, 'formula': 'Doanh thu thuần − Giá vốn (COGS) − Chi phí vận hành'},
            {'key': 'cogs_col', 'name': 'Giá vốn hàng bán (COGS)', 'required': False, 'formula': 'Chi phí vốn sản xuất hoặc mua vào'},
            {'key': 'operating_cost_col', 'name': 'Chi phí vận hành / Khác', 'required': False, 'formula': 'Chi phí bán hàng, vận chuyển, quản lý'},
            {'key': 'discount_col', 'name': 'Chiết khấu / Giảm giá', 'required': False, 'formula': 'Khoản giảm trừ doanh thu'},
            {'key': 'return_col', 'name': 'Hàng trả lại / Hoàn tiền', 'required': False, 'formula': 'Khoản giảm trừ do hủy hoặc trả hàng'},
            {'key': 'tax_col', 'name': 'Thuế (VAT / Thuế bán hàng)', 'required': False, 'formula': 'Khoản thuế phải nộp trong đơn giá'},
            {'key': 'date_col', 'name': 'Ngày / Thời gian giao dịch', 'required': True, 'formula': 'Trục thời gian phân tích chu kỳ, tháng, năm'},
            {'key': 'category_col', 'name': 'Nhóm sản phẩm / Ngành hàng', 'required': True, 'formula': 'Phân tích cơ cấu và so sánh danh mục'},
            {'key': 'channel_col', 'name': 'Kênh bán hàng / Khu vực', 'required': False, 'formula': 'Phân bổ doanh thu và hiệu quả kênh'},
            {'key': 'order_col', 'name': 'Mã đơn hàng / Vận đơn', 'required': False, 'formula': 'Đếm số đơn hàng độc lập, tính AOV'},
            {'key': 'quantity_col', 'name': 'Số lượng sản phẩm bán', 'required': False, 'formula': 'Tổng sản lượng tiêu thụ'}
        ]
        
        details = []
        for defn in schema_definitions:
            k = defn['key']
            mapped_col = active_roles.get(k, '')
            is_mapped = bool(mapped_col and mapped_col in df.columns)
            sample_val = "N/A"
            confidence = "Chưa xác định"
            
            if is_mapped:
                s = df[mapped_col].dropna()
                sample_val = str(s.iloc[0]) if not s.empty else "Rỗng"
                if len(sample_val) > 25:
                    sample_val = sample_val[:22] + "..."
                confidence = "Tự động phát hiện (Cao)"
            elif not defn['required']:
                confidence = "Không bắt buộc (Không có trong tệp)"
            else:
                confidence = "Yêu cầu người dùng chọn"
                
            details.append({
                'role_key': k,
                'role_name': defn['name'],
                'required': defn['required'],
                'mapped_column': mapped_col if is_mapped else '',
                'confidence': confidence,
                'sample_value': sample_val,
                'formula_note': defn['formula']
            })
            
        return details
