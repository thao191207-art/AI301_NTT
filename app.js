// Analysis Workspace — "Không gian phân tích" Frontend Application

class AnalysisApp {
  constructor() {
    this.currentStep = 1;
    this.stepUnlocked = { 1: true, 2: false, 3: false, 4: false };
    this.state = null;
    this.chartInstances = {};
    this.dashboardData = null;
    this.currentIssues = [];
    this.chartTypeOverrides = {
      chart1: 'bar',
      chart2: 'bar',
      chart4: 'bar',
      chart5: 'line'
    };
    
    // Register ChartDataLabels plugin if available
    if (window.ChartDataLabels) {
      Chart.register(ChartDataLabels);
    }

    // Register Center Text plugin for doughnut charts
    const centerTextPlugin = {
      id: 'centerTextPlugin',
      beforeDraw(chart) {
        if (chart.config.type === 'doughnut') {
          const { width, height, ctx } = chart;
          ctx.restore();
          const fontSize = (height / 114).toFixed(2);
          ctx.font = `bold ${fontSize}em Inter, sans-serif`;
          ctx.textBaseline = 'middle';
          ctx.fillStyle = '#0F172A';

          const text = chart.config.options.plugins.centerText?.text || '';
          const textX = Math.round((width - ctx.measureText(text).width) / 2);
          const textY = height / 2;

          ctx.fillText(text, textX, textY);
          ctx.save();
        }
      }
    };
    Chart.register(centerTextPlugin);

    this.init();
  }

  async init() {
    this.bindEvents();
    await this.fetchState();
    if (window.lucide) {
      lucide.createIcons();
    }
  }

  bindEvents() {
    // Validate question line count live
    const qInput = document.getElementById('input-questions');
    if (qInput) {
      qInput.addEventListener('input', () => {
        const lines = qInput.value.split('\n').filter(l => l.trim().length > 0);
        const badge = document.getElementById('question-count-badge');
        if (badge) {
          badge.textContent = `${lines.length}/8 câu`;
          if (lines.length > 8) {
            badge.style.color = '#DC2626';
          } else {
            badge.style.color = '#2563EB';
          }
        }
      });
    }
  }

  async fetchState() {
    try {
      const res = await fetch('/api/state');
      if (res.ok) {
        this.state = await res.json();
        this.stepUnlocked = this.state.step_unlocked;
        this.updateSidebarStatus();
        this.updateStepLockUI();
        if (this.state.has_data && this.state.current_step > 1) {
          this.goToStep(this.state.current_step);
        }
      }
    } catch (e) {
      console.error("Fetch state error:", e);
    }
  }

  updateSidebarStatus() {
    const dot = document.getElementById('status-dot');
    const badge = document.getElementById('sidebar-data-status');
    if (this.state && this.state.has_data) {
      dot.classList.add('active');
      const rowCount = this.state.row_count ? this.state.row_count.toLocaleString('vi-VN') : '0';
      badge.textContent = `${this.state.source_name || 'Dữ liệu'} (${rowCount} dòng)`;
    } else {
      dot.classList.remove('active');
      badge.textContent = 'Chưa có dữ liệu';
    }
  }

