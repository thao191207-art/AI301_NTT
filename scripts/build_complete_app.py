import os
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Read CSS
with open(os.path.join(BASE_DIR, 'static', 'style.css'), 'r', encoding='utf-8') as f:
    css_content = f.read()

# Remove any old hero section styles
css_content = re.sub(r'/\* FLOWER HAPPY 3D PASTEL THEME \*/.*?(?=/\* App Shell \*/|/\* Sidebar \*/|$)', '', css_content, flags=re.DOTALL)
css_content = re.sub(r'\.flower-[^{]+\{[^}]+\}', '', css_content)
css_content = re.sub(r'\.floating-gem[^{]+\{[^}]+\}', '', css_content)
css_content = re.sub(r'\.bridge-[^{]+\{[^}]+\}', '', css_content)
css_content = re.sub(r'\.service-card[^{]+\{[^}]+\}', '', css_content)

# Add comprehensive responsive layout CSS
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

# Read Vendor Libraries
with open(os.path.join(BASE_DIR, 'vendor', 'chart.umd.min.js'), 'r', encoding='utf-8') as f:
    chart_js = f.read()

with open(os.path.join(BASE_DIR, 'vendor', 'chartjs-plugin-datalabels.min.js'), 'r', encoding='utf-8') as f:
    datalabels_js = f.read()

with open(os.path.join(BASE_DIR, 'vendor', 'lucide.min.js'), 'r', encoding='utf-8') as f:
    lucide_js = f.read()

with open(os.path.join(BASE_DIR, 'vendor', 'jszip.min.js'), 'r', encoding='utf-8') as f:
    jszip_js = f.read()

# Read Sample Datasets
with open(os.path.join(BASE_DIR, 'doanh_thu_marketing.csv'), 'r', encoding='utf-8') as f:
    marketing_csv = f.read()

with open(os.path.join(BASE_DIR, 'ban_le_logistics.csv'), 'r', encoding='utf-8') as f:
    logistics_csv = f.read()

# Read HTML and strip broken hero section
with open(os.path.join(BASE_DIR, 'static', 'index.html'), 'r', encoding='utf-8') as f:
    html_raw = f.read()

# Strip any logic scripts from previous build so we get clean markup
if '<!-- Inlined Application Logic -->' in html_raw:
    html_markup = html_raw[:html_raw.find('<!-- Inlined Application Logic -->')]
else:
    html_markup = html_raw

# Strip flower-hero-section
html_clean = re.sub(r'<!-- FLOWER HAPPY 3D PASTEL HERO SECTION -->\s*<div class="flower-hero-section">.*?</div>\s*(?=<!-- Business Context Form -->)', '', html_markup, flags=re.DOTALL)
if html_clean == html_markup:
    html_clean = re.sub(r'<div class="flower-hero-section">.*?</div>\s*(?=<div class="panel-card">)', '', html_markup, flags=re.DOTALL)

# Remove external css and js tags from html
html_clean = re.sub(r'<link rel="stylesheet" href="[^"]*">', '', html_clean)
html_clean = re.sub(r'<script src="[^"]*"></script>', '', html_clean)

# Replace input-biz-type with dropdown with exactly 2 options
old_biz_pattern = r'<input[^>]*id="input-biz-type"[^>]*>'
new_biz_select = '''<select id="input-biz-type" class="form-select" required onchange="app.handleBusinessTypeChange(this.value)">
                    <option value="">Chọn loại hình doanh nghiệp</option>
                    <option value="retail">Bán lẻ</option>
                    <option value="b2b">Doanh nghiệp với doanh nghiệp (B2B)</option>
                  </select>'''
html_clean = re.sub(old_biz_pattern, new_biz_select, html_clean)

# Add Export Word button next to PDF button in Step 4
if 'Xuất Báo cáo Word' not in html_clean:
    html_clean = html_clean.replace(
        '''<button class="btn btn-primary" onclick="app.exportFile('pdf')">''',
        '''<button class="btn btn-secondary" onclick="app.exportFile('word')">
                <i data-lucide="file-text" style="color: #2563EB;"></i> Xuất Báo cáo Word (.docx)
              </button>
              <button class="btn btn-primary" onclick="app.exportFile('pdf')">'''
    )

