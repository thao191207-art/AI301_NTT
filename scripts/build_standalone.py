import os
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Read CSS
with open(os.path.join(BASE_DIR, 'static', 'style.css'), 'r', encoding='utf-8') as f:
    css_content = f.read()

# Clean out any old flower hero rules from CSS
css_content = re.sub(r'/\* FLOWER HAPPY 3D PASTEL THEME \*/.*?(?=/\* App Shell \*/|/\* Sidebar \*/|$)', '', css_content, flags=re.DOTALL)
css_content = re.sub(r'\.flower-[^{]+\{[^}]+\}', '', css_content)
css_content = re.sub(r'\.floating-gem[^{]+\{[^}]+\}', '', css_content)
css_content = re.sub(r'\.bridge-[^{]+\{[^}]+\}', '', css_content)
css_content = re.sub(r'\.service-card[^{]+\{[^}]+\}', '', css_content)

# Add enhanced mobile phone responsiveness
mobile_css = """
/* Responsive adjustments for Tablets & Phones */
@media (max-width: 900px) {
  .app-container {
    flex-direction: column !important;
  }
  .sidebar {
    width: 100% !important;
    height: auto !important;
    position: static !important;
    border-right: none !important;
    border-bottom: 1px solid #1E293B !important;
  }
  .workflow-nav {
    flex-direction: row !important;
    overflow-x: auto !important;
    padding: 12px 16px !important;
    gap: 8px !important;
  }
  .step-nav-btn {
    padding: 8px 12px !important;
    flex-shrink: 0 !important;
  }
  .step-subtitle {
    display: none !important;
  }
  .dash-row-1, .dash-row-2 {
    grid-template-columns: 1fr !important;
  }
}

@media (max-width: 600px) {
  .page-body {
    padding: 14px 12px !important;
  }
  .top-bar {
    padding: 12px 14px !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 8px !important;
  }
  .summary-strip-container {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 8px !important;
  }
  .issues-header-bar {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
    font-size: 13px !important;
  }
  .data-table th, .data-table td, .issues-table th, .issues-table td {
    padding: 8px 10px !important;
    font-size: 11.5px !important;
  }
}
"""
css_content += "\n" + mobile_css

# 2. Read Vendor Scripts
with open(os.path.join(BASE_DIR, 'vendor', 'chart.umd.min.js'), 'r', encoding='utf-8') as f:
    chart_js = f.read()

with open(os.path.join(BASE_DIR, 'vendor', 'chartjs-plugin-datalabels.min.js'), 'r', encoding='utf-8') as f:
    datalabels_js = f.read()

with open(os.path.join(BASE_DIR, 'vendor', 'lucide.min.js'), 'r', encoding='utf-8') as f:
    lucide_js = f.read()

# 3. Read Sample Datasets
with open(os.path.join(BASE_DIR, 'doanh_thu_marketing.csv'), 'r', encoding='utf-8') as f:
    marketing_csv = f.read()

with open(os.path.join(BASE_DIR, 'ban_le_logistics.csv'), 'r', encoding='utf-8') as f:
    logistics_csv = f.read()

# 4. Read HTML and remove broken hero section
with open(os.path.join(BASE_DIR, 'static', 'index.html'), 'r', encoding='utf-8') as f:
    html_raw = f.read()

# Remove the flower-hero-section block completely
html_no_hero = re.sub(r'<!-- FLOWER HAPPY 3D PASTEL HERO SECTION -->\s*<div class="flower-hero-section">.*?</div>\s*<!-- Business Context Form -->', '<!-- Business Context Form -->', html_raw, flags=re.DOTALL)
if html_no_hero == html_raw:
    # Try alternate regex
    html_no_hero = re.sub(r'<div class="flower-hero-section">.*?</div>\s*(?=<div class="panel-card">)', '', html_raw, flags=re.DOTALL)

print("Removed hero section:", len(html_raw) - len(html_no_hero), "bytes removed")

# Remove external stylesheet and script references from head & body
html_clean = re.sub(r'<link rel="stylesheet" href="[^"]*">', '', html_no_hero)
html_clean = re.sub(r'<script src="[^"]*"></script>', '', html_clean)

# Read app.js
with open(os.path.join(BASE_DIR, 'static', 'app.js'), 'r', encoding='utf-8') as f:
    app_js = f.read()

# Prepare Embedded CSV JS variables
sample_data_injection = f"""
// Embedded sample datasets for instant zero-latency offline loading
window.EMBEDDED_MARKETING_CSV = {json.dumps(marketing_csv)};
window.EMBEDDED_LOGISTICS_CSV = {json.dumps(logistics_csv)};
"""

