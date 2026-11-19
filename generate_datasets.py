import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_marketing_sales():
    np.random.seed(42)
    
    # Target values from reference image
    target_total_revenue = 20717175575
    target_total_orders = 1366
    target_t10_orders = 107
    target_t10_revenue = 1666023008
    
    # Months: 2018-11 to 2019-10 (12 months)
    months = [
        ('2018-11', 'T11-2018'),
        ('2018-12', 'T12-2018'),
        ('2019-01', 'T01-2019'),
        ('2019-02', 'T02-2019'),
        ('2019-03', 'T03-2019'),
        ('2019-04', 'T04-2019'),
        ('2019-05', 'T05-2019'),
        ('2019-06', 'T06-2019'),
        ('2019-07', 'T07-2019'),
        ('2019-08', 'T08-2019'),
        ('2019-09', 'T09-2019'),
        ('2019-10', 'T10-2019')
    ]
    
    # Target revenues for Nhóm chuối across 12 months (in millions)
    chuoi_monthly_millions = {
        '2018-11': 357,
        '2018-12': 307,
        '2019-01': 284,
        '2019-02': 428,
        '2019-03': 434,
        '2019-04': 393,
        '2019-05': 434,
        '2019-06': 311,
        '2019-07': 336,
        '2019-08': 399,
        '2019-09': 479,
        '2019-10': 222
    }
    
    # Target for T10 by product group (in millions)
    t10_groups = {
        'Nhóm chuối': (222_000_000, 48_840_000),
        'Nhóm khoai': (264_000_000, 60_720_000),
        'Nhóm mít':   (418_000_000, 85_260_000),
        'Nhóm thơm':  (363_000_000, 87_900_000),
        'Nhóm xoài':  (399_023_008, 91_200_000),
    }
    # Sum of T10 revenue = 1,666,023,008
    # Sum of T10 profit = 373,920,000 (ROS = 22.44% -> 22%)
    
    # Month 11 (2019-09) revenue must be ~1,717,549,493 so growth is -3.0%
    t09_revenue = int(target_t10_revenue / 0.97) # ~ 1,717,549,493
    
    # Distribute 1,366 orders across 12 months:
    # 107 orders in T10, remaining 1259 distributed across 11 months (~114 per month)
    order_counts = {}
    remaining_orders = target_total_orders - target_t10_orders
    for i, (ym, label) in enumerate(months[:-1]):
        if i == 10: # T09
            order_counts[ym] = 118
        else:
            order_counts[ym] = 114 if i % 2 == 0 else 115
    # adjust total to 1259
    diff = remaining_orders - sum(order_counts.values())
    order_counts['2018-11'] += diff
    order_counts['2019-10'] = target_t10_orders
    
    channels = ['Đại lý', 'Bán lẻ trực tiếp', 'Shopee', 'Tiki', 'Website']
    groups = ['Nhóm chuối', 'Nhóm khoai', 'Nhóm mít', 'Nhóm thơm', 'Nhóm xoài']
    
    records = []
    order_id_counter = 1
    
    # Generate for T10 (2019-10) with exact group totals
    # 107 orders in T10: distribute among groups (~21-22 orders each)
    t10_group_order_counts = {
        'Nhóm chuối': 21,
        'Nhóm khoai': 20,
        'Nhóm mít': 22,
        'Nhóm thơm': 21,
        'Nhóm xoài': 23
    } # sum = 107
    
    for grp, (grp_rev, grp_profit) in t10_groups.items():
        n_ords = t10_group_order_counts[grp]
        # random partitions of grp_rev
        weights = np.random.uniform(0.7, 1.3, n_ords)
        weights /= weights.sum()
        revs = np.round(weights * grp_rev).astype(int)
        revs[-1] = grp_rev - revs[:-1].sum()
        
        profit_weights = np.random.uniform(0.8, 1.2, n_ords)
        profit_weights /= profit_weights.sum()
        profits = np.round(profit_weights * grp_profit).astype(int)
        profits[-1] = grp_profit - profits[:-1].sum()
        
        for k in range(n_ords):
            day = np.random.randint(1, 31)
            date_str = f"2019-10-{day:02d}"
            r = int(revs[k])
            p = int(profits[k])
            c = r - p
            records.append({
                'Mã đơn hàng': f"DH-{order_id_counter:04d}",
                'Ngày đặt hàng': date_str,
                'Nhóm sản phẩm': grp,
                'Kênh bán hàng': np.random.choice(channels, p=[0.35, 0.25, 0.2, 0.1, 0.1]),
                'Doanh thu': r,
                'Chi phí': c,
                'Lợi nhuận HĐKD': p
            })
            order_id_counter += 1
            
    # Generate for other 11 months
    # Target remaining revenue
    remaining_rev = target_total_revenue - target_t10_revenue
    
    # We also want chuoi_monthly_millions for months 1..11
    # and T09 revenue to match t09_revenue
    monthly_targets = {}
    base_rem = (remaining_rev - t09_revenue) / 10
    for ym, _ in months[:-2]:
        monthly_targets[ym] = int(base_rem * np.random.uniform(0.95, 1.05))
    monthly_targets['2019-09'] = t09_revenue
    
    # Adjust remaining to equal exactly remaining_rev
    current_sum = sum(monthly_targets.values())
    adj = remaining_rev - current_sum
    monthly_targets['2018-11'] += adj
    
    for ym, label in months[:-1]:
        m_rev = monthly_targets[ym]
        n_ords = order_counts[ym]
        chuoi_target = chuoi_monthly_millions[ym] * 1_000_000
        
        # distribute orders: 20% to chuoi, 80% to others
        n_chuoi = max(5, int(n_ords * 0.2))
        n_other = n_ords - n_chuoi
        
        # chuoi orders
        w_c = np.random.uniform(0.7, 1.3, n_chuoi)
        w_c /= w_c.sum()
        revs_c = np.round(w_c * chuoi_target).astype(int)
        revs_c[-1] = chuoi_target - revs_c[:-1].sum()
        
        for k in range(n_chuoi):
            day = np.random.randint(1, 28)
            date_str = f"{ym}-{day:02d}"
            r = int(revs_c[k])
            ros = np.random.uniform(0.18, 0.25)
            p = int(r * ros)
            c = r - p
            records.append({
                'Mã đơn hàng': f"DH-{order_id_counter:04d}",
                'Ngày đặt hàng': date_str,
                'Nhóm sản phẩm': 'Nhóm chuối',
                'Kênh bán hàng': np.random.choice(channels),
                'Doanh thu': r,
                'Chi phí': c,
                'Lợi nhuận HĐKD': p
            })
            order_id_counter += 1
            
        # other groups
        other_rev = m_rev - chuoi_target
        w_o = np.random.uniform(0.7, 1.3, n_other)
        w_o /= w_o.sum()
        revs_o = np.round(w_o * other_rev).astype(int)
        revs_o[-1] = other_rev - revs_o[:-1].sum()
        
        other_grps = ['Nhóm khoai', 'Nhóm mít', 'Nhóm thơm', 'Nhóm xoài']
        for k in range(n_other):
            day = np.random.randint(1, 28)
            date_str = f"{ym}-{day:02d}"
            r = int(revs_o[k])
            ros = np.random.uniform(0.18, 0.26)
            p = int(r * ros)
            c = r - p
            grp = np.random.choice(other_grps)
            records.append({
                'Mã đơn hàng': f"DH-{order_id_counter:04d}",
                'Ngày đặt hàng': date_str,
                'Nhóm sản phẩm': grp,
                'Kênh bán hàng': np.random.choice(channels),
                'Doanh thu': r,
                'Chi phí': c,
                'Lợi nhuận HĐKD': p
            })
            order_id_counter += 1
            
    df = pd.DataFrame(records)
    # Check assertions
    total_rev = df['Doanh thu'].sum()
    diff_rev = target_total_revenue - total_rev
    if diff_rev != 0:
        # adjust first order of month 1
        df.loc[df['Ngày đặt hàng'].str.startswith('2018-11'), 'Doanh thu'].iloc[0] += diff_rev
        df.loc[df['Ngày đặt hàng'].str.startswith('2018-11'), 'Chi phí'].iloc[0] += diff_rev
        
    df = df.sort_values(by='Ngày đặt hàng').reset_index(drop=True)
    # Re-assign clean IDs
    df['Mã đơn hàng'] = [f"DH-{i+1:04d}" for i in range(len(df))]
    
    # Save CSV
    out_path = os.path.join('data', 'doanh_thu_marketing.csv')
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"Generated {out_path} with {len(df)} rows, total revenue: {df['Doanh thu'].sum():,}")