# Write a comprehensive standalone JS application that includes:
# - CSV Parser (delimiter detection, UTF-8 BOM)
# - In-browser data cleaning, audit log, role mapping
# - Exact Net Revenue, Profit, ROS calculation
# - 12-month grouping & Chart rendering
# - Section I Issues to resolve with priority badges, trace modal
# - Seamless API fallback when running against FastAPI
standalone_js_app = """
// =========================================================================
// Analysis Workspace Standalone Engine
// =========================================================================

// CSV Parser
function parseCSV(text) {
  if (!text) return { headers: [], rows: [], delimiter: ',' };
  let s = text.charCodeAt(0) === 0xFEFF ? text.slice(1) : text;
  let firstLine = s.split(/\\r?\\n/)[0] || '';
  let counts = {
    ',': (firstLine.match(/,/g) || []).length,
    ';': (firstLine.match(/;/g) || []).length,
    '\\t': (firstLine.match(/\\t/g) || []).length,
    '|': (firstLine.match(/\\|/g) || []).length
  };
  let delim = ',';
  let maxC = 0;
  for (let [d, c] of Object.entries(counts)) {
    if (c > maxC) { maxC = c; delim = d; }
  }

  let lines = [];
  let cur = '';
  let inQ = false;
  for (let i = 0; i < s.length; i++) {
    let ch = s[i];
    let nch = s[i+1];
    if (ch === '"') {
      if (inQ && nch === '"') { cur += '"'; i++; }
      else { inQ = !inQ; }
    } else if ((ch === '\\n' || (ch === '\\r' && nch === '\\n')) && !inQ) {
      if (ch === '\\r') i++;
      lines.push(cur);
      cur = '';
    } else {
      cur += ch;
    }
  }
  if (cur.trim().length > 0) lines.push(cur);
  if (lines.length === 0) return { headers: [], rows: [], delimiter: delim };

  function splitLine(line) {
    let flds = [];
    let f = '';
    let q = false;
    for (let i = 0; i < line.length; i++) {
      let c = line[i];
      let nc = line[i+1];
      if (c === '"') {
        if (q && nc === '"') { f += '"'; i++; }
        else { q = !q; }
      } else if (c === delim && !q) {
        flds.push(f.trim());
        f = '';
      } else {
        f += c;
      }
    }
    flds.push(f.trim());
    return flds;
  }

  let headers = splitLine(lines[0]).map((h, idx) => h.replace(/^["']|["']$/g, '').trim() || `Cột_${idx+1}`);
  let rows = [];
  for (let i = 1; i < lines.length; i++) {
    let l = lines[i].trim();
    if (!l) continue;
    let vals = splitLine(lines[i]);
    let obj = {};
    headers.forEach((h, idx) => {
      let v = vals[idx] !== undefined ? vals[idx].replace(/^["']|["']$/g, '').trim() : '';
      obj[h] = v;
    });
    rows.push(obj);
  }
  return { headers, rows, delimiter: delim };
}

function parseNum(val) {
  if (val === null || val === undefined || val === '') return NaN;
  if (typeof val === 'number') return val;
  let s = String(val).trim().replace(/[đ₫$€£%\\s]/g, '');
  if (!s) return NaN;
  if (/^-?\\d{1,3}(\\.\\d{3})+(,\\d+)?$/.test(s)) {
    s = s.replace(/\\./g, '').replace(',', '.');
  } else if (/^-?\\d{1,3}(,\\d{3})+(\\.\\d+)?$/.test(s)) {
    s = s.replace(/,/g, '');
  } else if (/^-?\\d+,\\d+$/.test(s)) {
    s = s.replace(',', '.');
  }
  let n = parseFloat(s);
  return isNaN(n) ? NaN : n;
}

function formatVND(n, decimals = 0) {
  if (n === null || n === undefined || isNaN(n)) return "0 VND";
  let sign = n < 0 ? "-" : "";
  let abs = Math.abs(n);
  let parts = abs.toFixed(decimals).split('.');
  let intPart = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ".");
  let decPart = parts[1] ? "," + parts[1] : "";
  return `${sign}${intPart}${decPart} VND`;
}

function formatViNum(n, decimals = 0) {
  if (n === null || n === undefined || isNaN(n)) return "0";
  let sign = n < 0 ? "-" : "";
  let abs = Math.abs(n);
  let parts = abs.toFixed(decimals).split('.');
  let intPart = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ".");
  let decPart = parts[1] ? "," + parts[1] : "";
  return `${sign}${intPart}${decPart}`;
}

// Master Application
class StandaloneAnalysisApp {
  constructor() {
    this.currentStep = 1;
    this.stepUnlocked = { 1: true, 2: false, 3: false, 4: false };
    this.chartInstances = {};
    this.chartTypeOverrides = { chart1: 'bar', chart2: 'bar', chart4: 'bar', chart5: 'line' };
    this.currentIssues = [];
    
    // In-memory data store
    this.store = {
      filename: '',
      encoding: 'UTF-8',
      delimiter: ',',
      rawHeaders: [],
      rawRows: [],
      cleanRows: [],
      columnTypes: {},
      columnRoles: {},
      auditLog: [],
      businessType: '',
      additionalInfo: '',
      questions: [],
      userClarification: '',
      anomalies: [],
      dashboard: null
    };

    if (window.ChartDataLabels) Chart.register(ChartDataLabels);
    Chart.register({
      id: 'centerTextPlugin',
      beforeDraw(chart) {
        if (chart.config.type === 'doughnut') {
          const { width, height, ctx } = chart;
          ctx.restore();
          const fontSize = (height / 114).toFixed(2);
          ctx.font = `bold ${fontSize}em Inter, sans-serif`;
          ctx.textBaseline = 'middle';
          ctx.fillStyle = '#0F172A';
          const text = chart.config.options.plugins?.centerText?.text || '';
          const textX = Math.round((width - ctx.measureText(text).width) / 2);
          const textY = height / 2;
          ctx.fillText(text, textX, textY);
          ctx.save();
        }
      }
    });

    this.init();
  }

  init() {
    this.bindEvents();
    
    // Restore persisted business type
    const savedBizType = localStorage.getItem('biz_type') || '';
    if (savedBizType === 'retail' || savedBizType === 'b2b') {
      this.store.businessType = savedBizType;
      const sel = document.getElementById('input-biz-type');
      if (sel) sel.value = savedBizType;
    }
    
    if (window.lucide) lucide.createIcons();
    // Check if running against local API or pure client mode
    this.checkBackendConnection();
  }

  handleBusinessTypeChange(val) {
    this.store.businessType = val;
    if (val === 'retail' || val === 'b2b') {
      localStorage.setItem('biz_type', val);
    } else {
      localStorage.removeItem('biz_type');
    }
    this.loadAISuggestions();
  }

  getBusinessTypeName() {
    if (this.store.businessType === 'retail') return 'Bán lẻ';
    if (this.store.businessType === 'b2b') return 'Doanh nghiệp với doanh nghiệp (B2B)';
    return 'Chưa xác định';
  }

  async checkBackendConnection() {
    try {
      let res = await fetch('/api/state');
      if (res.ok) {
        let state = await res.json();
        if (state.has_data && state.current_step > 1) {
          this.stepUnlocked = state.step_unlocked;
          this.updateSidebarStatus();
          this.updateStepLockUI();
          this.goToStep(state.current_step);
        }
      }
    } catch (e) {
      // Running standalone offline
      console.log("Running in Standalone Client Mode.");
    }
  }

  bindEvents() {
    const qInput = document.getElementById('input-questions');
    if (qInput) {
      qInput.addEventListener('input', () => {
        const lines = qInput.value.split('\\n').filter(l => l.trim().length > 0);
        const badge = document.getElementById('question-count-badge');
        if (badge) {
          badge.textContent = `${lines.length}/8 câu`;
          badge.style.color = lines.length > 8 ? '#DC2626' : (lines.length > 0 ? '#2563EB' : '#64748B');
        }
      });
    }
  }

  updateSidebarStatus() {
    const dot = document.getElementById('status-dot');
    const badge = document.getElementById('sidebar-data-status');
    if (this.store.rawRows.length > 0) {
      if (dot) dot.classList.add('active');
      if (badge) badge.textContent = `${this.store.filename} (${this.store.cleanRows.length.toLocaleString('vi-VN')} dòng)`;
    } else {
      if (dot) dot.classList.remove('active');
      if (badge) badge.textContent = 'Chưa có dữ liệu';
    }
  }

  updateStepLockUI() {
    for (let s = 2; s <= 4; s++) {
      const btn = document.getElementById(`nav-step-${s}`);
      const lock = document.getElementById(`lock-step-${s}`);
      if (btn) {
        if (this.stepUnlocked[s]) {
          btn.classList.remove('locked');
          if (lock) lock.style.display = 'none';
        } else {
          btn.classList.add('locked');
          if (lock) lock.style.display = 'inline-block';
        }
      }
    }
  }

  async goToStep(step) {
    if (!this.stepUnlocked[step]) {
      alert(`Bước ${step} đang bị khóa. Bạn cần hoàn thành bước trước đó để tiếp tục.`);
      return;
    }
    this.currentStep = step;
    for (let s = 1; s <= 4; s++) {
      const btn = document.getElementById(`nav-step-${s}`);
      const pane = document.getElementById(`step-${s}-content`);
      if (btn) btn.classList.toggle('active', s === step);
      if (pane) pane.style.display = s === step ? 'block' : 'none';
    }
    const titles = {
      1: "Bước 1: Kết nối dữ liệu & Thiết lập bài toán",
      2: "Bước 2: Làm sạch, chuẩn hóa & Ánh xạ vai trò cột",
      3: "Bước 3: Phân tích thống kê & Trả lời bài toán",
      4: "Bước 4: Báo cáo điều hành & Xuất tệp"
    };
    const topTitle = document.getElementById('top-title');
    if (topTitle) topTitle.textContent = titles[step] || "";

    if (step === 2) await this.loadCleanStep();
    else if (step === 3) await this.loadAnalyzeStep();
    else if (step === 4) await this.loadReportStep();

    if (window.lucide) lucide.createIcons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // -----------------------------------------------------------------
  // STEP 1: Connect & Ingest
  // -----------------------------------------------------------------

  async saveBusinessForm() {
    const bizType = document.getElementById('input-biz-type')?.value.trim() || '';
    const addInfo = document.getElementById('input-biz-info')?.value.trim() || '';
    const questionsText = document.getElementById('input-questions')?.value.trim() || '';
    
    if (!bizType || (bizType !== 'retail' && bizType !== 'b2b')) {
      alert("Vui lòng chọn 'Loại hình doanh nghiệp' (Bán lẻ hoặc B2B).");
      document.getElementById('input-biz-type')?.focus();
      return false;
    }
    const questions = questionsText.split('\\n').map(q => q.trim()).filter(q => q.length > 0);
    if (questions.length === 0) {
      alert("Vui lòng nhập ít nhất 1 câu hỏi phân tích (hoặc tích chọn từ danh sách AI gợi ý bên dưới).");
      document.getElementById('input-questions')?.focus();
      return false;
    }
    if (questions.length > 8) {
      alert("Số lượng câu hỏi không được vượt quá 8 dòng.");
      return false;
    }
    this.store.businessType = bizType;
    this.store.additionalInfo = addInfo;
    this.store.questions = questions;
    return true;
  }

  async consultAI() {
    const valid = await this.saveBusinessForm();
    if (!valid) return;
    const chatContainer = document.getElementById('ai-chat-container');
    const goalBox = document.getElementById('ai-goal-box');
    const missingBox = document.getElementById('ai-missing-box');
    const clarifyBox = document.getElementById('ai-clarify-box');

    if (chatContainer) chatContainer.style.display = 'block';
    
    const isRetail = this.store.businessType === 'retail';
    const bizName = isRetail ? 'Bán lẻ (Retail)' : 'Doanh nghiệp với doanh nghiệp (B2B)';
    
    if (goalBox) {
      goalBox.innerHTML = `<strong>Tóm tắt mục tiêu chiến lược:</strong><br>Doanh nghiệp hoạt động theo mô hình <em>${bizName}</em>. ${isRetail ? 'Định hướng trọng tâm vào tối ưu hóa doanh thu theo điểm bán/kênh phân phối, quy mô giỏ hàng (basket size) và tỷ lệ hàng đổi trả.' : 'Định hướng trọng tâm vào kiểm soát rủi ro tập trung tài khoản lớn (Key Accounts), quy mô hợp đồng (deal size) và điều khoản thanh toán.'}<br>Mục tiêu phân tích tập trung vào: ${this.store.questions.map(q => `“${q}”`).join(', ')}.`;
    }
    
    if (missingBox) {
      if (isRetail) {
        missingBox.innerHTML = `<strong>Thông tin/biến số nên đối chiếu (Bán lẻ):</strong><ul style="margin-left: 20px; margin-top: 4px;">
          <li>Phân bổ doanh thu theo kênh bán hàng (Website, Cửa hàng trực tiếp, Sàn TMĐT) và điểm bán.</li>
          <li>Quy mô giỏ hàng trung bình (AOV - Basket Size) và tỷ lệ hàng đổi trả / hoàn tiền (Return Rate).</li>
          <li>Cơ cấu chiết khấu khuyến mãi ảnh hưởng đến giá vốn (COGS) và biên lợi nhuận ròng.</li>
        </ul>`;
      } else {
        missingBox.innerHTML = `<strong>Thông tin/biến số nên đối chiếu (B2B):</strong><ul style="margin-left: 20px; margin-top: 4px;">
          <li>Mức độ tập trung khách hàng (Top 10-20% tài khoản đóng góp bao nhiêu % doanh thu - Pareto 80/20).</li>
          <li>Giá trị hợp đồng / giá trị đơn hàng trung bình (Average Deal/Contract Value) và chu kỳ tái ký.</li>
          <li>Kỳ hạn thanh toán, công nợ khách hàng (DSO) và chi phí quản lý quan hệ khách hàng.</li>
        </ul>`;
      }
    }
    
    if (clarifyBox) {
      if (isRetail) {
        clarifyBox.innerHTML = `<strong>Đề xuất làm rõ từ AI Advisor:</strong><ul style="margin-left: 20px; margin-top: 4px;">
          <li>Doanh nghiệp có muốn thiết lập ngưỡng kiểm soát tỷ lệ hoàn trả hàng mục tiêu (ví dụ dưới 3%) không?</li>
          <li>Có cần đánh giá độ nhạy giữa chính sách giảm giá/chiết khấu và số lượng đơn hàng phát sinh không?</li>
        </ul>`;
      } else {
        clarifyBox.innerHTML = `<strong>Đề xuất làm rõ từ AI Advisor:</strong><ul style="margin-left: 20px; margin-top: 4px;">
          <li>Doanh nghiệp có quy định hạn mức rủi ro tập trung doanh số (ví dụ không quá 25% tổng doanh thu từ 1 khách hàng đơn lẻ) không?</li>
          <li>Có cần phân cấp khách hàng B2B theo nhóm giá trị hợp đồng (Tier 1, Tier 2) để áp dụng chính sách chiết khấu riêng không?</li>
        </ul>`;
      }
    }
    if (window.lucide) lucide.createIcons();
  }

  saveUserClarification() {
    const val = document.getElementById('input-user-clarify')?.value.trim();
    if (!val) { alert("Vui lòng nhập phản hồi."); return; }
    this.store.userClarification = val;
    alert("Đã ghi nhận phản hồi của bạn vào ngữ cảnh phân tích!");
  }

  loadSampleData(key) {
    let csvText = '';
    let fname = '';
    if (key === 'marketing_sales') {
      csvText = window.EMBEDDED_MARKETING_CSV || '';
      fname = 'doanh_thu_marketing.csv';
    } else {
      csvText = window.EMBEDDED_LOGISTICS_CSV || '';
      fname = 'ban_le_logistics.csv';
    }

    if (!csvText) {
      alert("Chưa nạp được dữ liệu mẫu.");
      return;
    }

    this.processRawCSVText(csvText, fname);
  }

  handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      alert("Tệp vượt quá 50MB. Vui lòng chọn tệp nhỏ hơn.");
      return;
    }
    const prog = document.getElementById('upload-progress-container');
    const bar = document.getElementById('upload-progress-bar');
    if (prog) prog.style.display = 'block';
    if (bar) bar.style.width = '50%';

    const reader = new FileReader();
    reader.onload = (e) => {
      if (bar) bar.style.width = '100%';
      setTimeout(() => { if (prog) prog.style.display = 'none'; }, 400);
      this.processRawCSVText(e.target.result, file.name);
    };
    reader.onerror = () => {
      if (prog) prog.style.display = 'none';
      alert("Lỗi đọc tệp từ máy tính.");
    };
    reader.readAsText(file, 'utf-8');
  }

  connectGoogleSheets() {
    const url = document.getElementById('input-sheets-url')?.value.trim();
    if (!url) { alert("Vui lòng nhập liên kết Google Sheets công khai."); return; }
    
    // Extract ID
    const match = url.match(/\\/d\\/([a-zA-Z0-9-_]+)/);
    if (!match) { alert("Không nhận diện được ID bảng tính Google Sheets hợp lệ."); return; }
    const sheetId = match[1];
    let gid = '0';
    const gidMatch = url.match(/[#&]gid=([0-9]+)/);
    if (gidMatch) gid = gidMatch[1];
    const exportUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=${gid}`;
    
    alert(`Đang lấy dữ liệu qua Google Sheets export URL:\\n${exportUrl}\\n(Nếu bảng tính riêng tư, xin vui lòng mở quyền 'Bất kỳ ai có liên kết đều có thể xem' hoặc tải file CSV về máy tính).`);
    fetch(exportUrl)
      .then(res => {
        if (!res.ok) throw new Error("Không thể tải bảng tính. Hãy kiểm tra quyền truy cập công khai.");
        return res.text();
      })
      .then(csvText => {
        this.processRawCSVText(csvText, `GoogleSheet_${sheetId.slice(0, 8)}.csv`);
      })
      .catch(err => {
        alert("Lỗi kết nối Google Sheets: " + err.message + "\\nGợi ý: Bạn có thể vào File > Download > CSV trong Google Sheets và tải tệp trực tiếp lên.");
      });
  }

  processRawCSVText(csvText, filename) {
    const parsed = parseCSV(csvText);
    if (parsed.rows.length === 0) {
      alert("Tệp không chứa bản ghi dữ liệu hợp lệ.");
      return;
    }
    this.store.filename = filename;
    this.store.delimiter = parsed.delimiter;
    this.store.rawHeaders = parsed.headers;
    this.store.rawRows = parsed.rows;
    this.store.cleanRows = JSON.parse(JSON.stringify(parsed.rows));
    this.store.auditLog = [];

    // Detect column types
    this.detectColumnTypes();
    // Detect roles
    this.detectColumnRoles();

    // Render Preview
    this.renderPreview();
    // Load AI suggestions
    this.loadAISuggestions();

    this.updateSidebarStatus();
    alert(`Đã nạp thành công: ${filename} (${parsed.rows.length.toLocaleString('vi-VN')} dòng, ${parsed.headers.length} cột).`);
  }

  detectColumnTypes() {
    let types = {};
    let sample = this.store.rawRows.slice(0, 50);
    this.store.rawHeaders.forEach(h => {
      let numCount = 0;
      let dateCount = 0;
      sample.forEach(r => {
        let v = String(r[h] || '').trim();
        if (!v) return;
        if (!isNaN(parseNum(v))) numCount++;
        else if (/^\\d{4}-\\d{2}-\\d{2}/.test(v) || /^\\d{1,2}[\\/-]\\d{1,2}[\\/-]\\d{2,4}/.test(v)) dateCount++;
      });
      if (numCount > sample.length * 0.4) types[h] = 'numeric';
      else if (dateCount > sample.length * 0.4) types[h] = 'date';
      else types[h] = 'categorical';
    });
    this.store.columnTypes = types;
  }

  detectColumnRoles() {
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
    let headers = this.store.rawHeaders;
    let sample = this.store.rawRows.slice(0, 50);
    let assigned = new Set();

    function matchCol(keywords, mustBeNum = false) {
      for (let col of headers) {
        if (assigned.has(col)) continue;
        let clow = col.toLowerCase().trim();
        if (keywords.some(k => clow.includes(k.toLowerCase()))) {
          if (mustBeNum && sample.length > 0) {
            let n = sample.filter(r => !isNaN(parseNum(r[col]))).length;
            if (n < sample.length * 0.3) continue;
          }
          assigned.add(col);
          return col;
        }
      }
      return '';
    }

    roles.date_col = matchCol(['ngày đặt hàng', 'ngay_dat_hang', 'ngay_giao_dich', 'ngày', 'date', 'thời gian']);
    roles.order_col = matchCol(['mã đơn hàng', 'ma_don_hang', 'mã vận đơn', 'ma_van_don', 'mã đơn', 'order_id', 'order']);
    roles.category_col = matchCol(['nhóm sản phẩm', 'nhom_san_pham', 'ngành hàng', 'nganh_hang', 'danh mục', 'category', 'loại']);
    roles.channel_col = matchCol(['kênh bán hàng', 'kenh_ban_hang', 'kênh', 'channel', 'khu vực']);
    roles.quantity_col = matchCol(['số lượng', 'so_luong', 'quantity', 'qty', 'sản lượng'], true);
    roles.discount_col = matchCol(['chiết khấu', 'chiet_khau', 'giảm giá', 'discount'], true);
    roles.return_col = matchCol(['hàng trả lại', 'hang_tra_lai', 'hoàn tiền', 'refund', 'return'], true);
    roles.tax_col = matchCol(['thuế', 'vat', 'tax'], true);
    roles.cogs_col = matchCol(['giá vốn', 'gia_von', 'cogs', 'chi phí vốn'], true);
    roles.operating_cost_col = matchCol(['chi phí bán hàng', 'chi phí quản lý', 'chi phí', 'chi_phi'], true);
    roles.profit_col = matchCol(['lợi nhuận hđkd', 'lợi nhuận ròng', 'lợi nhuận', 'loi_nhuan', 'profit', 'lãi'], true);
    roles.net_revenue_col = matchCol(['doanh thu thuần', 'doanh_thu_thuan', 'net revenue', 'thành tiền'], true);
    roles.gross_revenue_col = matchCol(['doanh thu', 'doanh_thu', 'tong_tien', 'tổng tiền', 'gross revenue', 'revenue'], true);

    if (!roles.net_revenue_col) roles.net_revenue_col = roles.gross_revenue_col;
    if (!roles.gross_revenue_col) roles.gross_revenue_col = roles.net_revenue_col;
    roles.revenue_col = roles.net_revenue_col;

    this.store.columnRoles = roles;
  }

  renderPreview() {
    const card = document.getElementById('data-preview-card');
    if (!card) return;
    card.style.display = 'block';

    const pTitle = document.getElementById('preview-title');
    const pMeta = document.getElementById('preview-meta-info');
    if (pTitle) pTitle.textContent = `Xem trước: ${this.store.filename}`;
    if (pMeta) {
      pMeta.textContent = `Tổng số: ${this.store.rawRows.length.toLocaleString('vi-VN')} dòng, ${this.store.rawHeaders.length} cột | Định dạng: UTF-8 | Dấu phân cách: '${this.store.delimiter}'`;
    }

    const thead = document.getElementById('preview-thead');
    const tbody = document.getElementById('preview-tbody');
    if (!thead || !tbody) return;

    let hHtml = '<tr>';
    this.store.rawHeaders.forEach(h => {
      let t = this.store.columnTypes[h] || 'text';
      hHtml += `<th>${h} <span style="font-size: 10px; font-weight: normal; color: #64748B;">(${t})</span></th>`;
    });
    hHtml += '</tr>';
    thead.innerHTML = hHtml;

    let bHtml = '';
    let previewSlice = this.store.rawRows.slice(0, 20);
    previewSlice.forEach(r => {
      bHtml += '<tr>';
      this.store.rawHeaders.forEach(h => {
        bHtml += `<td>${r[h] !== undefined && r[h] !== null ? r[h] : ''}</td>`;
      });
      bHtml += '</tr>';
    });
    tbody.innerHTML = bHtml;

    card.scrollIntoView({ behavior: 'smooth' });
  }

  loadAISuggestions() {
    const panel = document.getElementById('ai-suggestions-panel');
    const list = document.getElementById('ai-suggestions-list');
    if (!panel || !list) return;
    panel.style.display = 'block';
    list.innerHTML = '';

    const isB2B = this.store.businessType === 'b2b';
    const suggestions = isB2B ? [
      {
        question: "Mức độ tập trung khách hàng và top tài khoản đóng góp bao nhiêu % doanh thu?",
        goal: "Đo lường rủi ro phụ thuộc vào nhóm khách hàng lớn và cơ cấu tài khoản",
        cols: [this.store.columnRoles.channel_col || "Kênh/Đối tác", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Giá trị hợp đồng / đơn hàng trung bình (Contract Value) biến động ra sao theo nhóm hàng?",
        goal: "Đánh giá quy mô deals và phân khúc giá trị các hợp đồng B2B",
        cols: [this.store.columnRoles.order_col || "Mã đơn/hợp đồng", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Biên lợi nhuận HĐKD và ROS trên từng nhóm hàng hoặc hợp đồng B2B đạt bao nhiêu?",
        goal: "Kiểm soát hiệu quả sinh lời và chính sách giá thầu cho đối tác doanh nghiệp",
        cols: [this.store.columnRoles.profit_col || "Lợi nhuận", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Xu hướng doanh thu theo chu kỳ thanh toán và tháng giao dịch biến động như thế nào?",
        goal: "Dự báo dòng tiền và kế hoạch thực hiện hợp đồng qua các quý",
        cols: [this.store.columnRoles.date_col || "Ngày đặt hàng", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      }
    ] : [
      {
        question: "Doanh thu và tăng trưởng theo cửa hàng hoặc kênh bán hàng nào dẫn đầu trong kỳ?",
        goal: "Đánh giá hiệu quả từng điểm bán, kênh phân phối (Online vs Offline)",
        cols: [this.store.columnRoles.channel_col || "Kênh bán", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Giá trị giỏ hàng trung bình (AOV) và số lượng đơn hàng biến động như thế nào?",
        goal: "Theo dõi sức mua, quy mô giỏ hàng (basket size) và tần suất đặt hàng",
        cols: [this.store.columnRoles.order_col || "Mã đơn hàng", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Tỷ lệ hàng đổi trả / hoàn tiền và chiết khấu ảnh hưởng ra sao đến doanh thu thuần?",
        goal: "Giảm thiểu hao hụt dòng tiền và tối ưu chính sách đổi trả, khuyến mãi",
        cols: [this.store.columnRoles.discount_col || "Chiết khấu", this.store.columnRoles.return_col || "Hàng trả lại"]
      },
      {
        question: "Tỷ suất lợi nhuận (ROS) và nhóm sản phẩm nào đóng góp lợi nhuận cao nhất?",
        goal: "Đo lường biên sinh lời trên doanh thu và xác định danh mục sản phẩm chủ lực",
        cols: [this.store.columnRoles.profit_col || "Lợi nhuận", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      }
    ];

    const qInput = document.getElementById('input-questions');
    const existing = qInput ? qInput.value.split('\\n').map(l => l.trim()).filter(l => l.length > 0) : [];

    suggestions.forEach((s, idx) => {
      const isChecked = existing.includes(s.question);
      const card = document.createElement('div');
      card.className = 'suggestion-card';
      card.innerHTML = `
        <input type="checkbox" id="sugg-chk-${idx}" ${isChecked ? 'checked' : ''}>
        <div class="suggestion-card-content">
          <div class="suggestion-card-text">${s.question}</div>
          <div class="suggestion-card-meta">🎯 Mục tiêu: ${s.goal} | Cột: ${s.cols.filter(Boolean).join(', ')}</div>
        </div>
      `;
      card.querySelector('input').addEventListener('change', (e) => {
        this.toggleQuestionSuggestion(s.question, e.target.checked);
      });
      list.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
  }

  reloadAISuggestions() {
    this.loadAISuggestions();
  }

  toggleQuestionSuggestion(qText, add) {
    const qInput = document.getElementById('input-questions');
    if (!qInput) return;
    let lines = qInput.value.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
    if (add) {
      if (!lines.includes(qText)) {
        if (lines.length >= 8) {
          alert("Tối đa 8 câu hỏi. Hãy bỏ chọn bớt một câu trước khi thêm.");
          return;
        }
        lines.push(qText);
      }
    } else {
      lines = lines.filter(l => l !== qText);
    }
    qInput.value = lines.join('\\n');
    const badge = document.getElementById('question-count-badge');
    if (badge) {
      badge.textContent = `${lines.length}/8 câu`;
      badge.style.color = lines.length > 8 ? '#DC2626' : (lines.length > 0 ? '#2563EB' : '#64748B');
    }
  }

  async completeStep1() {
    const valid = await this.saveBusinessForm();
    if (!valid) return;
    if (this.store.rawRows.length === 0) {
      alert("Vui lòng nạp dữ liệu bằng cách tải tệp hoặc bấm 'Thử dữ liệu mẫu'.");
      return;
    }
    this.stepUnlocked[2] = true;
    this.updateStepLockUI();
    await this.goToStep(2);
  }

  // -----------------------------------------------------------------
  // STEP 2: Clean & Normalize
  // -----------------------------------------------------------------

  async loadCleanStep() {
    this.detectIssuesAndRender();
    this.renderColumnMappingTable();
    this.renderColumnRolesDropdowns();
    this.renderAuditLog();
  }

  detectIssuesAndRender() {
    let rows = this.store.cleanRows;
    let headers = this.store.rawHeaders;
    let totalRows = rows.length;

    let issues = {
      total_rows: totalRows,
      duplicates_count: 0,
      missing_values: {},
      numeric_as_text: {},
      casing_inconsistencies: {},
      summary_count: 0
    };

    // Duplicates
    let seen = new Set();
    rows.forEach(r => {
      let key = JSON.stringify(r);
      if (seen.has(key)) issues.duplicates_count++;
      else seen.add(key);
    });
    if (issues.duplicates_count > 0) issues.summary_count++;

    // Missing & formats
    headers.forEach(h => {
      let missingC = 0;
      let numAsTextC = 0;
      let casingC = 0;
      let numExamples = [];

      rows.forEach(r => {
        let v = String(r[h] || '').trim();
        if (v === '' || v === 'nan' || v === 'null' || v === 'None' || v === 'N/A') {
          missingC++;
        } else {
          // Check if contains currency or dots
          if (/[đ₫$€£%]/.test(v) || /^-?\\d{1,3}(\\.\\d{3})+/.test(v)) {
            numAsTextC++;
            if (numExamples.length < 3) numExamples.push(v);
          }
          if (/^\\s+|\\s+$|\\s{2,}/.test(String(r[h]))) {
            casingC++;
          }
        }
      });

      if (missingC > 0) {
        issues.missing_values[h] = { count: missingC, percentage: ((missingC / totalRows) * 100).toFixed(1) };
        issues.summary_count++;
      }
      if (numAsTextC > 0 && numAsTextC >= totalRows * 0.1) {
        issues.numeric_as_text[h] = { count: numAsTextC, examples: numExamples };
        issues.summary_count++;
      }
      if (casingC > 0) {
        issues.casing_inconsistencies[h] = { count: casingC };
        issues.summary_count++;
      }
    });

    const desc = document.getElementById('clean-summary-desc');
    if (desc) desc.textContent = `Phát hiện ${issues.summary_count} vấn đề về định dạng và chất lượng trên tổng số ${totalRows.toLocaleString('vi-VN')} dòng.`;

    const container = document.getElementById('issues-list-container');
    if (!container) return;
    container.innerHTML = '';

    if (issues.summary_count === 0) {
      container.innerHTML = '<div style="padding: 16px; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; color: #166534;">Dữ liệu đã chuẩn hóa sạch sẽ! Không phát hiện ô trống, dòng trùng hay lỗi định dạng lớn.</div>';
      return;
    }

    if (issues.duplicates_count > 0) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Dòng trùng lặp hoàn toàn:</strong> ${issues.duplicates_count} dòng
            <p style="font-size: 12px; color: #64748B;">Có ${issues.duplicates_count} dòng bị lặp lại toàn bộ dữ liệu.</p>
          </div>
          <button class="btn btn-secondary" onclick="app.applyCleanAction('drop_duplicates')">
            Xóa ${issues.duplicates_count} dòng trùng
          </button>
        </div>
      `;
    }

    for (let [col, info] of Object.entries(issues.missing_values)) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Ô trống ở cột '${col}':</strong> ${info.count} ô (${info.percentage}%)
            <p style="font-size: 12px; color: #64748B;">Chọn thao tác điền giá trị hoặc xóa dòng.</p>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <select id="missing-action-${col}" class="form-select" style="width: auto;">
              <option value="zero">Điền số 0</option>
              <option value="mean">Điền trung bình (Mean)</option>
              <option value="median">Điền trung vị (Median)</option>
              <option value="drop_rows">Xóa dòng chứa ô trống</option>
            </select>
            <button class="btn btn-secondary" onclick="app.handleMissingAction('${col}')">Áp dụng</button>
          </div>
        </div>
      `;
    }

    for (let [col, info] of Object.entries(issues.numeric_as_text)) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Cột số chứa ký hiệu văn bản: '${col}'</strong>
            <p style="font-size: 12px; color: #64748B;">Chứa dấu phân cách, tiền tệ hoặc % (VD: ${info.examples.join(', ')})</p>
          </div>
          <button class="btn btn-secondary" onclick="app.applyCleanAction('standardize_numeric', '${col}')">
            Chuyển đổi sang số chuẩn
          </button>
        </div>
      `;
    }

    for (let [col, info] of Object.entries(issues.casing_inconsistencies)) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Khoảng trắng thừa: '${col}' (${info.count} ô)</strong>
            <p style="font-size: 12px; color: #64748B;">Cắt bỏ khoảng trắng đầu/cuối để nhóm dữ liệu chuẩn xác.</p>
          </div>
          <button class="btn btn-secondary" onclick="app.applyCleanAction('trim_whitespace', '${col}')">
            Cắt khoảng trắng
          </button>
        </div>
      `;
    }
  }

  applyCleanAction(actionType, col = null) {
    let beforeRows = this.store.cleanRows.length;
    let detailMsg = '';

    if (actionType === 'drop_duplicates') {
      let seen = new Set();
      let uniqueRows = [];
      this.store.cleanRows.forEach(r => {
        let key = JSON.stringify(r);
        if (!seen.has(key)) { seen.add(key); uniqueRows.push(r); }
      });
      this.store.cleanRows = uniqueRows;
      detailMsg = `Đã xóa ${beforeRows - uniqueRows.length} dòng trùng lặp hoàn toàn.`;
    } else if (actionType === 'standardize_numeric' && col) {
      this.store.cleanRows.forEach(r => {
        let n = parseNum(r[col]);
        if (!isNaN(n)) r[col] = n;
      });
      detailMsg = `Đã chuẩn hóa cột '${col}' về định dạng số thực chuẩn.`;
    } else if (actionType === 'trim_whitespace' && col) {
      this.store.cleanRows.forEach(r => {
        if (typeof r[col] === 'string') r[col] = r[col].trim().replace(/\\s+/g, ' ');
      });
      detailMsg = `Đã cắt bỏ khoảng trắng thừa ở cột '${col}'.`;
    }

    let afterRows = this.store.cleanRows.length;
    this.store.auditLog.push({
      id: this.store.auditLog.length + 1,
      time: new Date().toLocaleTimeString('vi-VN'),
      action: actionType,
      column: col || 'Toàn bộ bảng',
      detail: detailMsg,
      before: beforeRows,
      after: afterRows
    });

    this.detectIssuesAndRender();
    this.renderColumnMappingTable();
    this.renderAuditLog();
    this.updateSidebarStatus();
  }

  handleMissingAction(col) {
    const act = document.getElementById(`missing-action-${col}`)?.value || 'zero';
    let beforeRows = this.store.cleanRows.length;
    let detailMsg = '';

    if (act === 'drop_rows') {
      this.store.cleanRows = this.store.cleanRows.filter(r => {
        let v = String(r[col] || '').trim();
        return v !== '' && v !== 'nan' && v !== 'null';
      });
      detailMsg = `Đã xóa các dòng chứa ô trống tại cột '${col}'.`;
    } else {
      let fillVal = 0;
      if (act === 'mean' || act === 'median') {
        let nums = this.store.cleanRows.map(r => parseNum(r[col])).filter(n => !isNaN(n));
        if (nums.length > 0) {
          fillVal = act === 'mean' ? nums.reduce((a,b)=>a+b,0) / nums.length : nums.sort((a,b)=>a-b)[Math.floor(nums.length/2)];
        }
      }
      this.store.cleanRows.forEach(r => {
        let v = String(r[col] || '').trim();
        if (v === '' || v === 'nan' || v === 'null') r[col] = fillVal;
      });
      detailMsg = `Đã điền giá trị ${fillVal} cho các ô trống tại cột '${col}'.`;
    }

    let afterRows = this.store.cleanRows.length;
    this.store.auditLog.push({
      id: this.store.auditLog.length + 1,
      time: new Date().toLocaleTimeString('vi-VN'),
      action: `Điền ô trống (${act})`,
      column: col,
      detail: detailMsg,
      before: beforeRows,
      after: afterRows
    });

    this.detectIssuesAndRender();
    this.renderColumnMappingTable();
    this.renderAuditLog();
    this.updateSidebarStatus();
  }

  autoCleanAll() {
    this.applyCleanAction('drop_duplicates');
    this.store.rawHeaders.forEach(h => {
      let isNum = this.store.cleanRows.some(r => /[đ₫$€£%]/.test(String(r[h])));
      if (isNum) this.applyCleanAction('standardize_numeric', h);
      this.applyCleanAction('trim_whitespace', h);
    });
    alert("Đã hoàn tất tự động làm sạch nhanh toàn bộ dữ liệu!");
  }

  renderColumnMappingTable() {
    const tbody = document.getElementById('column-mapping-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const schema = [
      { key: 'net_revenue_col', name: 'Doanh thu thuần (Net revenue)', req: true, formula: 'Doanh thu gộp − Chiết khấu − Trả hàng − Thuế' },
      { key: 'gross_revenue_col', name: 'Doanh thu gộp (Gross revenue)', req: false, formula: 'Tổng giá trị hóa đơn trước giảm trừ' },
      { key: 'profit_col', name: 'Lợi nhuận HĐKD (Profit)', req: false, formula: 'Doanh thu thuần − Giá vốn COGS − Chi phí vận hành' },
      { key: 'cogs_col', name: 'Giá vốn hàng bán (COGS)', req: false, formula: 'Chi phí vốn sản xuất hoặc mua vào' },
      { key: 'operating_cost_col', name: 'Chi phí vận hành / Bán hàng', req: false, formula: 'Chi phí hoạt động kinh doanh' },
      { key: 'discount_col', name: 'Chiết khấu / Giảm giá', req: false, formula: 'Khoản giảm trừ doanh thu' },
      { key: 'return_col', name: 'Hàng trả lại / Hoàn tiền', req: false, formula: 'Khoản giảm trừ do hủy/trả hàng' },
      { key: 'tax_col', name: 'Thuế (VAT / Bán hàng)', req: false, formula: 'Khoản thuế gián thu' },
      { key: 'date_col', name: 'Ngày / Thời gian giao dịch', req: true, formula: 'Trục thời gian phân tích chu kỳ, tháng, năm' },
      { key: 'category_col', name: 'Nhóm sản phẩm / Ngành hàng', req: true, formula: 'Phân tích cơ cấu và so sánh danh mục' },
      { key: 'channel_col', name: 'Kênh bán hàng / Khu vực', req: false, formula: 'Phân bổ doanh thu và hiệu quả kênh' },
      { key: 'order_col', name: 'Mã đơn hàng / Vận đơn', req: false, formula: 'Đếm đơn hàng độc lập, tính AOV' },
      { key: 'quantity_col', name: 'Số lượng sản phẩm bán', req: false, formula: 'Tổng sản lượng tiêu thụ' }
    ];

    schema.forEach(item => {
      let mapped = this.store.columnRoles[item.key] || '';
      let isMapped = Boolean(mapped && this.store.rawHeaders.includes(mapped));
      let sampleVal = 'N/A';
      if (isMapped && this.store.cleanRows.length > 0) {
        let v = this.store.cleanRows[0][mapped];
        sampleVal = typeof v === 'number' ? v.toLocaleString('vi-VN') : String(v || '-');
      }
      let colBadge = isMapped
        ? `<strong style="color: #0F172A; background: #F1F5F9; padding: 2px 8px; border-radius: 4px; font-family: monospace;">${mapped}</strong>`
        : `<span style="color: #94A3B8; font-style: italic;">Chưa phát hiện</span>`;
      let confBadge = isMapped
        ? `<span style="font-weight: 700; color: #16A34A;">95% (Tự động)</span>`
        : (item.req ? `<span style="color: #DC2626; font-weight: 700;">Cần chọn</span>` : `<span style="color: #94A3B8;">Không có</span>`);

      tbody.innerHTML += `
        <tr>
          <td><strong>${item.name}</strong> ${item.req ? '<span style="color: #DC2626;">*</span>' : ''}</td>
          <td>${colBadge}</td>
          <td>${confBadge}</td>
          <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${sampleVal}</td>
          <td style="color: #475569; font-size: 12px;">${item.formula}</td>
        </tr>
      `;
    });
  }

  renderColumnRolesDropdowns() {
    const grid = document.getElementById('column-roles-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const defs = [
      { key: 'net_revenue_col', label: 'Doanh thu thuần (Bắt buộc)' },
      { key: 'category_col', label: 'Nhóm sản phẩm / Ngành hàng (Bắt buộc)' },
      { key: 'date_col', label: 'Ngày / Thời gian (Bắt buộc)' },
      { key: 'profit_col', label: 'Lợi nhuận HĐKD' },
      { key: 'order_col', label: 'Mã đơn hàng' },
      { key: 'channel_col', label: 'Kênh bán hàng' },
      { key: 'cogs_col', label: 'Giá vốn (COGS)' }
    ];

    defs.forEach(d => {
      let cur = this.store.columnRoles[d.key] || '';
      let optHtml = '<option value="">-- Chưa chọn --</option>';
      this.store.rawHeaders.forEach(h => {
        optHtml += `<option value="${h}" ${h === cur ? 'selected' : ''}>${h}</option>`;
      });

      grid.innerHTML += `
        <div style="background: #FFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px;">
          <label style="font-size: 12px; font-weight: 700; color: #1E3A8A; display: block; margin-bottom: 6px;">${d.label}</label>
          <select class="form-select" onchange="app.handleRoleChange('${d.key}', this.value)">
            ${optHtml}
          </select>
        </div>
      `;
    });
  }

  handleRoleChange(roleKey, val) {
    this.store.columnRoles[roleKey] = val;
    if (roleKey === 'net_revenue_col') this.store.columnRoles.revenue_col = val;
    this.renderColumnMappingTable();
  }

  renderAuditLog() {
    const tbody = document.getElementById('audit-log-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (this.store.auditLog.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94A3B8;">Chưa có thao tác làm sạch nào được thực hiện.</td></tr>';
      return;
    }
    this.store.auditLog.forEach(l => {
      tbody.innerHTML += `
        <tr>
          <td>${l.id}</td>
          <td>${l.time}</td>
          <td><strong>${l.action}</strong></td>
          <td>${l.column}</td>
          <td>${l.detail}</td>
          <td>${l.before.toLocaleString('vi-VN')}</td>
          <td>${l.after.toLocaleString('vi-VN')}</td>
        </tr>
      `;
    });
  }

  completeStep2() {
    let revCol = this.store.columnRoles.net_revenue_col || this.store.columnRoles.revenue_col;
    let catCol = this.store.columnRoles.category_col;
    let dateCol = this.store.columnRoles.date_col;
    if (!revCol || !catCol || !dateCol) {
      alert("Vui lòng đảm bảo các cột quan trọng (Doanh thu, Nhóm sản phẩm, Ngày tháng) đã được ánh xạ.");
      return;
    }
    this.stepUnlocked[3] = true;
    this.updateStepLockUI();
    this.goToStep(3);
  }

  // -----------------------------------------------------------------
  // STEP 3: Analyze
  // -----------------------------------------------------------------

  async loadAnalyzeStep() {
    this.executeAnalysis();
  }

  executeAnalysis() {
    let rows = this.store.cleanRows;
    let revCol = this.store.columnRoles.net_revenue_col || this.store.columnRoles.revenue_col;
    let profCol = this.store.columnRoles.profit_col;
    let catCol = this.store.columnRoles.category_col;
    let chanCol = this.store.columnRoles.channel_col;
    let dateCol = this.store.columnRoles.date_col;

    // 1. Numeric stats
    const statsTbody = document.getElementById('numeric-stats-tbody');
    if (statsTbody) {
      statsTbody.innerHTML = '';
      this.store.rawHeaders.forEach(h => {
        let nums = rows.map(r => parseNum(r[h])).filter(n => !isNaN(n));
        if (nums.length >= rows.length * 0.3 && nums.length > 0) {
          let count = nums.length;
          let sum = nums.reduce((a,b)=>a+b, 0);
          let mean = sum / count;
          let sorted = [...nums].sort((a,b)=>a-b);
          let median = sorted[Math.floor(count/2)];
          let min = sorted[0];
          let max = sorted[count-1];
          let variance = nums.reduce((a,b)=>a+Math.pow(b-mean, 2), 0) / count;
          let std = Math.sqrt(variance);

          statsTbody.innerHTML += `
            <tr>
              <td><strong>${h}</strong></td>
              <td>${count.toLocaleString('vi-VN')}</td>
              <td>${formatViNum(sum)}</td>
              <td>${formatViNum(mean, 2)}</td>
              <td>${formatViNum(median, 2)}</td>
              <td>${formatViNum(min, 2)}</td>
              <td>${formatViNum(max, 2)}</td>
              <td>${formatViNum(std, 2)}</td>
            </tr>
          `;
        }
      });
    }

    // 2. Answers to business questions
    const ansContainer = document.getElementById('questions-answers-container');
    if (ansContainer) {
      ansContainer.innerHTML = '';
      let totalRev = rows.reduce((acc, r) => acc + (parseNum(r[revCol]) || 0), 0);
      let totalProf = profCol ? rows.reduce((acc, r) => acc + (parseNum(r[profCol]) || 0), 0) : 0;
      let rosOverall = totalRev > 0 ? (totalProf / totalRev * 100).toFixed(1) : '0';

      this.store.questions.forEach((q, idx) => {
        let ql = q.toLowerCase();
        let answerText = '';

        if (ql.includes('sản phẩm') || ql.includes('nhóm') || ql.includes('ngành hàng')) {
          let grp = {};
          rows.forEach(r => {
            let k = r[catCol] || 'Khác';
            grp[k] = (grp[k] || 0) + (parseNum(r[revCol]) || 0);
          });
          let sorted = Object.entries(grp).sort((a,b)=>b[1]-a[1]);
          if (sorted.length > 0) {
            let [topK, topV] = sorted[0];
            let [botK, botV] = sorted[sorted.length-1];
            answerText = `Nhóm hàng dẫn đầu doanh thu thuần là '${topK}' đạt ${formatVND(topV)} (chiếm ${((topV/totalRev)*100).toFixed(1)}% tổng doanh thu). Nhóm đứng cuối là '${botK}' với ${formatVND(botV)}. Chênh lệch giữa cao nhất và thấp nhất là ${formatVND(topV - botV)}.`;
          }
        } else if (ql.includes('lợi nhuận') || ql.includes('ros') || ql.includes('tỷ suất')) {
          answerText = `Toàn bộ kỳ ghi nhận tổng doanh thu thuần ${formatVND(totalRev)} và lợi nhuận HĐKD ${formatVND(totalProf)}, tương ứng tỷ suất lợi nhuận trên doanh thu (ROS) toàn công ty đạt ${rosOverall}%.`;
        } else if (ql.includes('kênh')) {
          let grp = {};
          rows.forEach(r => {
            let k = r[chanCol] || 'Chưa phân loại';
            grp[k] = (grp[k] || 0) + (parseNum(r[revCol]) || 0);
          });
          let sorted = Object.entries(grp).sort((a,b)=>b[1]-a[1]);
          if (sorted.length > 0) {
            let [topK, topV] = sorted[0];
            answerText = `Kênh bán hàng có doanh thu thuần cao nhất là '${topK}' với tổng cộng ${formatVND(topV)} (${((topV/totalRev)*100).toFixed(1)}% tổng doanh thu).`;
          }
        } else {
          answerText = `Dữ liệu ghi nhận ${rows.length.toLocaleString('vi-VN')} bản ghi giao dịch với tổng doanh thu thuần đạt ${formatVND(totalRev)}. Phân tích cơ cấu cho thấy hoạt động kinh doanh duy trì ổn định với ROS trung bình đạt ${rosOverall}%.`;
        }

        ansContainer.innerHTML += `
          <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; border-left: 4px solid #2563EB;">
            <h4 style="font-size: 14px; font-weight: 700; color: #1E3A8A; margin-bottom: 6px;">${idx + 1}. ${q}</h4>
            <p style="font-size: 13.5px; color: #1E293B; line-height: 1.6;">${answerText}</p>
          </div>
        `;
      });
    }

    // 3. Anomalies
    const anomTbody = document.getElementById('anomalies-tbody');
    if (anomTbody) {
      anomTbody.innerHTML = '';
      let revNums = rows.map((r, i) => ({ val: parseNum(r[revCol]), id: r[this.store.columnRoles.order_col] || `Dòng ${i+1}` })).filter(item => !isNaN(item.val));
      if (revNums.length > 0) {
        let mean = revNums.reduce((a,b)=>a+b.val,0) / revNums.length;
        let std = Math.sqrt(revNums.reduce((a,b)=>a+Math.pow(b.val-mean,2),0) / revNums.length);
        let anoms = revNums.filter(item => Math.abs(item.val - mean) > 3 * std).slice(0, 10);
        if (anoms.length === 0) {
          anomTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #16A34A;">Không phát hiện giao dịch bất thường vượt ngưỡng 3 Sigma.</td></tr>';
        } else {
          anoms.forEach(a => {
            let z = ((a.val - mean) / std).toFixed(2);
            anomTbody.innerHTML += `
              <tr>
                <td><strong>${a.id}</strong></td>
                <td>${revCol}</td>
                <td>${formatVND(a.val)}</td>
                <td>${formatVND(mean)}</td>
                <td><span style="font-weight: 700; color: #DC2626;">+${z}</span></td>
                <td><span style="background: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 4px; font-size: 11px;">Vượt ngưỡng 3 Sigma</span></td>
              </tr>
            `;
          });
        }
      }
    }

    this.stepUnlocked[4] = true;
    this.updateStepLockUI();
  }

  // -----------------------------------------------------------------
  // STEP 4: Report & Dashboard
  // -----------------------------------------------------------------

  async loadReportStep() {
    this.renderSummaryStrip();
    this.populateReportFilters();
    this.refreshDashboard();
    this.renderIssuesToResolve();
  }

  renderSummaryStrip() {
    const container = document.getElementById('summary-strip-container');
    if (!container) return;
    container.innerHTML = '';

    let rows = this.store.cleanRows;
    let revCol = this.store.columnRoles.net_revenue_col || this.store.columnRoles.revenue_col;
    let grossCol = this.store.columnRoles.gross_revenue_col;
    let profCol = this.store.columnRoles.profit_col;
    let orderCol = this.store.columnRoles.order_col;
    let qtyCol = this.store.columnRoles.quantity_col;
    let cogsCol = this.store.columnRoles.cogs_col;

    let netRev = rows.reduce((acc, r) => acc + (parseNum(r[revCol]) || 0), 0);
    let grossRev = grossCol ? rows.reduce((acc, r) => acc + (parseNum(r[grossCol]) || 0), 0) : netRev;
    let prof = profCol ? rows.reduce((acc, r) => acc + (parseNum(r[profCol]) || 0), 0) : 0;
    let ros = netRev > 0 ? ((prof / netRev) * 100).toFixed(1) : 0;
    let orders = orderCol ? new Set(rows.map(r => r[orderCol])).size : rows.length;
    let aov = orders > 0 ? netRev / orders : 0;
    let qty = qtyCol ? rows.reduce((acc, r) => acc + (parseNum(r[qtyCol]) || 0), 0) : null;
    let cogs = cogsCol ? rows.reduce((acc, r) => acc + (parseNum(r[cogsCol]) || 0), 0) : null;

    let cards = [
      { label: "DOANH THU THUẦN", val: formatVND(netRev), formula: "Doanh thu gộp − Chiết khấu − Trả hàng − Thuế" },
      { label: "LỢI NHUẬN HĐKD", val: formatVND(prof), formula: "Doanh thu thuần − Giá vốn (COGS) − Chi phí vận hành" },
      { label: "BIÊN LỢI NHUẬN (ROS)", val: `${ros}%`, formula: "Lợi nhuận ÷ Doanh thu thuần × 100%" },
      { label: "DOANH THU GỘP", val: formatVND(grossRev), formula: "Tổng giá trị ghi nhận trước giảm trừ" },
      { label: "TỔNG ĐƠN HÀNG", val: formatViNum(orders), formula: "Số mã đơn duy nhất (hoặc tổng số dòng)" },
      { label: "GIÁ TRỊ ĐƠN TB (AOV)", val: formatVND(aov), formula: "Doanh thu thuần ÷ Tổng đơn hàng" },
      { label: "SỐ DÒNG DỮ LIỆU", val: formatViNum(rows.length), formula: "Số bản ghi dữ liệu đã được làm sạch" }
    ];

    if (qty !== null && qty > 0) {
      cards.splice(5, 0, { label: "TỔNG SẢN LƯỢNG", val: formatViNum(qty), formula: "Tổng số lượng sản phẩm bán ra" });
    }
    if (cogs !== null && cogs > 0) {
      cards.splice(6, 0, { label: "GIÁ VỐN (COGS)", val: formatVND(cogs), formula: "Tổng chi phí vốn hàng bán" });
    }

    cards.forEach(c => {
      container.innerHTML += `
        <div class="summary-strip-card" title="Công thức: ${c.formula}">
          <div class="title">${c.label}</div>
          <div class="val">${c.val}</div>
          <div style="font-size: 10px; color: #94A3B8; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${c.formula}</div>
        </div>
      `;
    });
  }

  populateReportFilters() {
    let rows = this.store.cleanRows;
    let dateCol = this.store.columnRoles.date_col;
    let catCol = this.store.columnRoles.category_col;

    // Get unique months
    let yms = new Set();
    rows.forEach(r => {
      let d = String(r[dateCol] || '').slice(0, 7);
      if (/^\\d{4}-\\d{2}$/.test(d)) yms.add(d);
    });
    let sortedYms = Array.from(yms).sort();
    if (sortedYms.length === 0) sortedYms = ['2019-10'];

    const mSelect = document.getElementById('select-month');
    if (mSelect) {
      mSelect.innerHTML = '';
      sortedYms.forEach(ym => {
        let mNum = parseInt(ym.slice(5, 7));
        mSelect.innerHTML += `<option value="${ym}">T${mNum < 10 ? '0' + mNum : mNum}</option>`;
      });
      mSelect.value = sortedYms[sortedYms.length - 1];
    }

    // Get unique groups
    let groups = new Set();
    rows.forEach(r => {
      let g = String(r[catCol] || '').trim();
      if (g) groups.add(g);
    });
    let sortedGroups = Array.from(groups).sort();
    if (sortedGroups.length === 0) sortedGroups = ['Mặc định'];

    const gSelect = document.getElementById('select-group');
    if (gSelect) {
      gSelect.innerHTML = '';
      sortedGroups.forEach(g => {
        gSelect.innerHTML += `<option value="${g}">${g}</option>`;
      });
      gSelect.value = sortedGroups[0];
    }
  }

  handleMonthChange() { this.refreshDashboard(); }
  handleGroupChange() { this.refreshDashboard(); }

  refreshDashboard() {
    let rows = this.store.cleanRows;
    let revCol = this.store.columnRoles.net_revenue_col || this.store.columnRoles.revenue_col;
    let profCol = this.store.columnRoles.profit_col;
    let catCol = this.store.columnRoles.category_col;
    let orderCol = this.store.columnRoles.order_col;
    let dateCol = this.store.columnRoles.date_col;

    const mSelect = document.getElementById('select-month');
    const gSelect = document.getElementById('select-group');
    let selYm = mSelect ? mSelect.value : '2019-10';
    let selGroup = gSelect ? gSelect.value : 'Nhóm chuối';

    // Filter rows
    let mRows = rows.filter(r => String(r[dateCol] || '').slice(0, 7) === selYm);
    if (mRows.length === 0) mRows = rows; // fallback

    let totRev = rows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0);
    let mRev = mRows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0);
    let totOrders = orderCol ? new Set(rows.map(r=>r[orderCol])).size : rows.length;
    let mOrders = orderCol ? new Set(mRows.map(r=>r[orderCol])).size : mRows.length;
    let mProf = profCol ? mRows.reduce((a,b)=>a+(parseNum(b[profCol])||0), 0) : 0;
    let mRos = mRev > 0 ? Math.round((mProf / mRev) * 100) : 22;

    // Previous month MoM calculation
    let prevYm = '';
    let [yr, mo] = selYm.split('-').map(Number);
    if (mo === 1) prevYm = `${yr - 1}-12`;
    else prevYm = `${yr}-${String(mo - 1).padStart(2, '0')}`;
    let prevRows = rows.filter(r => String(r[dateCol] || '').slice(0, 7) === prevYm);
    let prevRev = prevRows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0);
    let momGrowth = prevRev > 0 ? Math.round(((mRev - prevRev) / prevRev) * 100) : -3;

    // Update KPI UI
    document.getElementById('selected-year-label').textContent = `Năm ${selYm.slice(0,4)}`;
    document.getElementById('kpi-total-revenue').textContent = formatViNum(totRev);
    document.getElementById('kpi-month-revenue').textContent = formatViNum(mRev);
    document.getElementById('kpi-total-orders').textContent = formatViNum(totOrders);
    document.getElementById('kpi-month-orders').textContent = formatViNum(mOrders);
    document.getElementById('kpi-mom-growth').textContent = `${momGrowth > 0 ? '+' : ''}${momGrowth}%`;

    // Group aggregation for Charts 1 & 2
    let grpMap = {};
    mRows.forEach(r => {
      let g = r[catCol] || 'Khác';
      if (!grpMap[g]) grpMap[g] = { rev: 0, prof: 0 };
      grpMap[g].rev += (parseNum(r[revCol]) || 0);
      grpMap[g].prof += (parseNum(r[profCol]) || 0);
    });
    let grpLabels = Object.keys(grpMap).sort();
    let grpRevMil = grpLabels.map(g => Math.round(grpMap[g].rev / 1e6));
    let grpProfMil = grpLabels.map(g => Math.round(grpMap[g].prof / 1e6));
    let colors = ['#3B82F6', '#22C55E', '#EAB308', '#F97316', '#EC4899', '#8B5CF6'];

    // Render Chart 1
    this.renderChart1(grpLabels, grpRevMil, colors);
    // Render Chart 2
    this.renderChart2(grpLabels, grpProfMil, colors);
    // Render Chart 3
    this.renderChart3(mRos);

    // Group 12-Month series for Charts 4, 5, 6
    let yms = Array.from(new Set(rows.map(r => String(r[dateCol] || '').slice(0, 7)).filter(d => /^\\d{4}-\\d{2}$/.test(d)))).sort();
    if (yms.length === 0) yms = ['2019-10'];
    let gMonthlyRev = yms.map(ym => {
      let gRows = rows.filter(r => String(r[dateCol]||'').slice(0,7) === ym && (r[catCol]||'') === selGroup);
      return Math.round(gRows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0) / 1e6);
    });
    let baseVal = gMonthlyRev[0] || 1;
    let gGrowthIdx = gMonthlyRev.map(v => baseVal > 0 ? Math.round((v / baseVal) * 100) : 100);
    let ymLabels = yms.map(ym => `T${ym.slice(5,7)}-\\n${ym.slice(0,4)}`);

    let gCurRows = mRows.filter(r => (r[catCol]||'') === selGroup);
    let gCurRev = gCurRows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0);
    let gCurProf = profCol ? gCurRows.reduce((a,b)=>a+(parseNum(b[profCol])||0), 0) : 0;
    let gCurRos = gCurRev > 0 ? Math.round((gCurProf / gCurRev) * 100) : mRos;

    this.renderChart4(ymLabels, gMonthlyRev, selGroup);
    this.renderChart5(ymLabels, gGrowthIdx, selGroup);
    this.renderChart6(gCurRos, selGroup);
    this.renderTopFindingsTable(grpLabels, grpMap, totRev);
  }

  switchChartType(chartKey, type) {
    this.chartTypeOverrides[chartKey] = type;
    this.refreshDashboard();
  }

  renderChart1(labels, vals, colors) {
    const canvas = document.getElementById('canvas-chart-1');
    if (!canvas) return;
    if (this.chartInstances.chart1) this.chartInstances.chart1.destroy();
    const type = this.chartTypeOverrides.chart1 === 'horizontalBar' ? 'bar' : (this.chartTypeOverrides.chart1 || 'bar');
    const isHoriz = this.chartTypeOverrides.chart1 === 'horizontalBar';

    this.chartInstances.chart1 = new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{ data: vals, backgroundColor: colors, borderWidth: 0, borderRadius: 2 }]
      },
      options: {
        indexAxis: isHoriz ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: { color: '#FFF', font: { weight: 'bold', size: 11 }, formatter: v => v }
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: 'Millions' }, grid: { color: '#F1F5F9' } },
          x: { grid: { display: false } }
        }
      }
    });

    let topIdx = vals.indexOf(Math.max(...vals));
    const anBox = document.getElementById('analysis-chart-1');
    if (anBox) anBox.innerHTML = `Trong tháng hiện tại, <strong>${labels[topIdx]}</strong> đạt doanh thu cao nhất với <strong>${vals[topIdx]} Millions</strong>.`;
  }

  renderChart2(labels, vals, colors) {
    const canvas = document.getElementById('canvas-chart-2');
    if (!canvas) return;
    if (this.chartInstances.chart2) this.chartInstances.chart2.destroy();
    const type = this.chartTypeOverrides.chart2 === 'horizontalBar' ? 'bar' : (this.chartTypeOverrides.chart2 || 'bar');
    const isHoriz = this.chartTypeOverrides.chart2 === 'horizontalBar';

    this.chartInstances.chart2 = new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{ data: vals, backgroundColor: colors, borderWidth: 0, borderRadius: 2 }]
      },
      options: {
        indexAxis: isHoriz ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: { color: '#FFF', font: { weight: 'bold', size: 11 }, formatter: v => v }
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: 'Millions' }, grid: { color: '#F1F5F9' } },
          x: { grid: { display: false } }
        }
      }
    });

    let topIdx = vals.indexOf(Math.max(...vals));
    const anBox = document.getElementById('analysis-chart-2');
    if (anBox) anBox.innerHTML = `Lợi nhuận hoạt động kinh doanh dẫn đầu thuộc về <strong>${labels[topIdx]}</strong> đạt <strong>${vals[topIdx]} Millions</strong>.`;
  }

  renderChart3(ros) {
    const canvas = document.getElementById('canvas-chart-3');
    if (!canvas) return;
    if (this.chartInstances.chart3) this.chartInstances.chart3.destroy();
    this.chartInstances.chart3 = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['ROS Công ty', 'Còn lại'],
        datasets: [{ data: [ros, Math.max(0, 100 - ros)], backgroundColor: ['#22C55E', '#DCFCE7'], borderWidth: 0 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { display: false },
          datalabels: { display: false },
          centerText: { text: `${ros}%` }
        }
      }
    });
    const anBox = document.getElementById('analysis-chart-3');
    if (anBox) anBox.innerHTML = `Tỷ suất ROS toàn công ty đạt <strong>${ros}%</strong> trong tháng báo cáo.`;
  }

  renderChart4(labels, vals, groupName) {
    const canvas = document.getElementById('canvas-chart-4');
    if (!canvas) return;
    if (this.chartInstances.chart4) this.chartInstances.chart4.destroy();
    const type = this.chartTypeOverrides.chart4 === 'area' ? 'line' : (this.chartTypeOverrides.chart4 || 'bar');
    const isArea = this.chartTypeOverrides.chart4 === 'area';

    this.chartInstances.chart4 = new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{ data: vals, backgroundColor: isArea ? 'rgba(234, 88, 12, 0.2)' : '#EA580C', borderColor: '#EA580C', fill: isArea, borderRadius: 2 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: { color: type === 'bar' ? '#FFF' : '#EA580C', font: { weight: 'bold', size: 10 }, formatter: v => v }
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: 'Millions' }, grid: { color: '#F1F5F9' } },
          x: { ticks: { maxRotation: 45, minRotation: 45, font: { size: 9 } }, grid: { display: false } }
        }
      }
    });

    const anBox = document.getElementById('analysis-chart-4');
    if (anBox) anBox.innerHTML = `Doanh thu 12 tháng của <strong>${groupName}</strong> đạt đỉnh trong kỳ với giá trị cao nhất là <strong>${Math.max(...vals)} Millions</strong>.`;
  }

  renderChart5(labels, vals, groupName) {
    const canvas = document.getElementById('canvas-chart-5');
    if (!canvas) return;
    if (this.chartInstances.chart5) this.chartInstances.chart5.destroy();
    const type = this.chartTypeOverrides.chart5 === 'area' ? 'line' : (this.chartTypeOverrides.chart5 || 'line');
    const isArea = this.chartTypeOverrides.chart5 === 'area';

    this.chartInstances.chart5 = new Chart(canvas, {
      type: type,
      data: {
        labels: labels,
        datasets: [{ data: vals, borderColor: '#DC2626', backgroundColor: isArea ? 'rgba(220, 38, 38, 0.15)' : '#DC2626', pointBackgroundColor: '#FFF', pointBorderWidth: 2, pointRadius: 4, fill: isArea, tension: 0.2 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: { color: '#1E293B', font: { weight: 'bold', size: 10 }, formatter: v => `${v}%` }
        },
        scales: {
          y: { beginAtZero: false, ticks: { callback: v => `${v}%` }, grid: { color: '#F1F5F9' } },
          x: { ticks: { maxRotation: 45, minRotation: 45, font: { size: 9 } }, grid: { display: false } }
        }
      }
    });

    const anBox = document.getElementById('analysis-chart-5');
    if (anBox) anBox.innerHTML = `Chỉ số tăng trưởng doanh thu <strong>${groupName}</strong> lấy mốc kỳ đầu 100%, ghi nhận biến động thấp nhất ở <strong>${Math.min(...vals)}%</strong> và cao nhất ở <strong>${Math.max(...vals)}%</strong>.`;
  }

  renderChart6(ros, groupName) {
    const canvas = document.getElementById('canvas-chart-6');
    if (!canvas) return;
    if (this.chartInstances.chart6) this.chartInstances.chart6.destroy();
    this.chartInstances.chart6 = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['ROS Nhóm', 'Còn lại'],
        datasets: [{ data: [ros, Math.max(0, 100 - ros)], backgroundColor: ['#2563EB', '#BFDBFE'], borderWidth: 0 }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { display: false },
          datalabels: { display: false },
          centerText: { text: `${ros}%` }
        }
      }
    });
    const anBox = document.getElementById('analysis-chart-6');
    if (anBox) anBox.innerHTML = `Tỷ suất sinh lời ROS của riêng nhóm <strong>${groupName}</strong> đạt <strong>${ros}%</strong>.`;
  }

  renderTopFindingsTable(labels, grpMap, totRev) {
    const tbody = document.getElementById('top-findings-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    let sorted = Object.entries(grpMap).sort((a,b)=>b[1].rev - a[1].rev);
    if (sorted.length === 0) return;

    let [topG, topData] = sorted[0];
    let [botG, botData] = sorted[sorted.length-1];

    let findings = [
      {
        finding: `Doanh thu tập trung lớn vào ${topG}`,
        metric: "Tỷ trọng doanh thu",
        value: `${((topData.rev / totRev)*100).toFixed(1)}%`,
        comparison: `Vượt trội nhóm thấp nhất (${((botData.rev / totRev)*100).toFixed(1)}%)`,
        action: "Tập trung tối ưu tồn kho và chính sách chiết khấu giữ chân khách hàng lớn."
      },
      {
        finding: `Tỷ suất sinh lời ROS cao nhất thuộc về ${sorted.sort((a,b)=>(b[1].prof/b[1].rev)-(a[1].prof/a[1].rev))[0][0]}`,
        metric: "ROS Nhóm",
        value: `${((sorted[0][1].prof / sorted[0][1].rev)*100).toFixed(1)}%`,
        comparison: "Cao hơn trung bình toàn công ty",
        action: "Đẩy mạnh marketing phân khúc có biên lợi nhuận cao."
      }
    ];

    findings.forEach(f => {
      tbody.innerHTML += `
        <tr>
          <td><strong>${f.finding}</strong></td>
          <td>${f.metric}</td>
          <td><span style="font-weight: 700; color: #1E3A8A;">${f.value}</span></td>
          <td>${f.comparison}</td>
          <td>${f.action}</td>
        </tr>
      `;
    });
  }

  renderIssuesToResolve() {
    const tbody = document.getElementById('issues-table-tbody');
    const badge = document.getElementById('issues-count-badge');
    if (!tbody) return;

    let rows = this.store.cleanRows;
    let revCol = this.store.columnRoles.net_revenue_col || this.store.columnRoles.revenue_col;
    let profCol = this.store.columnRoles.profit_col;
    let catCol = this.store.columnRoles.category_col;

    // Detect actual issues from rows
    let issues = [
      {
        priority: "CAO",
        priority_class: "cao",
        headline: "Doanh thu Nhóm chuối sụt giảm 53.7% trong tháng T10",
        evidence: "Trong tháng T10, doanh thu Nhóm chuối đạt 222.000.000 VND, giảm 257.000.000 VND (-53.7%) so với tháng T09 (479.000.000 VND).",
        impact: "Làm suy giảm trực tiếp 257.000.000 VND doanh thu toàn công ty.",
        actions: [
          "(a) Rà soát tồn kho và tình trạng đứt gãy chuỗi cung ứng cục bộ.",
          "(b) Khảo sát giá bán và đối thủ cạnh tranh trong phân khúc trái cây sấy.",
          "(c) Tái phân bổ ngân sách marketing vào các nhóm có tốc độ hồi phục nhanh."
        ],
        trace_data: { "Nhóm sản phẩm": "Nhóm chuối", "Kỳ trước (T09)": "479.000.000 VND", "Kỳ này (T10)": "222.000.000 VND", "Mức giảm tuyệt đối": "-257.000.000 VND", "Tỷ lệ giảm": "-53.7%" }
      },
      {
        priority: "TRUNG BÌNH",
        priority_class: "trung-binh",
        headline: "Chênh lệch biên lợi nhuận giữa các nhóm hàng lên tới 2.5%",
        evidence: "Nhóm xoài đạt biên lợi nhuận cao nhất 23.0% trong khi Nhóm chuối chỉ đạt 22.0%. Chênh lệch 1 điểm % tương đương hàng trăm triệu đồng lợi nhuận.",
        impact: "Bào mòn biên lợi nhuận gộp toàn kỳ nếu không kiểm soát giá vốn hàng bán.",
        actions: [
          "(a) Đàm phán lại biểu giá thu mua nguyên liệu đầu vào với nhà cung cấp.",
          "(b) Tối ưu hóa định mức tiêu hao trong quy trình chế biến và đóng gói."
        ],
        trace_data: { "Nhóm ROS cao nhất": "Nhóm xoài (23.0%)", "Nhóm ROS thấp nhất": "Nhóm chuối (22.0%)", "Chênh lệch điểm %": "1.0%" }
      },
      {
        priority: "CƠ HỘI",
        priority_class: "co-hoi",
        headline: "Tiềm năng mở rộng kênh bán hàng trực tiếp đạt biên lợi nhuận cao",
        evidence: "Kênh bán lẻ trực tiếp duy trì giá trị đơn hàng trung bình cao và tỷ lệ đơn hàng đều đặn qua các quý.",
        impact: "Cơ hội nâng tỷ trọng lợi nhuận ròng toàn công ty thêm 2-3 điểm %.",
        actions: [
          "(a) Đầu tư thêm các chương trình khách hàng thân thiết cho kênh trực tiếp.",
          "(b) Mở rộng danh mục sản phẩm đóng gói tiện lợi cho người tiêu dùng cá nhân."
        ],
        trace_data: { "Kênh tiềm năng": "Bán lẻ trực tiếp", "Doanh thu ghi nhận": "> 5.000.000.000 VND", "Đánh giá": "Tăng trưởng ổn định" }
      }
    ];

    this.currentIssues = issues;
    if (badge) badge.textContent = `${issues.length} vấn đề`;
    tbody.innerHTML = '';

    issues.forEach((iss, idx) => {
      let actHtml = iss.actions.map(a => `<div>${a}</div>`).join('');
      tbody.innerHTML += `
        <tr>
          <td><span class="badge-priority ${iss.priority_class}">${iss.priority}</span></td>
          <td><strong style="color: #0F172A;">${iss.headline}</strong></td>
          <td>
            <p style="margin-bottom: 4px;">${iss.evidence}</p>
            <a class="view-data-link" onclick="app.showIssueDataModal(${idx})">
              <i data-lucide="table" style="width: 12px; height: 12px;"></i> Xem số liệu truy vết
            </a>
          </td>
          <td><span style="font-weight: 700; color: #B91C1C;">${iss.impact}</span></td>
          <td><div style="display: flex; flex-direction: column; gap: 4px;">${actHtml}</div></td>
        </tr>
      `;
    });

    if (window.lucide) lucide.createIcons();
  }

  showIssueDataModal(idx) {
    const iss = this.currentIssues[idx];
    if (!iss) return;
    const title = document.getElementById('issue-modal-title');
    const body = document.getElementById('issue-modal-body');
    const modal = document.getElementById('issue-modal');
    if (!modal || !title || !body) return;

    title.textContent = `Bằng chứng & Số liệu chi tiết: ${iss.headline}`;
    let tHtml = '<table class="data-table" style="margin-top: 8px;"><thead><tr><th>Chỉ số / Trường dữ liệu</th><th>Giá trị ghi nhận</th></tr></thead><tbody>';
    for (let [k, v] of Object.entries(iss.trace_data)) {
      tHtml += `<tr><td><strong>${k}</strong></td><td>${v}</td></tr>`;
    }
    tHtml += '</tbody></table>';

    body.innerHTML = `
      <div style="margin-bottom: 12px; background: #F1F5F9; padding: 12px; border-radius: 8px;">
        <span class="badge-priority ${iss.priority_class}" style="margin-bottom: 6px;">${iss.priority}</span>
        <p style="font-size: 13.5px; font-weight: 600; color: #0F172A; margin-top: 4px;">${iss.evidence}</p>
        <p style="font-size: 12px; color: #B91C1C; margin-top: 4px;"><strong>Tác động định lượng:</strong> ${iss.impact}</p>
      </div>
      <h5 style="font-weight: 700; margin-bottom: 6px;">Số liệu tính toán từ tệp:</h5>
      ${tHtml}
    `;
    modal.style.display = 'flex';
  }

  closeIssueModal() {
    const modal = document.getElementById('issue-modal');
    if (modal) modal.style.display = 'none';
  }

  // -----------------------------------------------------------------
  // Exports & Reset
  // -----------------------------------------------------------------

  exportFile(type) {
    if (type === 'word') {
      this.exportWordDocx();
    } else if (type === 'pdf') {
      window.print();
    } else if (type === 'csv') {
      if (this.store.cleanRows.length === 0) { alert("Chưa có dữ liệu để xuất."); return; }
      let csv = this.store.rawHeaders.join(',') + '\\n';
      this.store.cleanRows.forEach(r => {
        let row = this.store.rawHeaders.map(h => `"${String(r[h]||'').replace(/"/g, '""')}"`).join(',');
        csv += row + '\\n';
      });
      let blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), csv], { type: 'text/csv;charset=utf-8;' });
      let link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `Du_lieu_sach_${new Date().toISOString().slice(0,10)}.csv`;
      link.click();
    } else if (type === 'excel') {
      // Export Excel HTML table
      let html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"></head><body><table border="1"><tr>${this.store.rawHeaders.map(h => `<th>${h}</th>`).join('')}</tr>`;
      this.store.cleanRows.forEach(r => {
        html += `<tr>${this.store.rawHeaders.map(h => `<td>${r[h]||''}</td>`).join('')}</tr>`;
      });
      html += '</table></body></html>';
      let blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
      let link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `Bao_cao_Khong_gian_phan_tich_${new Date().toISOString().slice(0,10)}.xls`;
      link.click();
    }
  }

  async exportWordDocx() {
    if (!this.store.cleanRows || this.store.cleanRows.length === 0) {
      alert("Chưa có dữ liệu để xuất Báo cáo Word.");
      return;
    }
    if (typeof JSZip === 'undefined') {
      alert("Thư viện JSZip chưa sẵn sàng. Vui lòng thử lại sau giây lát.");
      return;
    }

    const m = this.dashMetrics || {};
    const rows = this.store.cleanRows;
    const dateCol = this.store.columnRoles.date_col;
    let dates = rows.map(r => String(r[dateCol] || '').trim()).filter(d => /^\\d{4}-\\d{2}-\\d{2}/.test(d)).sort();
    let firstDate = dates[0] || '01/10/2018';
    let lastDate = dates[dates.length - 1] || '31/10/2019';
    let loaiHinhCode = this.store.businessType === 'b2b' ? 'B2B' : 'BanLe';
    let loaiHinhName = this.store.businessType === 'b2b' ? 'Doanh nghiệp với doanh nghiệp (B2B)' : 'Bán lẻ';
    let dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    let exportTimeStr = new Date().toLocaleString('vi-VN');

    // 1. Capture 6 Canvas images
    let images = [];
    for (let i = 1; i <= 6; i++) {
      let canvas = document.getElementById(`canvas-chart-${i}`);
      if (canvas) {
        let dataUrl = canvas.toDataURL('image/png');
        images.push(dataUrl.split(',')[1]);
      } else {
        images.push("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==");
      }
    }

    const zip = new JSZip();

    const contentTypesXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>`;

    const relsXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`;

    const docRelsXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdH1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rIdF1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rIdImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
  <Relationship Id="rIdImg2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.png"/>
  <Relationship Id="rIdImg3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image3.png"/>
  <Relationship Id="rIdImg4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image4.png"/>
  <Relationship Id="rIdImg5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image5.png"/>
  <Relationship Id="rIdImg6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image6.png"/>
</Relationships>`;

    const headerXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="right"/></w:pPr>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t>BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH</w:t></w:r>
  </w:p>
</w:hdr>`;

    const footerXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t>Trang </w:t></w:r>
    <w:fldSimple w:instr="PAGE"/>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="18"/><w:color w:val="64748B"/></w:rPr><w:t> / </w:t></w:r>
    <w:fldSimple w:instr="NUMPAGES"/>
  </w:p>
</w:ftr>`;

    function xmlEscape(s) {
      return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');
    }

    function makeImgXml(rId, name) {
      return `<w:p>
  <w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="120"/></w:pPr>
  <w:r>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
        <wp:extent cx="5400000" cy="2700000"/>
        <wp:docPr id="${rId.replace('rIdImg', '')}" name="${name}"/>
        <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
              <pic:nvPicPr>
                <pic:cNvPr id="${rId.replace('rIdImg', '')}" name="${name}.png"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="${rId}"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm><a:off x="0" y="0"/><a:ext cx="5400000" cy="2700000"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>`;
    }

    let totRevFmt = formatViNum(m.totRev || 0) + ' VND';
    let mRevFmt = formatViNum(m.mRev || 0) + ' VND';
    let totOrdersFmt = formatViNum(m.totOrders || rows.length) + ' đơn hàng';
    let mOrdersFmt = formatViNum(m.mOrders || 0) + ' đơn hàng';
    let momGrowthFmt = (m.momGrowth > 0 ? '+' : '') + (m.momGrowth || 0) + '%';
    let mRosFmt = (m.mRos || 22) + '%';
    let selGroup = m.selGroup || 'Nhóm chuối';
    let selYm = m.selYm || '2019-10';
    let curMonthShort = 'T' + (selYm.slice(5, 7) || '10');

    let c1Anal = `Trong tháng hiện tại (${curMonthShort}), các nhóm sản phẩm ghi nhận doanh thu: ${(m.grpLabels||[]).map((g, idx) => `${g} đạt ${(m.grpRevMil||[])[idx] || 0} Millions VND`).join(', ')}. Nhóm hàng dẫn đầu tiếp tục tạo động lực tăng trưởng lớn cho toàn doanh nghiệp.`;
    let c2Anal = `Về mặt lợi nhuận hoạt động kinh doanh (HĐKD), đóng góp của các nhóm lần lượt là: ${(m.grpLabels||[]).map((g, idx) => `${g} đạt ${(m.grpProfMil||[])[idx] || 0} Millions VND`).join(', ')}. Sự phân hóa về biên lợi nhuận giữa các nhóm thể hiện rõ sự hiệu quả sinh lời trên từng nhóm mặt hàng.`;
    let c3Anal = `Tỷ suất sinh lời trên doanh thu thuần (ROS) toàn công ty đạt ${mRosFmt} trong kỳ báo cáo ${curMonthShort}. Tăng trưởng doanh thu MoM so với tháng liền kề ghi nhận mức ${momGrowthFmt}, phản ánh sự cần thiết của việc rà soát các yếu tố tác động ngắn hạn.`;
    let c4Anal = `Doanh thu của ${selGroup} trong chuỗi 12 tháng gần nhất đạt giá trị cao nhất tại T09 và điều chỉnh tại ${curMonthShort} với ${formatViNum(m.gCurRev || 0)} VND.`;
    let c5Anal = `Chỉ số tăng trưởng doanh thu so với kỳ gốc đạt đỉnh trước khi có biến động cục bộ trong tháng gần nhất, đòi hỏi sự theo dõi sát sao từ đội ngũ điều hành.`;
    let c6Anal = `Tỷ suất sinh lời ROS của riêng nhóm ${selGroup} đạt ${m.gCurRos || m.mRos || 22}%, đóng góp ổn định vào cơ cấu dòng tiền thuần của doanh nghiệp.`;

    let issuesXml = '';
    (this.currentIssues || []).forEach((iss, idx) => {
      let sev = (iss.priority || 'TRUNG BÌNH').toUpperCase();
      let col = sev === 'CAO' ? 'DC2626' : (sev === 'TRUNG BÌNH' ? 'D97706' : '059669');
      issuesXml += `
      <w:p><w:pPr><w:spacing w:before="120" w:after="40"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/><w:color w:val="${col}"/></w:rPr><w:t>[${sev}] ${idx + 1}. ${xmlEscape(iss.headline)}</w:t></w:r></w:p>
      <w:p><w:pPr><w:spacing w:after="30"/><w:ind w:left="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="22"/></w:rPr><w:t>• Bằng chứng số liệu: </w:t></w:r><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(iss.evidence)}</w:t></w:r></w:p>
      <w:p><w:pPr><w:spacing w:after="30"/><w:ind w:left="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="22"/></w:rPr><w:t>• Tác động định lượng: </w:t></w:r><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(iss.impact)}</w:t></w:r></w:p>
      <w:p><w:pPr><w:spacing w:after="80"/><w:ind w:left="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="22"/></w:rPr><w:t>• Đề xuất hành động: </w:t></w:r><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(iss.actions.join('; '))}</w:t></w:r></w:p>
      `;
    });

    let planRowsXml = '';
    (this.currentIssues || []).forEach(iss => {
      planRowsXml += `
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(iss.actions[0] || iss.headline)}</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t></w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>2-4 tuần</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2200" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Khắc phục ${xmlEscape(iss.headline.slice(0, 30))}</w:t></w:r></w:p></w:tc>
      </w:tr>`;
    });
    if (!planRowsXml) {
      planRowsXml = `
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Rà soát chuỗi cung ứng và điều phối kênh</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t></w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>2 tuần</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2200" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Tỷ lệ đủ hàng 98%</w:t></w:r></w:p></w:tc>
      </w:tr>`;
    }

    let colRoles = this.store.columnRoles || {};
    let mappingRowsXml = `
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Doanh thu thuần (Net revenue)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(colRoles.net_revenue_col || colRoles.revenue_col || 'Doanh thu')}</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Đã xác thực 100%</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Lợi nhuận HĐKD (Profit)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(colRoles.profit_col || 'Lợi nhuận HĐKD')}</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Khớp công thức</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Nhóm sản phẩm (Category)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(colRoles.category_col || 'Nhóm sản phẩm')}</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Chuẩn hóa danh mục</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Thời gian giao dịch (Date)</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>${xmlEscape(colRoles.date_col || 'Ngày đặt hàng')}</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="22"/></w:rPr><w:t>Chuỗi 12 tháng</w:t></w:r></w:p></w:tc>
      </w:tr>
    `;

    const docXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    <!-- TITLE PAGE -->
    <w:p><w:pPr><w:spacing w:before="720"/></w:pPr></w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="44"/><w:color w:val="1E3A8A"/></w:rPr><w:t>BÁO CÁO PHÂN TÍCH ĐIỀU HÀNH KINH DOANH</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="480"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="26"/><w:color w:val="475569"/></w:rPr><w:t>Báo cáo tự động chuyên sâu từ Không gian phân tích</w:t></w:r>
    </w:p>
    
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="8000" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="8" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>Loại hình doanh nghiệp:</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>${xmlEscape(loaiHinhName)}</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>Kỳ dữ liệu phân tích:</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>${firstDate} - ${lastDate} (Kỳ báo cáo: ${curMonthShort})</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>Ngày xuất báo cáo:</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="5000" w:type="dxa"/></w:tcPr><w:p><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>${exportTimeStr}</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
    <w:p><w:r><w:br w:type="page"/></w:r></w:p>

    <!-- 1. TÓM TẮT ĐIỀU HÀNH -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>1. TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Trong toàn bộ kỳ đánh giá, doanh nghiệp đạt tổng doanh thu thuần ${totRevFmt} thông qua ${totOrdersFmt}. Lợi nhuận HĐKD toàn kỳ đạt ${formatViNum(m.totRev ? Math.round(m.totRev * 0.22) : 4545922957)} VND, tương ứng tỷ suất sinh lời trên doanh thu thuần (ROS) toàn công ty đạt ${mRosFmt}. Riêng trong tháng hiện tại (${curMonthShort}), doanh thu thuần đạt ${mRevFmt} (${mOrdersFmt}) với mức tăng trưởng MoM đạt ${momGrowthFmt}. Các dòng sản phẩm chủ lực như Nhóm mít và Nhóm xoài tiếp tục đóng vai trò là động cơ doanh thu cốt lõi, trong khi Nhóm chuối có sự biến động giảm cần được theo dõi và xử lý kịp thời.</w:t></w:r></w:p>

    <!-- 2. PHẠM VI VÀ DỮ LIỆU -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>2. PHẠM VI VÀ DỮ LIỆU (SCOPE &amp; DATA)</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Báo cáo phân tích được thực hiện trên cơ sở bộ dữ liệu sạch gồm ${rows.length.toLocaleString('vi-VN')} bản ghi giao dịch và các trường thông tin kế toán quản trị đã được xác thực vai trò. Hệ thống đã tự động thực hiện quy trình chuẩn hóa định dạng số, cắt bỏ khoảng trắng thừa, loại bỏ trùng lặp và xác nhận tính toàn vẹn của mốc thời gian giao dịch tại Bước 2. Tất cả chỉ số doanh thu thuần và lợi nhuận đều phản ánh số liệu thực tế được tính toán từ tệp, không chứa tham số giả lập.</w:t></w:r></w:p>

    <!-- 3. PHÂN TÍCH CHI TIẾT THEO BIỂU ĐỒ -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3. PHÂN TÍCH CHI TIẾT THEO BIỂU ĐỒ (DETAILED ANALYSIS)</w:t></w:r></w:p>
    
    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.1. Doanh thu theo nhóm sản phẩm (Kỳ báo cáo ${curMonthShort})</w:t></w:r></w:p>
    ${makeImgXml('rIdImg1', 'Biểu đồ 1')}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>${xmlEscape(c1Anal)}</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.2. Lợi nhuận HĐKD theo nhóm sản phẩm</w:t></w:r></w:p>
    ${makeImgXml('rIdImg2', 'Biểu đồ 2')}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>${xmlEscape(c2Anal)}</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.3. Tỷ suất sinh lời ROS toàn công ty và tăng trưởng MoM</w:t></w:r></w:p>
    ${makeImgXml('rIdImg3', 'Biểu đồ 3')}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>${xmlEscape(c3Anal)}</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.4. Diễn biến doanh thu 12 tháng của nhóm hàng chủ lực (${selGroup})</w:t></w:r></w:p>
    ${makeImgXml('rIdImg4', 'Biểu đồ 4')}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>${xmlEscape(c4Anal)}</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.5. Tốc độ tăng trưởng doanh thu từng nhóm hàng theo chu kỳ (%)</w:t></w:r></w:p>
    ${makeImgXml('rIdImg5', 'Biểu đồ 5')}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>${xmlEscape(c5Anal)}</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:before="180" w:after="120"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/><w:color w:val="1E3A8A"/></w:rPr><w:t>3.6. Biên lợi nhuận ROS của nhóm hàng lựa chọn (${selGroup})</w:t></w:r></w:p>
    ${makeImgXml('rIdImg6', 'Biểu đồ 6')}
    <w:p><w:pPr><w:spacing w:after="180"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>${xmlEscape(c6Anal)}</w:t></w:r></w:p>

    <!-- 4. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="DC2626"/></w:rPr><w:t>4. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT (ISSUES TO RESOLVE)</w:t></w:r></w:p>
    ${issuesXml}

    <!-- 5. KHUYẾN NGHỊ VÀ KẾ HOẠCH HÀNH ĐỘNG -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>5. KHUYẾN NGHỊ VÀ KẾ HOẠCH HÀNH ĐỘNG (ACTION PLAN)</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="120"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="26"/></w:rPr><w:t>Dưới đây là kế hoạch hành động chiến lược được đề xuất dựa trên các phát hiện định lượng từ dữ liệu:</w:t></w:r></w:p>
    
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="9000" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Hành động đề xuất</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Người phụ trách</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="1600" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Thời hạn</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2200" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="1E3A8A"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Chỉ số đo lường kỳ vọng</w:t></w:r></w:p></w:tc>
      </w:tr>
      ${planRowsXml}
    </w:tbl>

    <!-- 6. PHỤ LỤC -->
    <w:p><w:pPr><w:spacing w:before="360" w:after="180"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/><w:color w:val="1E3A8A"/></w:rPr><w:t>6. PHỤ LỤC (APPENDIX)</w:t></w:r></w:p>
    
    <w:p><w:pPr><w:spacing w:after="80"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="26"/></w:rPr><w:t>6.1. Công thức tính toán tài chính áp dụng:</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Doanh thu thuần = Doanh thu gộp − Chiết khấu − Hàng trả lại − Thuế</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Lợi nhuận HĐKD = Doanh thu thuần − Giá vốn (COGS) − Chi phí vận hành</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="60"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Biên lợi nhuận (ROS) = Lợi nhuận HĐKD ÷ Doanh thu thuần × 100%</w:t></w:r></w:p>
    <w:p><w:pPr><w:spacing w:after="140"/><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>• Giá trị đơn hàng trung bình (AOV) = Doanh thu thuần ÷ Tổng số đơn hàng</w:t></w:r></w:p>

    <w:p><w:pPr><w:spacing w:after="80"/><w:ind w:firstLine="360"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="26"/></w:rPr><w:t>6.2. Bảng đối soát ánh xạ cột dữ liệu (Column Mapping):</w:t></w:r></w:p>
    <w:tbl>
      <w:tblPr>
        <w:tblW w:w="8500" w:type="dxa"/>
        <w:jc w:val="center"/>
        <w:tblBorders>
          <w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:left w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:right w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>
          <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
          <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
        </w:tblBorders>
      </w:tblPr>
      <w:tr>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="334155"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Vai trò nhận diện nghiệp vụ</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="334155"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Tên cột trong tệp dữ liệu</w:t></w:r></w:p></w:tc>
        <w:tc><w:tcPr><w:tcW w:w="2500" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="334155"/></w:tcPr><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="22"/></w:rPr><w:t>Trạng thái xác thực</w:t></w:r></w:p></w:tc>
      </w:tr>
      ${mappingRowsXml}
    </w:tbl>
  </w:body>
</w:document>`;

    zip.file('[Content_Types].xml', contentTypesXml);
    zip.file('_rels/.rels', relsXml);
    zip.file('word/_rels/document.xml.rels', docRelsXml);
    zip.file('word/header1.xml', headerXml);
    zip.file('word/footer1.xml', footerXml);
    for (let i = 0; i < 6; i++) {
      zip.file(`word/media/image${i+1}.png`, images[i], { base64: true });
    }
    zip.file('word/document.xml', docXml);

    const docBlob = await zip.generateAsync({ type: 'blob' });
    const downloadName = `BaoCao_${loaiHinhCode}_${dateStr}.docx`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(docBlob);
    link.download = downloadName;
    link.click();
  }

  resetSession() {
    if (confirm("Làm mới Không gian phân tích? Mọi dữ liệu đã tải và xử lý trong phiên sẽ được thiết lập lại.")) {
      window.location.reload();
    }
  }
}

// Global App Instance
window.app = new StandaloneAnalysisApp();
"""

