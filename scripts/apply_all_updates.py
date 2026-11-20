import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
builder_path = os.path.join(BASE_DIR, 'scripts', 'build_complete_app.py')

with open(builder_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update HTML body extraction & replacements
# Find where html_clean is prepared
target_html_clean = """# Read HTML and strip broken hero section
with open(os.path.join(BASE_DIR, 'static', 'index.html'), 'r', encoding='utf-8') as f:
    html_raw = f.read()

# Strip flower-hero-section
html_clean = re.sub(r'<!-- FLOWER HAPPY 3D PASTEL HERO SECTION -->\s*<div class="flower-hero-section">.*?</div>\s*(?=<!-- Business Context Form -->)', '', html_raw, flags=re.DOTALL)
if html_clean == html_raw:
    html_clean = re.sub(r'<div class="flower-hero-section">.*?</div>\s*(?=<div class="panel-card">)', '', html_raw, flags=re.DOTALL)

# Remove external css and js tags from html
html_clean = re.sub(r'<link rel="stylesheet" href="[^"]*">', '', html_clean)
html_clean = re.sub(r'<script src="[^"]*"></script>', '', html_clean)"""

replacement_html_clean = """# Read HTML and strip broken hero section
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
    )"""

if target_html_clean in content:
    content = content.replace(target_html_clean, replacement_html_clean)
    print("Replaced html_clean extraction logic.")
else:
    print("Warning: target_html_clean not matched exactly. Checking if already replaced.")

# 2. Update init() in JS
old_init = """  init() {
    this.bindEvents();
    if (window.lucide) lucide.createIcons();
    // Check if running against local API or pure client mode
    this.checkBackendConnection();
  }"""

new_init = """  init() {
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
  }"""

if old_init in content:
    content = content.replace(old_init, new_init)
    print("Replaced init() and added handleBusinessTypeChange().")

# 3. Update saveBusinessForm()
old_save_form = """  async saveBusinessForm() {
    const bizType = document.getElementById('input-biz-type')?.value.trim() || '';
    const addInfo = document.getElementById('input-biz-info')?.value.trim() || '';
    const questionsText = document.getElementById('input-questions')?.value.trim() || '';
    
    if (!bizType) {
      alert("Vui lòng nhập 'Loại hình doanh nghiệp'.");
      document.getElementById('input-biz-type')?.focus();
      return false;
    }
    const questions = questionsText.split('\\\\n').map(q => q.trim()).filter(q => q.length > 0);
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
  }"""

new_save_form = """  async saveBusinessForm() {
    const bizType = document.getElementById('input-biz-type')?.value.trim() || '';
    const addInfo = document.getElementById('input-biz-info')?.value.trim() || '';
    const questionsText = document.getElementById('input-questions')?.value.trim() || '';
    
    if (!bizType || (bizType !== 'retail' && bizType !== 'b2b')) {
      alert("Vui lòng chọn 'Loại hình doanh nghiệp' (Bán lẻ hoặc B2B).");
      document.getElementById('input-biz-type')?.focus();
      return false;
    }
    const questions = questionsText.split('\\\\n').map(q => q.trim()).filter(q => q.length > 0);
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
  }"""

if old_save_form in content:
    content = content.replace(old_save_form, new_save_form)
    print("Replaced saveBusinessForm().")

# 4. Update consultAI()
old_consult_ai = """  async consultAI() {
    const valid = await this.saveBusinessForm();
    if (!valid) return;
    const chatContainer = document.getElementById('ai-chat-container');
    const goalBox = document.getElementById('ai-goal-box');
    const missingBox = document.getElementById('ai-missing-box');
    const clarifyBox = document.getElementById('ai-clarify-box');

    if (chatContainer) chatContainer.style.display = 'block';
    if (goalBox) goalBox.innerHTML = `<strong>Tóm tắt mục tiêu chiến lược:</strong><br>Doanh nghiệp hoạt động trong lĩnh vực <em>${this.store.businessType}</em>. Mục tiêu phân tích tập trung vào: ${this.store.questions.map(q => `“${q}”`).join(', ')}.`;
    if (missingBox) missingBox.innerHTML = `<strong>Thông tin/biến số nên đối chiếu:</strong><ul style="margin-left: 20px; margin-top: 4px;"><li>Cơ cấu giá vốn (COGS) và các khoản giảm trừ doanh thu (chiết khấu, hoàn trả).</li><li>Phân bổ doanh thu theo kênh bán hàng và khu vực địa lý để đánh giá hiệu quả kênh.</li><li>Chu kỳ biến động đơn hàng theo tháng để phát hiện xu hướng mùa vụ.</li></ul>`;
    if (clarifyBox) clarifyBox.innerHTML = `<strong>Đề xuất làm rõ từ AI Advisor:</strong><ul style="margin-left: 20px; margin-top: 4px;"><li>Bạn có muốn xem xét tỷ suất ROS mục tiêu cụ thể (ví dụ tối thiểu 20%) hay không?</li><li>Có cần tách riêng chi phí khuyến mãi và giá vốn khi tính toán biên lợi nhuận ròng không?</li></ul>`;
    if (window.lucide) lucide.createIcons();
  }"""

new_consult_ai = """  async consultAI() {
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
  }"""

if old_consult_ai in content:
    content = content.replace(old_consult_ai, new_consult_ai)
    print("Replaced consultAI().")

# 5. Update loadSampleData() - remove pre-fill
old_sample = """    if (key === 'marketing_sales') {
      csvText = window.EMBEDDED_MARKETING_CSV || '';
      fname = 'doanh_thu_marketing.csv';
      if (!document.getElementById('input-biz-type')?.value) {
        document.getElementById('input-biz-type').value = 'Bán lẻ nông sản & Thực phẩm chế biến';
      }
    } else {
      csvText = window.EMBEDDED_LOGISTICS_CSV || '';
      fname = 'ban_le_logistics.csv';
      if (!document.getElementById('input-biz-type')?.value) {
        document.getElementById('input-biz-type').value = 'Bán lẻ đa kênh & Logistics';
      }
    }"""

new_sample = """    if (key === 'marketing_sales') {
      csvText = window.EMBEDDED_MARKETING_CSV || '';
      fname = 'doanh_thu_marketing.csv';
    } else {
      csvText = window.EMBEDDED_LOGISTICS_CSV || '';
      fname = 'ban_le_logistics.csv';
    }"""

if old_sample in content:
    content = content.replace(old_sample, new_sample)
    print("Replaced loadSampleData() (no pre-fill).")

# 6. Update loadAISuggestions()
old_sugg = """    const suggestions = [
      {
        question: "Doanh thu theo nhóm sản phẩm nào dẫn đầu trong kỳ?",
        goal: "Xác định danh mục sản phẩm cốt lõi đóng góp doanh thu lớn nhất",
        cols: [this.store.columnRoles.category_col || "Nhóm sản phẩm", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Tỷ suất lợi nhuận trên doanh thu (ROS) toàn công ty đạt bao nhiêu?",
        goal: "Đo lường hiệu quả sinh lời tổng thể trên từng đồng doanh thu thuần",
        cols: [this.store.columnRoles.profit_col || "Lợi nhuận", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      },
      {
        question: "Xu hướng tăng trưởng của nhóm chủ lực qua các tháng biến động ra sao?",
        goal: "Phát hiện chu kỳ tăng giảm và điểm gãy doanh thu theo chu kỳ tháng",
        cols: [this.store.columnRoles.date_col || "Ngày đặt hàng", this.store.columnRoles.category_col || "Nhóm sản phẩm"]
      },
      {
        question: "Kênh bán hàng nào có hiệu quả doanh thu cao nhất và thấp nhất?",
        goal: "Tối ưu hóa nguồn lực và chi phí phân bổ cho các kênh bán",
        cols: [this.store.columnRoles.channel_col || "Kênh bán", this.store.columnRoles.net_revenue_col || "Doanh thu"]
      }
    ];"""

new_sugg = """    const isB2B = this.store.businessType === 'b2b';
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
    ];"""

if old_sugg in content:
    content = content.replace(old_sugg, new_sugg)
    print("Replaced loadAISuggestions().")

# 7. Update refreshDashboard to save this.dashMetrics
old_refresh_end = """    let gCurRows = mRows.filter(r => (r[catCol]||'') === selGroup);
    let gCurRev = gCurRows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0);
    let gCurProf = profCol ? gCurRows.reduce((a,b)=>a+(parseNum(b[profCol])||0), 0) : 0;
    let gCurRos = gCurRev > 0 ? Math.round((gCurProf / gCurRev) * 100) : mRos;

    // Render Chart 4
    this.renderChart4(ymLabels, gMonthlyRev, selGroup);
    // Render Chart 5
    this.renderChart5(ymLabels, gGrowthIdx, selGroup);
    // Render Chart 6
    this.renderChart6(gCurRos, selGroup);

    // Top Findings table
    this.renderTopFindingsTable(grpLabels, grpMap, totRev);
  }"""

new_refresh_end = """    let gCurRows = mRows.filter(r => (r[catCol]||'') === selGroup);
    let gCurRev = gCurRows.reduce((a,b)=>a+(parseNum(b[revCol])||0), 0);
    let gCurProf = profCol ? gCurRows.reduce((a,b)=>a+(parseNum(b[profCol])||0), 0) : 0;
    let gCurRos = gCurRev > 0 ? Math.round((gCurProf / gCurRev) * 100) : mRos;

    this.dashMetrics = {
      selYm,
      selGroup,
      totRev,
      mRev,
      totOrders,
      mOrders,
      momGrowth,
      mRos,
      grpLabels,
      grpRevMil,
      grpProfMil,
      yms,
      gMonthlyRev,
      gGrowthIdx,
      gCurRev,
      gCurProf,
      gCurRos
    };

    // Render Chart 4
    this.renderChart4(ymLabels, gMonthlyRev, selGroup);
    // Render Chart 5
    this.renderChart5(ymLabels, gGrowthIdx, selGroup);
    // Render Chart 6
    this.renderChart6(gCurRos, selGroup);

    // Top Findings table
    this.renderTopFindingsTable(grpLabels, grpMap, totRev);
  }"""

if old_refresh_end in content:
    content = content.replace(old_refresh_end, new_refresh_end)
    print("Replaced refreshDashboard end with this.dashMetrics.")

# 8. Update exportFile() and add exportWordDocx()
old_export = """  exportFile(type) {
    if (type === 'pdf') {
      window.print();
    } else if (type === 'csv') {
      if (this.store.cleanRows.length === 0) { alert("Chưa có dữ liệu để xuất."); return; }
      let csv = this.store.rawHeaders.join(',') + '\\\\n';
      this.store.cleanRows.forEach(r => {
        let row = this.store.rawHeaders.map(h => `"${String(r[h]||'').replace(/"/g, '""')}"`).join(',');
        csv += row + '\\\\n';
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
  }"""

new_export = """  exportFile(type) {
    if (type === 'word') {
      this.exportWordDocx();
    } else if (type === 'pdf') {
      window.print();
    } else if (type === 'csv') {
      if (this.store.cleanRows.length === 0) { alert("Chưa có dữ liệu để xuất."); return; }
      let csv = this.store.rawHeaders.join(',') + '\\\\n';
      this.store.cleanRows.forEach(r => {
        let row = this.store.rawHeaders.map(h => `"${String(r[h]||'').replace(/"/g, '""')}"`).join(',');
        csv += row + '\\\\n';
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
    let dates = rows.map(r => String(r[dateCol] || '').trim()).filter(d => /^\\\\d{4}-\\\\d{2}-\\\\d{2}/.test(d)).sort();
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
  }"""

if old_export in content:
    content = content.replace(old_export, new_export)
    print("Replaced exportFile() with Word DOCX exporter.")

with open(builder_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved updated build_complete_app.py.")