# Enhance app.js with client-side pure JS data processor
client_engine_js = """
// =========================================================================
// Pure Client-Side CSV Parser & Analytics Engine (Standalone Mode)
// =========================================================================

function parseCSVToRows(csvText) {
  if (!csvText) return { headers: [], rows: [] };
  // Strip UTF-8 BOM
  let text = csvText.charCodeAt(0) === 0xFEFF ? csvText.slice(1) : csvText;
  
  // Detect delimiter: check first line for comma, semicolon, tab, pipe
  let firstLine = text.split(/\\r?\\n/)[0] || '';
  let counts = {
    ',': (firstLine.match(/,/g) || []).length,
    ';': (firstLine.match(/;/g) || []).length,
    '\\t': (firstLine.match(/\\t/g) || []).length,
    '|': (firstLine.match(/\\|/g) || []).length
  };
  let delim = ',';
  let maxCount = 0;
  for (let [d, count] of Object.entries(counts)) {
    if (count > maxCount) {
      maxCount = count;
      delim = d;
    }
  }

  // Parse lines with quote handling
  let lines = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    let char = text[i];
    let nextChar = text[i + 1];
    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        cur += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if ((char === '\\n' || (char === '\\r' && nextChar === '\\n')) && !inQuotes) {
      if (char === '\\r') i++;
      lines.push(cur);
      cur = '';
    } else {
      cur += char;
    }
  }
  if (cur.trim().length > 0) lines.push(cur);

  if (lines.length === 0) return { headers: [], rows: [] };

  function parseRow(line) {
    let fields = [];
    let field = '';
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      let ch = line[i];
      let nch = line[i + 1];
      if (ch === '"') {
        if (inQ && nch === '"') {
          field += '"';
          i++;
        } else {
          inQ = !inQ;
        }
      } else if (ch === delim && !inQ) {
        fields.push(field.trim());
        field = '';
      } else {
        field += ch;
      }
    }
    fields.push(field.trim());
    return fields;
  }

  let rawHeaders = parseRow(lines[0]);
  let headers = rawHeaders.map((h, idx) => h.replace(/^["']|["']$/g, '').trim() || `Cot_${idx+1}`);
  let rows = [];

  for (let i = 1; i < lines.length; i++) {
    let l = lines[i].trim();
    if (!l) continue;
    let vals = parseRow(lines[i]);
    let rowObj = {};
    headers.forEach((h, idx) => {
      let v = vals[idx] !== undefined ? vals[idx].replace(/^["']|["']$/g, '').trim() : '';
      rowObj[h] = v;
    });
    rows.push(rowObj);
  }

  return { headers, rows, delimiter: delim };
}

function parseNumericValue(val) {
  if (val === null || val === undefined || val === '') return NaN;
  if (typeof val === 'number') return val;
  let s = String(val).trim();
  // Remove currency signs & spaces
  s = s.replace(/[đ₫$€£%\\s]/g, '');
  if (!s) return NaN;
  // If format is like 1.234.567 or 1.234.567,89 (European/Vietnamese)
  if (/^-?\\d{1,3}(\\.\\d{3})+(,\\d+)?$/.test(s)) {
    s = s.replace(/\\./g, '').replace(',', '.');
  } else if (/^-?\\d{1,3}(,\\d{3})+(\\.\\d+)?$/.test(s)) {
    s = s.replace(/,/g, '');
  } else if (/^-?\\d+,\\d+$/.test(s)) {
    s = s.replace(',', '.');
  }
  let num = parseFloat(s);
  return isNaN(num) ? NaN : num;
}

function formatVND(num, decimals = 0) {
  if (num === null || num === undefined || isNaN(num)) return "0 VND";
  let sign = num < 0 ? "-" : "";
  let abs = Math.abs(num);
  let parts = abs.toFixed(decimals).split('.');
  let intPart = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ".");
  let decPart = parts[1] ? "," + parts[1] : "";
  return `${sign}${intPart}${decPart} VND`;
}

function formatViNum(num, decimals = 0) {
  if (num === null || num === undefined || isNaN(num)) return "0";
  let sign = num < 0 ? "-" : "";
  let abs = Math.abs(num);
  let parts = abs.toFixed(decimals).split('.');
  let intPart = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ".");
  let decPart = parts[1] ? "," + parts[1] : "";
  return `${sign}${intPart}${decPart}`;
}

// Global Standalone Session Store
window.standaloneSession = {
  hasData: false,
  sourceName: '',
  headers: [],
  rows: [],
  cleanedRows: [],
  columnRoles: {},
  columnTypes: {},
  auditLog: [],
  issues: null,
  financialMetrics: null,
  dashboardData: null
};

// Client-side Semantic Role Detection
function detectRolesFromHeaders(headers, sampleRows) {
  let roles = {
    gross_revenue_col: '',
    net_revenue_col: '',
    revenue_col: '',
    profit_col: '',
    cogs_col: '',
    operating_cost_col: '',
    discount_col: '',
    return_col: '',
    tax_col: '',
    date_col: '',
    category_col: '',
    channel_col: '',
    order_col: '',
    quantity_col: ''
  };

  let assigned = new Set();

  function findCol(keywords, mustBeNumeric = false) {
    for (let col of headers) {
      if (assigned.has(col)) continue;
      let clow = col.toLowerCase().trim();
      let match = keywords.some(k => clow.includes(k.toLowerCase()));
      if (match) {
        if (mustBeNumeric && sampleRows.length > 0) {
          let numCount = sampleRows.filter(r => !isNaN(parseNumericValue(r[col]))).length;
          if (numCount < sampleRows.length * 0.4) continue;
        }
        assigned.add(col);
        return col;
      }
    }
    return '';
  }

  roles.date_col = findCol(['ngày đặt hàng', 'ngay_dat_hang', 'ngay_giao_dich', 'ngày', 'date', 'thời gian', 'time']);
  roles.order_col = findCol(['mã đơn hàng', 'ma_don_hang', 'mã vận đơn', 'ma_van_don', 'mã đơn', 'order_id', 'order']);
  roles.category_col = findCol(['nhóm sản phẩm', 'nhom_san_pham', 'ngành hàng', 'nganh_hang', 'danh mục', 'category', 'loại']);
  roles.channel_col = findCol(['kênh bán hàng', 'kenh_ban_hang', 'kênh', 'channel', 'khu vực', 'vùng']);
  roles.quantity_col = findCol(['số lượng', 'so_luong', 'quantity', 'qty', 'sản lượng'], true);
  roles.discount_col = findCol(['chiết khấu', 'chiet_khau', 'giảm giá', 'giam_gia', 'discount'], true);
  roles.return_col = findCol(['hàng trả lại', 'hang_tra_lai', 'hoàn tiền', 'refund', 'return'], true);
  roles.tax_col = findCol(['thuế', 'thue', 'vat', 'tax'], true);
  roles.cogs_col = findCol(['giá vốn', 'gia_von', 'cogs', 'chi phí vốn', 'cost of goods'], true);
  roles.operating_cost_col = findCol(['chi phí bán hàng', 'chi phí quản lý', 'chi phí', 'chi_phi', 'operating cost'], true);
  roles.profit_col = findCol(['lợi nhuận hđkd', 'lợi nhuận ròng', 'lợi nhuận', 'loi_nhuan', 'profit', 'lãi'], true);
  roles.net_revenue_col = findCol(['doanh thu thuần', 'doanh_thu_thuan', 'net revenue', 'thành tiền'], true);
  roles.gross_revenue_col = findCol(['doanh thu', 'doanh_thu', 'tong_tien', 'tổng tiền', 'gross revenue', 'revenue', 'tiền hàng'], true);

  if (!roles.net_revenue_col) roles.net_revenue_col = roles.gross_revenue_col;
  if (!roles.gross_revenue_col) roles.gross_revenue_col = roles.net_revenue_col;
  roles.revenue_col = roles.net_revenue_col;

  return roles;
}
"""