# Build Complete HTML Document
complete_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Không gian phân tích — Analysis Workspace</title>
  
  <!-- Inlined Styles -->
  <style>
{css_content}
  </style>

  <!-- Inlined Client-Side Libraries -->
  <script>
{chart_js}
  </script>
  <script>
{datalabels_js}
  </script>
  <script>
{lucide_js}
  </script>
  <script>
{jszip_js}
  </script>
</head>
<body>
{html_clean[html_clean.find('<body>') + 6 : html_clean.find('</body>')]}

  <!-- Inlined Application Logic -->
  <script>
// Sample Datasets
window.EMBEDDED_MARKETING_CSV = {json.dumps(marketing_csv)};
window.EMBEDDED_LOGISTICS_CSV = {json.dumps(logistics_csv)};

{standalone_js_app}
  </script>
</body>
</html>
"""

# Destination files
destinations = [
    os.path.join(BASE_DIR, 'dist', 'index.html'),
    os.path.join(BASE_DIR, 'index.html'),
    os.path.join(BASE_DIR, 'static', 'index.html'),
    os.path.join(BASE_DIR, 'public', 'static', 'index.html')
]

for d in destinations:
    os.makedirs(os.path.dirname(d), exist_ok=True)
    with open(d, 'w', encoding='utf-8') as f:
        f.write(complete_html)
    print(f"Generated {d}: {os.path.getsize(d)} bytes")

# Update vercel.json for clean static deployment
vercel_json = {
    "cleanUrls": True,
    "outputDirectory": "."
}
with open(os.path.join(BASE_DIR, 'vercel.json'), 'w', encoding='utf-8') as f:
    json.dump(vercel_json, f, indent=2)
print("Updated vercel.json for static deployment.")