  updateStepLockUI() {
    for (let step = 2; step <= 4; step++) {
      const btn = document.getElementById(`nav-step-step-${step}`) || document.getElementById(`nav-step-${step}`);
      const lock = document.getElementById(`lock-step-${step}`);
      if (btn) {
        if (this.stepUnlocked[step]) {
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

    try {
      await fetch('/api/step/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step })
      });
    } catch (e) {
      console.error(e);
    }

    this.currentStep = step;
    
    // Update Nav buttons
    for (let s = 1; s <= 4; s++) {
      const btn = document.getElementById(`nav-step-${s}`);
      const pane = document.getElementById(`step-${s}-content`);
      if (btn) {
        if (s === step) btn.classList.add('active');
        else btn.classList.remove('active');
      }
      if (pane) {
        pane.style.display = s === step ? 'block' : 'none';
      }
    }

    // Top title update
    const titles = {
      1: "Bước 1: Kết nối dữ liệu & Thiết lập bài toán",
      2: "Bước 2: Làm sạch, chuẩn hóa & Ánh xạ vai trò cột",
      3: "Bước 3: Phân tích thống kê & Trả lời bài toán",
      4: "Bước 4: Báo cáo điều hành & Xuất tệp"
    };
    document.getElementById('top-title').textContent = titles[step] || "";

    // Trigger step-specific load
    if (step === 2) {
      await this.loadCleanStep();
    } else if (step === 3) {
      await this.loadAnalyzeStep();
    } else if (step === 4) {
      await this.loadReportStep();
    }

    if (window.lucide) lucide.createIcons();
  }

  // -------------------------------------------------------------
  // Step 1: Connect handlers
  // -------------------------------------------------------------

  async saveBusinessForm() {
    const bizType = document.getElementById('input-biz-type').value.trim();
    const addInfo = document.getElementById('input-biz-info').value.trim();
    const questions = document.getElementById('input-questions').value.trim();

    const res = await fetch('/api/connect/form', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        business_type: bizType,
        additional_info: addInfo,
        questions: questions
      })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || "Lỗi lưu thông tin bài toán kinh doanh.");
      return false;
    }
    return true;
  }

  async consultAI() {
    const valid = await this.saveBusinessForm();
    if (!valid) return;

    const chatContainer = document.getElementById('ai-chat-container');
    const goalBox = document.getElementById('ai-goal-box');
    const missingBox = document.getElementById('ai-missing-box');
    const clarifyBox = document.getElementById('ai-clarify-box');

    chatContainer.style.display = 'block';
    goalBox.innerHTML = '<em>Đang kết nối AI để phân tích ngữ cảnh...</em>';
    missingBox.innerHTML = '';
    clarifyBox.innerHTML = '';

    try {
      const res = await fetch('/api/connect/ai-consult', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lỗi khi gọi AI");

      goalBox.innerHTML = `<strong>Tóm tắt mục tiêu chiến lược:</strong><br>${data.goal_restatement || ''}`;
      
      const missingHtml = (data.missing_information || []).map(m => `<li>${m}</li>`).join('');
      missingBox.innerHTML = `<strong>Thông tin/biến số nên bổ sung:</strong><ul style="margin-left: 20px; margin-top: 4px;">${missingHtml}</ul>`;

      const clarifyHtml = (data.clarifying_questions || []).map(q => `<li>${q}</li>`).join('');
      clarifyBox.innerHTML = `<strong>Câu hỏi làm rõ từ chuyên gia AI:</strong><ul style="margin-left: 20px; margin-top: 4px;">${clarifyHtml}</ul>`;
    } catch (e) {
      goalBox.innerHTML = `<span style="color: #DC2626;">Lỗi: ${e.message}</span>`;
    }
    if (window.lucide) lucide.createIcons();
  }

  async saveUserClarification() {
    const val = document.getElementById('input-user-clarify').value.trim();
    if (!val) {
      alert("Vui lòng nhập nội dung phản hồi.");
      return;
    }
    const res = await fetch('/api/connect/ai-clarify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clarification: val })
    });
    if (res.ok) {
      alert("Đã lưu phản hồi của bạn vào ngữ cảnh phân tích!");
    }
  }

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      alert("Dung lượng tệp vượt quá 50MB. Vui lòng chọn tệp nhỏ hơn.");
      return;
    }

    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('upload-progress-bar');
    progressContainer.style.display = 'block';
    progressBar.style.width = '30%';

    const formData = new FormData();
    formData.append('file', file);

    try {
      progressBar.style.width = '70%';
      const res = await fetch('/api/connect/upload', {
        method: 'POST',
        body: formData
      });
      progressBar.style.width = '100%';

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lỗi tải tệp");

      setTimeout(() => { progressContainer.style.display = 'none'; }, 500);
      this.renderPreview(data.metadata);
      await this.fetchState();
    } catch (e) {
      progressContainer.style.display = 'none';
      alert(`Lỗi: ${e.message}`);
    }
  }

  async loadSampleData(key) {
    try {
      const res = await fetch('/api/connect/sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lỗi tải dữ liệu mẫu");

      this.renderPreview(data.metadata);
      await this.fetchState();
    } catch (e) {
      alert(`Lỗi: ${e.message}`);
    }
  }

  async connectGoogleSheets() {
    const url = document.getElementById('input-sheets-url').value.trim();
    if (!url) {
      alert("Vui lòng dán liên kết Google Sheets.");
      return;
    }

    try {
      const res = await fetch('/api/connect/sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lỗi kết nối Google Sheets");

      this.renderPreview(data.metadata);
      await this.fetchState();
    } catch (e) {
      alert(e.message);
    }
  }

  renderPreview(metadata) {
    const card = document.getElementById('data-preview-card');
    card.style.display = 'block';
    
    document.getElementById('preview-title').textContent = `Xem trước: ${metadata.filename}`;
    const rowCount = metadata.row_count ? metadata.row_count.toLocaleString('vi-VN') : '0';
    document.getElementById('preview-meta-info').textContent = 
      `Tổng số: ${rowCount} dòng, ${metadata.column_count} cột | Định dạng: ${metadata.encoding.toUpperCase()} | Phân cách: '${metadata.delimiter}'`;

    const thead = document.getElementById('preview-thead');
    const tbody = document.getElementById('preview-tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    const cols = metadata.columns || [];
    let headerRow = '<tr>';
    cols.forEach(c => {
      const type = (metadata.column_types && metadata.column_types[c]) || 'text';
      headerRow += `<th>${c} <span style="font-size: 10px; font-weight: normal; color: #64748B;">(${type})</span></th>`;
    });
    headerRow += '</tr>';
    thead.innerHTML = headerRow;

    const previewRows = metadata.preview || [];
    previewRows.forEach(row => {
      let tr = '<tr>';
      cols.forEach(c => {
        const val = row[c] !== undefined && row[c] !== null ? row[c] : '';
        tr += `<td>${val}</td>`;
      });
      tr += '</tr>';
      tbody.innerHTML += tr;
    });

    card.scrollIntoView({ behavior: 'smooth' });
    this.loadAISuggestions();
  }

  async completeStep1() {
    const valid = await this.saveBusinessForm();
    if (!valid) return;

    try {
      const res = await fetch('/api/connect/complete', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      this.stepUnlocked[2] = true;
      this.updateStepLockUI();
      await this.goToStep(2);
    } catch (e) {
      alert(e.message);
    }
  }

  // -------------------------------------------------------------
  // Step 2: Clean handlers
  // -------------------------------------------------------------

  async loadCleanStep() {
    try {
      const res = await fetch('/api/clean/issues');
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      this.renderCleanIssues(data.issues);
      this.renderColumnRoles(data.columns, data.column_roles);
      this.renderAuditLog(data.audit_log);
      await this.renderColumnMappingTable();
    } catch (e) {
      console.error(e);
    }
  }

  renderCleanIssues(issues) {
    const container = document.getElementById('issues-list-container');
    container.innerHTML = '';

    const desc = document.getElementById('clean-summary-desc');
    desc.textContent = `Phát hiện ${issues.summary_count} vấn đề về định dạng và chất lượng trên tổng số ${issues.total_rows.toLocaleString('vi-VN')} dòng.`;

    if (issues.summary_count === 0) {
      container.innerHTML = '<div style="padding: 16px; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; color: #166534;">Dữ liệu rất sạch sẽ! Không phát hiện ô trống, dòng trùng hay lỗi định dạng lớn.</div>';
      return;
    }

    // 1. Duplicates
    if (issues.duplicates_count > 0) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Dòng trùng lặp hoàn toàn:</strong> ${issues.duplicates_count} dòng
            <p style="font-size: 12px; color: #64748B;">Có ${issues.duplicates_count} dòng bị lặp lại tất cả các giá trị.</p>
          </div>
          <div>
            <button class="btn btn-secondary" onclick="app.applyCleanAction('drop_duplicates')">
              Xóa ${issues.duplicates_count} dòng trùng
            </button>
          </div>
        </div>
      `;
    }

    // 2. Missing values
    for (const [col, mInfo] of Object.entries(issues.missing_values || {})) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Ô trống ở cột '${col}':</strong> ${mInfo.count} ô (${mInfo.percentage}%)
            <p style="font-size: 12px; color: #64748B;">Chọn thao tác điền hoặc xóa để tránh ảnh hưởng phép tính.</p>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <select id="missing-action-${col}" class="form-select" style="width: auto;">
              <option value="zero">Điền số 0</option>
              <option value="mean">Điền trung bình (Mean)</option>
              <option value="median">Điền trung vị (Median)</option>
              <option value="mode">Điền giá trị phổ biến (Mode)</option>
              <option value="drop_rows">Xóa dòng chứa ô trống</option>
              <option value="drop_col">Xóa hẳn cột này</option>
            </select>
            <button class="btn btn-secondary" onclick="app.handleMissingAction('${col}')">Áp dụng</button>
          </div>
        </div>
      `;
    }

    // 3. Numeric in text
    for (const [col, nInfo] of Object.entries(issues.numeric_as_text || {})) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Cột số chứa ký hiệu văn bản: '${col}'</strong>
            <p style="font-size: 12px; color: #64748B;">Chứa dấu phân cách, tiền tệ hoặc % (VD: ${nInfo.examples.join(', ')})</p>
          </div>
          <div>
            <button class="btn btn-secondary" onclick="app.applyCleanAction('standardize_numeric', '${col}')">
              Chuyển đổi sang số chuẩn
            </button>
          </div>
        </div>
      `;
    }

    // 4. Whitespace and casing
    for (const [col, cInfo] of Object.entries(issues.casing_inconsistencies || {})) {
      container.innerHTML += `
        <div class="issue-card">
          <div>
            <strong>Khoảng trắng thừa & chữ hoa thường: '${col}'</strong>
            <p style="font-size: 12px; color: #64748B;">Phát hiện khoảng trắng đầu/cuối hoặc cách viết hoa không đồng nhất.</p>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary" onclick="app.applyCleanAction('trim_and_case', '${col}', {case: 'trim'})">
              Cắt khoảng trắng
            </button>
            <button class="btn btn-secondary" onclick="app.applyCleanAction('trim_and_case', '${col}', {case: 'title'})">
              Chuyển Title Case
            </button>
          </div>
        </div>
      `;
    }

    if (window.lucide) lucide.createIcons();
  }

  renderColumnRoles(columns, currentRoles) {
    const grid = document.getElementById('column-roles-grid');
    grid.innerHTML = '';

    const roleDefinitions = [
      { key: 'revenue_col', label: 'Cột Doanh thu (Bắt buộc)', required: true },
      { key: 'category_col', label: 'Cột Nhóm sản phẩm / Ngành hàng', required: true },
      { key: 'date_col', label: 'Cột Ngày / Thời gian', required: true },
      { key: 'profit_col', label: 'Cột Lợi nhuận HĐKD', required: false },
      { key: 'order_col', label: 'Cột Mã đơn hàng', required: false },
      { key: 'channel_col', label: 'Cột Kênh bán / Khu vực', required: false },
      { key: 'cost_col', label: 'Cột Chi phí vốn', required: false }
    ];

    roleDefinitions.forEach(r => {
      let optionsHtml = '<option value="">-- Chưa gán --</option>';
      columns.forEach(c => {
        const isSel = currentRoles && currentRoles[r.key] === c;
        optionsHtml += `<option value="${c}" ${isSel ? 'selected' : ''}>${c}</option>`;
      });

      grid.innerHTML += `
        <div class="form-group" style="background: #F8FAFC; padding: 12px; border-radius: 8px; border: 1px solid #E2E8F0;">
          <label class="form-label">${r.label} ${r.required ? '<span class="req">*</span>' : ''}</label>
          <select class="form-select" onchange="app.updateSingleRole('${r.key}', this.value)">
            ${optionsHtml}
          </select>
        </div>
      `;
    });
  }

  renderAuditLog(logs) {
    const tbody = document.getElementById('audit-log-tbody');
    tbody.innerHTML = '';
    if (!logs || logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #94A3B8;">Chưa có thao tác làm sạch nào được thực hiện.</td></tr>';
      return;
    }
    logs.forEach(log => {
      tbody.innerHTML += `
        <tr>
          <td>${log.id}</td>
          <td>${log.timestamp}</td>
          <td><strong>${log.action_name}</strong></td>
          <td>${log.column}</td>
          <td>${log.details}</td>
          <td>${log.before_rows.toLocaleString('vi-VN')}</td>
          <td>${log.after_rows.toLocaleString('vi-VN')}</td>
        </tr>
      `;
    });
  }

  async handleMissingAction(col) {
    const sel = document.getElementById(`missing-action-${col}`);
    const action = sel.value;
    if (action === 'drop_rows') {
      await this.applyCleanAction('drop_missing_rows', col);
    } else if (action === 'drop_col') {
      await this.applyCleanAction('drop_column', col);
    } else {
      await this.applyCleanAction('fill_missing', col, { method: action });
    }
  }

  async applyCleanAction(actionType, column = null, params = {}) {
    try {
      const res = await fetch('/api/clean/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_type: actionType, column, params })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      this.renderCleanIssues(data.issues);
      this.renderAuditLog(data.audit_log);
      await this.renderColumnMappingTable();
      await this.fetchState();
    } catch (e) {
      alert(`Lỗi: ${e.message}`);
    }
  }

  async autoCleanAll() {
    try {
      const res = await fetch('/api/clean/auto', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      this.renderCleanIssues(data.issues);
      this.renderAuditLog(data.audit_log);
      await this.renderColumnMappingTable();
      await this.fetchState();
      alert("Đã tự động loại bỏ dòng trùng, chuẩn hóa kiểu số và cắt khoảng trắng thành công!");
    } catch (e) {
      alert(`Lỗi: ${e.message}`);
    }
  }

  async updateSingleRole(roleKey, colValue) {
    const payload = {};
    payload[roleKey] = colValue;
    await fetch('/api/clean/roles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }

  async completeStep2() {
    try {
      const res = await fetch('/api/clean/complete', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      this.stepUnlocked[3] = true;
      this.updateStepLockUI();
      await this.goToStep(3);
    } catch (e) {
      alert(e.message);
    }
  }

  // -------------------------------------------------------------
  // Step 3: Analyze handlers
  // -------------------------------------------------------------

  async loadAnalyzeStep() {
    await this.executeAnalysis();
  }

  async executeAnalysis() {
    try {
      const res = await fetch('/api/analyze/run', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      const results = data.analysis_results;
      this.renderQuestionAnswers(results.answers);
      this.renderNumericStats(results.summary_stats.numeric_columns);
      this.renderAnomalies(results.anomalies);
      
      this.stepUnlocked[4] = true;
      this.updateStepLockUI();
    } catch (e) {
      alert(`Lỗi phân tích: ${e.message}`);
    }
  }

  renderQuestionAnswers(answers) {
    const container = document.getElementById('questions-answers-container');
    container.innerHTML = '';
    if (!answers || answers.length === 0) {
      container.innerHTML = '<p style="color: #64748B;">Chưa có câu hỏi nào được giải quyết.</p>';
      return;
    }
    answers.forEach((ans, idx) => {
      container.innerHTML += `
        <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; border-left: 4px solid #2563EB;">
          <h4 style="font-size: 14px; font-weight: 700; color: #1E3A8A; margin-bottom: 6px;">
            ${idx + 1}. ${ans.question}
          </h4>
          <p style="font-size: 13.5px; color: #1E293B; line-height: 1.6;">
            ${ans.answer}
          </p>
        </div>
      `;
    });
  }

  renderNumericStats(numStats) {
    const tbody = document.getElementById('numeric-stats-tbody');
    tbody.innerHTML = '';
    for (const [col, s] of Object.entries(numStats || {})) {
      tbody.innerHTML += `
        <tr>
          <td><strong>${col}</strong></td>
          <td>${s.count.toLocaleString('vi-VN')}</td>
          <td>${s.sum.toLocaleString('vi-VN', { maximumFractionDigits: 0 })}</td>
          <td>${s.mean.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}</td>
          <td>${s.median.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}</td>
          <td>${s.min.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}</td>
          <td>${s.max.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}</td>
          <td>${s.std.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}</td>
        </tr>
      `;
    }
  }

  renderAnomalies(anomalies) {
    const tbody = document.getElementById('anomalies-tbody');
    tbody.innerHTML = '';
    if (!anomalies || anomalies.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #16A34A;">Không phát hiện giao dịch bất thường (3 Sigma/IQR).</td></tr>';
      return;
    }
    anomalies.forEach(a => {
      tbody.innerHTML += `
        <tr>
          <td><strong>${a.order_id}</strong></td>
          <td>${a.column}</td>
          <td>${a.value.toLocaleString('vi-VN')}</td>
          <td>${a.mean.toLocaleString('vi-VN')}</td>
          <td><span style="font-weight: 700; color: #DC2626;">${a.z_score}</span></td>
          <td><span style="background: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 4px; font-size: 11px;">${a.type}</span></td>
        </tr>
      `;
    });
  }

  // -------------------------------------------------------------
  // Step 4: Report and Executive Dashboard
  // -------------------------------------------------------------

  async loadReportStep() {
    await this.loadSummaryStrip();
    await this.loadFilterOptions();
    await this.refreshDashboard();
    await this.renderIssuesToResolve();
  }

  async loadSummaryStrip() {
    try {
      const res = await fetch('/api/report/summary-strip');
      if (!res.ok) return;
      const data = await res.json();
      const container = document.getElementById('summary-strip-container');
      if (!container) return;
      container.innerHTML = '';

      // If data.cards exists (new financial metrics), render all cards
      if (data.cards && data.cards.length > 0) {
        data.cards.forEach(c => {
          const valDisplay = c.is_na 
            ? `<span style="color: #94A3B8; font-size: 13px;" title="${c.na_reason || 'N/A'}">N/A</span>`
            : c.value_formatted;
          container.innerHTML += `
            <div class="summary-strip-card" title="${c.formula ? 'Công thức: ' + c.formula : ''}">
              <div class="title">${c.label}</div>
              <div class="val">${valDisplay}</div>
              ${c.formula ? `<div style="font-size: 10px; color: #94A3B8; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${c.formula}</div>` : ''}
            </div>
          `;
        });

        if (data.skipped_cards && data.skipped_cards.length > 0) {
          const note = document.createElement('div');
          note.style.gridColumn = '1 / -1';
          note.style.fontSize = '11.5px';
          note.style.color = '#64748B';
          note.style.padding = '4px 8px';
          note.style.fontStyle = 'italic';
          note.textContent = `* Các chỉ số chưa hiển thị do tệp thiếu cột tương ứng: ${data.skipped_cards.join(', ')}`;
          container.appendChild(note);
        }
      } else {
        // Fallback backward compatibility
        container.innerHTML = `
          <div class="summary-strip-card"><div class="title">TỔNG DOANH THU</div><div class="val">${data.total_formatted || 'N/A'}</div></div>
          <div class="summary-strip-card"><div class="title">TRUNG BÌNH</div><div class="val">${data.average_formatted || 'N/A'}</div></div>
          <div class="summary-strip-card"><div class="title">TRUNG VỊ</div><div class="val">${data.median_formatted || 'N/A'}</div></div>
          <div class="summary-strip-card"><div class="title">NHỎ NHẤT</div><div class="val">${data.min_formatted || 'N/A'}</div></div>
          <div class="summary-strip-card"><div class="title">LỚN NHẤT</div><div class="val">${data.max_formatted || 'N/A'}</div></div>
          <div class="summary-strip-card"><div class="title">SỐ DÒNG DỮ LIỆU</div><div class="val">${(data.row_count || 0).toLocaleString('vi-VN')}</div></div>
          <div class="summary-strip-card"><div class="title">NHÓM DẪN ĐẦU</div><div class="val" style="font-size: 15px;">${data.top_category || 'N/A'}</div></div>
        `;
      }
    } catch (e) {
      console.error("loadSummaryStrip error:", e);
    }
  }

  async loadFilterOptions() {
    try {
      const res = await fetch('/api/report/options');
      const data = await res.json();

      const mSelect = document.getElementById('select-month');
      mSelect.innerHTML = '';
      data.months.forEach(m => {
        const isSel = m.ym === data.default_month;
        mSelect.innerHTML += `<option value="${m.ym}" ${isSel ? 'selected' : ''}>${m.short_label}</option>`;
      });

      const gSelect = document.getElementById('select-group');
      gSelect.innerHTML = '';
      data.groups.forEach(g => {
        const isSel = g === data.default_group;
        gSelect.innerHTML += `<option value="${g}" ${isSel ? 'selected' : ''}>${g}</option>`;
      });
    } catch (e) {
      console.error(e);
    }
  }

  async handleMonthChange(event) {
    await this.refreshDashboard();
    await this.renderIssuesToResolve();
  }

  async handleGroupChange(event) {
    await this.refreshDashboard();
    await this.renderIssuesToResolve();
  }

  async refreshDashboard() {
    const mSelect = document.getElementById('select-month');
    const gSelect = document.getElementById('select-group');
    const month = mSelect ? mSelect.value : '';
    const group = gSelect ? gSelect.value : '';

    try {
      const res = await fetch(`/api/report/dashboard?month=${encodeURIComponent(month)}&group=${encodeURIComponent(group)}`);
      const dash = await res.json();
      this.dashboardData = dash;

      // Update Year Label
      document.getElementById('selected-year-label').textContent = `Năm ${dash.selected_year}`;

      // Update KPIs
      document.getElementById('kpi-total-revenue').textContent = dash.kpis.total_revenue_formatted;
      document.getElementById('kpi-month-revenue').textContent = dash.kpis.month_revenue_formatted;
      document.getElementById('kpi-total-orders').textContent = dash.kpis.total_orders_formatted;
      document.getElementById('kpi-month-orders').textContent = dash.kpis.month_orders_formatted;
      document.getElementById('kpi-mom-growth').textContent = dash.kpis.mom_growth_formatted;

      // Render Charts
      this.renderChart1(dash.charts.chart1_revenue_by_group);
      this.renderChart2(dash.charts.chart2_profit_by_group);
      this.renderChart3(dash.charts.chart3_company_ros);
      this.renderChart4(dash.charts.chart4_group_monthly_revenue);
      this.renderChart5(dash.charts.chart5_group_growth_index);
      this.renderChart6(dash.charts.chart6_group_ros);

      // Render Top Findings Table
      this.renderTopFindings(dash.top_findings);
    } catch (e) {
      console.error("Dashboard refresh error:", e);
    }
  }

  switchChartType(chartId, newType) {
    this.chartTypeOverrides[chartId] = newType;
    if (chartId === 'chart1') this.renderChart1(this.dashboardData.charts.chart1_revenue_by_group);
    else if (chartId === 'chart2') this.renderChart2(this.dashboardData.charts.chart2_profit_by_group);
    else if (chartId === 'chart4') this.renderChart4(this.dashboardData.charts.chart4_group_monthly_revenue);
    else if (chartId === 'chart5') this.renderChart5(this.dashboardData.charts.chart5_group_growth_index);
  }

  // Chart 1: Doanh thu theo nhóm SP (Column chart with value inside each bar)
  renderChart1(cData) {
    const canvas = document.getElementById('canvas-chart-1');
    const analysisBox = document.getElementById('analysis-chart-1');
    analysisBox.innerHTML = cData.analysis || '';

    if (this.chartInstances.chart1) this.chartInstances.chart1.destroy();

    const chartType = this.chartTypeOverrides.chart1 === 'horizontalBar' ? 'bar' : (this.chartTypeOverrides.chart1 || 'bar');
    const isHorizontal = this.chartTypeOverrides.chart1 === 'horizontalBar';

    const labels = cData.data.map(d => d.category);
    const values = cData.data.map(d => d.millions);
    const colors = cData.data.map(d => d.color);

    this.chartInstances.chart1 = new Chart(canvas, {
      type: chartType,
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderWidth: 0,
          borderRadius: 2
        }]
      },
      options: {
        indexAxis: isHorizontal ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: {
            color: '#FFFFFF',
            anchor: 'center',
            align: 'center',
            font: { weight: 'bold', size: 12 },
            formatter: (val) => val
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Doanh thu: ${ctx.raw} Millions`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Millions', font: { weight: 'bold' } },
            grid: { color: '#F1F5F9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // Chart 2: Lợi nhuận HĐKD theo nhóm SP
  renderChart2(cData) {
    const canvas = document.getElementById('canvas-chart-2');
    const analysisBox = document.getElementById('analysis-chart-2');
    analysisBox.innerHTML = cData.analysis || '';

    if (this.chartInstances.chart2) this.chartInstances.chart2.destroy();

    const chartType = this.chartTypeOverrides.chart2 === 'horizontalBar' ? 'bar' : (this.chartTypeOverrides.chart2 || 'bar');
    const isHorizontal = this.chartTypeOverrides.chart2 === 'horizontalBar';

    const labels = cData.data.map(d => d.category);
    const values = cData.data.map(d => d.millions);
    const colors = cData.data.map(d => d.color);

    this.chartInstances.chart2 = new Chart(canvas, {
      type: chartType,
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderWidth: 0,
          borderRadius: 2
        }]
      },
      options: {
        indexAxis: isHorizontal ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: {
            color: '#FFFFFF',
            anchor: 'center',
            align: 'center',
            font: { weight: 'bold', size: 12 },
            formatter: (val) => val
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Lợi nhuận: ${ctx.raw} Millions`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Millions', font: { weight: 'bold' } },
            grid: { color: '#F1F5F9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // Chart 3: ROS Toàn công ty (Doughnut chart with center percentage)
  renderChart3(cData) {
    const canvas = document.getElementById('canvas-chart-3');
    const analysisBox = document.getElementById('analysis-chart-3');
    analysisBox.innerHTML = cData.analysis || '';

    if (this.chartInstances.chart3) this.chartInstances.chart3.destroy();

    const rosVal = cData.value;
    const remain = Math.max(0, 100 - rosVal);

    this.chartInstances.chart3 = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['ROS', 'Còn lại'],
        datasets: [{
          data: [rosVal, remain],
          backgroundColor: ['#16A34A', '#BBF7D0'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { display: false },
          datalabels: { display: false },
          centerText: { text: `${rosVal}%` },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
            }
          }
        }
      }
    });
  }

  // Chart 4: Doanh thu của nhóm hàng (12 months orange column chart)
  renderChart4(cData) {
    const canvas = document.getElementById('canvas-chart-4');
    const analysisBox = document.getElementById('analysis-chart-4');
    analysisBox.innerHTML = cData.analysis || '';

    if (this.chartInstances.chart4) this.chartInstances.chart4.destroy();

    const chartType = this.chartTypeOverrides.chart4 === 'area' ? 'line' : (this.chartTypeOverrides.chart4 || 'bar');
    const isArea = this.chartTypeOverrides.chart4 === 'area';

    this.chartInstances.chart4 = new Chart(canvas, {
      type: chartType,
      data: {
        labels: cData.labels,
        datasets: [{
          data: cData.values,
          backgroundColor: isArea ? 'rgba(234, 88, 12, 0.2)' : '#EA580C',
          borderColor: '#EA580C',
          fill: isArea,
          borderRadius: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: {
            color: chartType === 'bar' ? '#FFFFFF' : '#EA580C',
            anchor: chartType === 'bar' ? 'center' : 'end',
            align: chartType === 'bar' ? 'center' : 'top',
            font: { weight: 'bold', size: 11 },
            formatter: (val) => val
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Doanh thu: ${ctx.raw} Millions`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Millions', font: { weight: 'bold' } },
            grid: { color: '#F1F5F9' }
          },
          x: {
            ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } },
            grid: { display: false }
          }
        }
      }
    });
  }

  // Chart 5: Tăng trưởng doanh thu từng nhóm hàng (Line chart with 100% base)
  renderChart5(cData) {
    const canvas = document.getElementById('canvas-chart-5');
    const footnote = document.getElementById('chart-5-footnote');
    const analysisBox = document.getElementById('analysis-chart-5');

    footnote.textContent = cData.footnote || '';
    analysisBox.innerHTML = cData.analysis || '';

    if (this.chartInstances.chart5) this.chartInstances.chart5.destroy();

    const chartType = this.chartTypeOverrides.chart5 === 'area' ? 'line' : (this.chartTypeOverrides.chart5 || 'line');
    const isArea = this.chartTypeOverrides.chart5 === 'area';

    this.chartInstances.chart5 = new Chart(canvas, {
      type: chartType,
      data: {
        labels: cData.labels,
        datasets: [{
          data: cData.values,
          borderColor: '#DC2626',
          backgroundColor: isArea ? 'rgba(220, 38, 38, 0.15)' : '#DC2626',
          pointBackgroundColor: '#FFFFFF',
          pointBorderColor: '#DC2626',
          pointBorderWidth: 2,
          pointRadius: 5,
          fill: isArea,
          tension: 0.2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: {
            color: '#1E293B',
            anchor: 'end',
            align: 'top',
            font: { weight: 'bold', size: 10 },
            formatter: (val) => `${val}%`
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Chỉ số tăng trưởng: ${ctx.raw}%`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: false,
            grid: { color: '#F1F5F9' },
            ticks: { callback: (val) => `${val}%` }
          },
          x: {
            ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } },
            grid: { display: false }
          }
        }
      }
    });
  }

  // Chart 6: ROS của nhóm hàng
  renderChart6(cData) {
    const canvas = document.getElementById('canvas-chart-6');
    const analysisBox = document.getElementById('analysis-chart-6');
    analysisBox.innerHTML = cData.analysis || '';

    if (this.chartInstances.chart6) this.chartInstances.chart6.destroy();

    const rosVal = cData.value;
    const remain = Math.max(0, 100 - rosVal);

    this.chartInstances.chart6 = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['ROS Nhóm', 'Còn lại'],
        datasets: [{
          data: [rosVal, remain],
          backgroundColor: ['#2563EB', '#BFDBFE'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: { display: false },
          datalabels: { display: false },
          centerText: { text: `${rosVal}%` },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
            }
          }
        }
      }
    });
  }

  renderTopFindings(findings) {
    const tbody = document.getElementById('top-findings-tbody');
    tbody.innerHTML = '';
    if (!findings || findings.length === 0) return;

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

  // -------------------------------------------------------------
  // Exports & Reset
  // -------------------------------------------------------------


  // -------------------------------------------------------------
  // AI Core Suggestions, Column Mapping & Issues Handlers
  // -------------------------------------------------------------

  async loadAISuggestions() {
    const panel = document.getElementById('ai-suggestions-panel');
    const list = document.getElementById('ai-suggestions-list');
    if (!panel || !list) return;
    panel.style.display = 'block';
    list.innerHTML = '<div style="font-size: 13px; color: #15803D;"><em>Đang quét dữ liệu và tạo gợi ý bài toán cốt lõi...</em></div>';
    
    try {
      const res = await fetch('/api/connect/ai-suggestions');
      if (!res.ok) throw new Error("Chưa thể tạo gợi ý");
      const data = await res.json();
      const suggestions = data.suggestions || [];
      if (suggestions.length === 0) {
        list.innerHTML = '<div style="font-size: 12px; color: #64748B;">Không có gợi ý tự động cho tệp này.</div>';
        return;
      }
      list.innerHTML = '';
      const qInput = document.getElementById('input-questions');
      const existingLines = qInput ? qInput.value.split('\n').map(l => l.trim()).filter(l => l.length > 0) : [];

      suggestions.forEach((s, idx) => {
        const isChecked = existingLines.includes(s.question);
        const card = document.createElement('div');
        card.className = 'suggestion-card';
        card.innerHTML = `
          <input type="checkbox" id="sugg-chk-${idx}" ${isChecked ? 'checked' : ''}>
          <div class="suggestion-card-content">
            <div class="suggestion-card-text">${s.question}</div>
            <div class="suggestion-card-meta">🎯 Mục tiêu: ${s.business_goal} | Cột liên quan: ${(s.columns_used || []).join(', ')}</div>
          </div>
        `;
        card.querySelector('input').addEventListener('change', (e) => {
          this.toggleQuestionSuggestion(s.question, e.target.checked);
        });
        list.appendChild(card);
      });
    } catch (e) {
      list.innerHTML = `<div style="font-size: 12px; color: #DC2626;">Lỗi tạo gợi ý: ${e.message}</div>`;
    }
    if (window.lucide) lucide.createIcons();
  }

  async reloadAISuggestions() {
    await this.loadAISuggestions();
  }

  toggleQuestionSuggestion(qText, add) {
    const qInput = document.getElementById('input-questions');
    if (!qInput) return;
    let lines = qInput.value.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (add) {
      if (!lines.includes(qText)) {
        if (lines.length >= 8) {
          alert("Bạn đã chọn đủ tối đa 8 câu hỏi. Hãy bỏ chọn một câu trước khi thêm mới.");
          const chk = Array.from(document.querySelectorAll('.suggestion-card')).find(c => c.textContent.includes(qText))?.querySelector('input');
          if (chk) chk.checked = false;
          return;
        }
        lines.push(qText);
      }
    } else {
      lines = lines.filter(l => l !== qText);
    }
    qInput.value = lines.join('\n');
    const badge = document.getElementById('question-count-badge');
    if (badge) {
      badge.textContent = `${lines.length}/8 câu`;
      badge.style.color = lines.length > 8 ? '#DC2626' : (lines.length > 0 ? '#2563EB' : '#64748B');
    }
  }

  async renderColumnMappingTable() {
    const tbody = document.getElementById('column-mapping-tbody');
    if (!tbody) return;
    try {
      const res = await fetch('/api/clean/mapping');
      if (!res.ok) return;
      const data = await res.json();
      const details = data.details || data.mapping_table || [];
      tbody.innerHTML = '';
      if (details.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #64748B;">Chưa có dữ liệu ánh xạ.</td></tr>';
        return;
      }
      details.forEach(item => {
        const roleLabel = item.role_name || item.label || item.role_key;
        const colName = item.mapped_column || item.detected_column;
        const colBadge = colName 
          ? `<strong style="color: #0F172A; background: #F1F5F9; padding: 2px 8px; border-radius: 4px; font-family: monospace;">${colName}</strong>`
          : `<span style="color: #94A3B8; font-style: italic;">Chưa phát hiện</span>`;
        const confStr = typeof item.confidence === 'number' ? `${Math.round(item.confidence * 100)}%` : (item.confidence || 'Tự động');
        const sampleStr = (item.sample_values || [item.sample_value || '-']).map(v => typeof v === 'number' ? v.toLocaleString('vi-VN') : v).join(', ');
        const formulaRole = item.formula_note || item.formula_role || '';
        tbody.innerHTML += `
          <tr>
            <td><strong>${roleLabel}</strong> ${item.required ? '<span style="color: #DC2626;">*</span>' : ''}</td>
            <td>${colBadge}</td>
            <td><span style="font-weight: 700; color: ${colName ? '#16A34A' : '#94A3B8'};">${confStr}</span></td>
            <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${sampleStr}">${sampleStr}</td>
            <td style="color: #475569; font-size: 12px;">${formulaRole}</td>
          </tr>
        `;
      });
    } catch (e) {
      console.error("renderColumnMappingTable error:", e);
    }
  }

  async renderIssuesToResolve() {
    const tbody = document.getElementById('issues-table-tbody');
    const badge = document.getElementById('issues-count-badge');
    if (!tbody) return;
    try {
      const res = await fetch('/api/report/issues');
      if (!res.ok) return;
      const data = await res.json();
      const issues = data.issues || [];
      this.currentIssues = issues;
      if (badge) badge.textContent = `${issues.length} vấn đề`;
      tbody.innerHTML = '';
      if (issues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #16A34A; padding: 20px;">Không phát hiện vấn đề bất thường cần cảnh báo từ dữ liệu.</td></tr>';
        return;
      }
      issues.forEach((iss, idx) => {
        const pClass = (iss.priority_class || iss.priority || 'trung-binh').toLowerCase().replace(' ', '-');
        const headlineText = iss.headline || iss.issue || 'Vấn đề trọng yếu';
        const actList = (iss.actions || []).map((a, i) => `<div>${a}</div>`).join('');
        tbody.innerHTML += `
          <tr>
            <td><span class="badge-priority ${pClass}">${iss.priority}</span></td>
            <td><strong style="color: #0F172A;">${headlineText}</strong></td>
            <td>
              <p style="margin-bottom: 4px;">${iss.evidence}</p>
              <a class="view-data-link" onclick="app.showIssueDataModal(${idx})">
                <i data-lucide="table" style="width: 12px; height: 12px;"></i> Xem số liệu truy vết
              </a>
            </td>
            <td><span style="font-weight: 700; color: #B91C1C;">${iss.impact}</span></td>
            <td><div style="display: flex; flex-direction: column; gap: 4px;">${actList}</div></td>
          </tr>
        `;
      });
      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error("renderIssuesToResolve error:", e);
    }
  }

  showIssueDataModal(idx) {
    const iss = (this.currentIssues || [])[idx];
    if (!iss) return;
    const title = document.getElementById('issue-modal-title');
    const body = document.getElementById('issue-modal-body');
    const modal = document.getElementById('issue-modal');
    if (!modal || !title || !body) return;

    const headlineText = iss.headline || iss.issue || 'Chi tiết số liệu';
    title.textContent = `Bằng chứng & Số liệu chi tiết: ${headlineText}`;
    const rawData = iss.trace_data || iss.underlying_data || {};
    let tableHtml = '<table class="data-table" style="margin-top: 8px;"><thead><tr><th>Chỉ số / Trường dữ liệu</th><th>Giá trị ghi nhận</th></tr></thead><tbody>';
    for (const [k, v] of Object.entries(rawData)) {
      const displayVal = typeof v === 'number' ? v.toLocaleString('vi-VN') : (typeof v === 'object' ? JSON.stringify(v) : v);
      tableHtml += `<tr><td><strong>${k}</strong></td><td>${displayVal}</td></tr>`;
    }
    tableHtml += '</tbody></table>';

    body.innerHTML = `
      <div style="margin-bottom: 12px; background: #F1F5F9; padding: 12px; border-radius: 8px;">
        <span class="badge-priority ${(iss.priority_class || iss.priority || 'trung-binh').toLowerCase()}" style="margin-bottom: 6px;">${iss.priority}</span>
        <p style="font-size: 13.5px; font-weight: 600; color: #0F172A; margin-top: 4px;">${iss.evidence}</p>
        <p style="font-size: 12px; color: #B91C1C; margin-top: 4px;"><strong>Tác động định lượng:</strong> ${iss.impact}</p>
      </div>
      <h5 style="font-weight: 700; margin-bottom: 6px;">Số liệu tính toán từ tệp:</h5>
      ${tableHtml}
    `;
    modal.style.display = 'flex';
  }

  closeIssueModal() {
    const modal = document.getElementById('issue-modal');
    if (modal) modal.style.display = 'none';
  }

    exportFile(type) {
    if (type === 'pdf') {
      window.open('/api/export/pdf', '_blank');
    } else if (type === 'excel') {
      window.location.href = '/api/export/excel';
    } else if (type === 'csv') {
      window.location.href = '/api/export/csv';
    }
  }

  async resetSession() {
    if (confirm("Bạn có chắc chắn muốn làm mới toàn bộ Không gian phân tích không? Mọi dữ liệu phiên hiện tại sẽ bị xóa.")) {
      await fetch('/api/reset', { method: 'POST' });
      window.location.reload();
    }
  }
}

// Instantiate global app
window.app = new AnalysisApp();