def generate_retail_logistics():
    np.random.seed(123)
    n_rows = 1500
    
    categories = ['Điện tử', 'Thời trang', 'Gia dụng', 'Mỹ phẩm', 'Mẹ & Bé']
    channels = ['Cửa hàng', 'Shopee', 'Lazada', 'TikTok Shop', 'Website']
    regions = ['Miền Bắc', 'Miền Trung', 'Miền Nam']
    statuses = ['Hoàn thành', 'Hoàn thành', 'Hoàn thành', 'Đang giao', 'Đã hủy']
    
    start_date = datetime(2023, 1, 1)
    
    records = []
    for i in range(n_rows):
        days_offset = np.random.randint(0, 365)
        dt = start_date + timedelta(days=days_offset)
        cat = np.random.choice(categories, p=[0.25, 0.3, 0.2, 0.15, 0.1])
        ch = np.random.choice(channels)
        reg = np.random.choice(regions, p=[0.4, 0.2, 0.4])
        qty = np.random.randint(1, 15)
        
        if cat == 'Điện tử':
            unit_price = np.random.choice([1500000, 3200000, 5800000, 12000000])
        elif cat == 'Thời trang':
            unit_price = np.random.choice([180000, 350000, 650000, 950000])
        elif cat == 'Gia dụng':
            unit_price = np.random.choice([250000, 500000, 1200000, 2400000])
        elif cat == 'Mỹ phẩm':
            unit_price = np.random.choice([320000, 580000, 890000, 1450000])
        else:
            unit_price = np.random.choice([220000, 450000, 780000, 1100000])
            
        revenue = int(qty * unit_price)
        ship_fee = int(np.random.choice([25000, 35000, 50000, 75000]))
        margin = np.random.uniform(0.15, 0.35)
        profit = int(revenue * margin - ship_fee * 0.3)
        cost = revenue - profit
        delivery_days = np.random.choice([1, 2, 3, 4, 5, 7], p=[0.1, 0.35, 0.3, 0.15, 0.08, 0.02])
        status = np.random.choice(statuses)
        
        records.append({
            'Ma_Van_Don': f"VD-{20230000 + i + 1}",
            'Ngay_Giao_Dich': dt.strftime('%Y-%m-%d'),
            'Nganh_Hang': cat,
            'Kenh_Phan_Phoi': ch,
            'Khu_Vuc': reg,
            'So_Luong': qty,
            'Don_Gia': unit_price,
            'Tong_Tien': revenue,
            'Phi_Van_Chuyen': ship_fee,
            'Chi_Phi_Von': cost,
            'Loi_Nhuan_Rong': profit,
            'Thoi_Gian_Giao_Hang_Ngay': delivery_days,
            'Trang_Thai': status
        })
        
    df = pd.DataFrame(records)
    # Add a few realistic dirty data points for Step 2 testing
    # Missing values
    df.loc[10:14, 'Phi_Van_Chuyen'] = np.nan
    # Whitespace inconsistency
    df.loc[20, 'Khu_Vuc'] = "  Miền Bắc  "
    df.loc[25, 'Khu_Vuc'] = "miền nam"
    # Duplicate rows
    df = pd.concat([df, df.iloc[[5, 8]]], ignore_index=True)
    
    out_path = os.path.join('data', 'ban_le_logistics.csv')
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"Generated {out_path} with {len(df)} rows, total revenue: {df['Tong_Tien'].sum():,}")

if __name__ == '__main__':
    generate_marketing_sales()
    generate_retail_logistics()