# Assemble Standalone HTML
standalone_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Không gian phân tích — Analysis Workspace</title>
  
  <!-- Inlined Stylesheets -->
  <style>
{css_content}
  </style>

  <!-- Inlined Chart.js, Plugins & Lucide Icons -->
  <script>
{chart_js}
  </script>
  <script>
{datalabels_js}
  </script>
  <script>
{lucide_js}
  </script>
</head>
<body>
{html_clean[html_clean.find('<body>') + 6 : html_clean.find('</body>')]}

  <!-- Inlined Application Logic & Standalone Engine -->
  <script>
{sample_data_injection}
{client_engine_js}
{app_js}
  </script>
</body>
</html>
"""

# Write to destination files
outputs = [
    os.path.join(BASE_DIR, 'dist', 'index.html'),
    os.path.join(BASE_DIR, 'index.html'),
    os.path.join(BASE_DIR, 'static', 'index.html'),
    os.path.join(BASE_DIR, 'public', 'static', 'index.html')
]

for out_path in outputs:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(standalone_html)
    print(f"Wrote {out_path} ({len(standalone_html)} bytes)")

# Update vercel.json for clean static deployment
vercel_config = {
    "cleanUrls": True,
    "outputDirectory": "."
}
with open(os.path.join(BASE_DIR, 'vercel.json'), 'w', encoding='utf-8') as f:
    json.dump(vercel_config, f, indent=2)
print("Updated vercel.json to static outputDirectory: '.'")
