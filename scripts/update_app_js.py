import re

with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add this.currentIssues = [] in constructor
if 'this.currentIssues = [];' not in js:
    js = js.replace('this.dashboardData = null;', 'this.dashboardData = null;\n    this.currentIssues = [];')
    print("Added this.currentIssues to constructor")

# 2. In renderPreview, call loadAISuggestions
if 'this.loadAISuggestions();' not in js:
    js = js.replace('card.scrollIntoView({ behavior: \'smooth\' });', 'card.scrollIntoView({ behavior: \'smooth\' });\n    this.loadAISuggestions();')
    print("Added this.loadAISuggestions() to renderPreview")

# 3. In loadCleanStep, call renderColumnMappingTable
if 'this.renderColumnMappingTable();' not in js:
    js = js.replace('this.renderAuditLog(data.audit_log);', 'this.renderAuditLog(data.audit_log);\n      await this.renderColumnMappingTable();')
    print("Added this.renderColumnMappingTable() to loadCleanStep")

# 4. In loadReportStep, call renderIssuesToResolve
if 'this.renderIssuesToResolve();' not in js:
    js = js.replace('await this.refreshDashboard();', 'await this.refreshDashboard();\n    await this.renderIssuesToResolve();')
    print("Added this.renderIssuesToResolve() to loadReportStep")

# 5. Replace loadSummaryStrip with new implementation handling cards, tooltips, formulas, and skipped cards
old_load_summary = """  async loadSummaryStrip() {
    try {
      const res = await fetch('/api/report/summary-strip');
      const data = await res.json();
      const container = document.getElementById('summary-strip-container');
      container.innerHTML = `
        <div class="summary-strip-card">
          <div class="title">TỔNG DOANH THU</div>
          <div class="val">${data.total_formatted}</div>
        </div>
        <div class="summary-strip-card">
          <div class="title">TRUNG BÌNH</div>
          <div class="val">${data.average_formatted}</div>
        </div>
        <div class="summary-strip-card">
          <div class="title">TRUNG VỊ</div>
          <div class="val">${data.median_formatted}</div>
        </div>
        <div class="summary-strip-card">
          <div class="title">NHỎ NHẤT</div>
          <div class="val">${data.min_formatted}</div>
        </div>
        <div class="summary-strip-card">
          <div class="title">LỚN NHẤT</div>
          <div class="val">${data.max_formatted}</div>
        </div>
        <div class="summary-strip-card">
          <div class="title">SỐ DÒNG DỮ LIỆU</div>
          <div class="val">${data.row_count.toLocaleString('vi-VN')}</div>
        </div>
        <div class="summary-strip-card">
          <div class="title">NHÓM DẪN ĐẦU</div>
          <div class="val" style="font-size: 15px;">${data.top_category || 'N/A'}</div>
        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  }"""

new_load_summary = """  async loadSummaryStrip() {
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
  }"""

if old_load_summary in js:
    js = js.replace(old_load_summary, new_load_summary)
    print("Replaced loadSummaryStrip")
else:
    print("old_load_summary not found exactly, will check")

# 6. Add new helper methods at the end of class AnalysisApp (before exportFile)
new_methods = """
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
      const existingLines = qInput ? qInput.value.split('\\n').map(l => l.trim()).filter(l => l.length > 0) : [];

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
    let lines = qInput.value.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
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
    qInput.value = lines.join('\\n');
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
      const details = data.details || [];
      tbody.innerHTML = '';
      if (details.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #64748B;">Chưa có dữ liệu ánh xạ.</td></tr>';
        return;
      }
      details.forEach(item => {
        const colBadge = item.detected_column 
          ? `<strong style="color: #0F172A; background: #F1F5F9; padding: 2px 8px; border-radius: 4px; font-family: monospace;">${item.detected_column}</strong>`
          : `<span style="color: #94A3B8; font-style: italic;">Chưa phát hiện</span>`;
        const confPercent = Math.round((item.confidence || 0) * 100);
        const confBadge = item.detected_column
          ? `<span style="font-weight: 700; color: ${confPercent >= 80 ? '#16A34A' : '#EA580C'};">${confPercent}%</span>`
          : `<span style="color: #94A3B8;">0%</span>`;
        const sampleStr = (item.sample_values || []).map(v => typeof v === 'number' ? v.toLocaleString('vi-VN') : v).join(', ') || '-';
        tbody.innerHTML += `
          <tr>
            <td><strong>${item.label}</strong> ${item.is_required ? '<span style="color: #DC2626;">*</span>' : ''}</td>
            <td>${colBadge}</td>
            <td>${confBadge}</td>
            <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${sampleStr}">${sampleStr}</td>
            <td style="color: #475569; font-size: 12px;">${item.formula_role}</td>
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
        const pClass = (iss.priority_class || 'trung-binh').toLowerCase();
        const actList = (iss.actions || []).map((a, i) => `<div><strong>${String.fromCharCode(97 + i)}.</strong> ${a}</div>`).join('');
        tbody.innerHTML += `
          <tr>
            <td><span class="badge-priority ${pClass}">${iss.priority}</span></td>
            <td><strong style="color: #0F172A;">${iss.issue}</strong></td>
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

    title.textContent = `Bằng chứng & Số liệu chi tiết: ${iss.issue}`;
    const rawData = iss.underlying_data || {};
    let tableHtml = '<table class="data-table" style="margin-top: 8px;"><thead><tr><th>Chỉ số / Trường dữ liệu</th><th>Giá trị ghi nhận</th></tr></thead><tbody>';
    for (const [k, v] of Object.entries(rawData)) {
      const displayVal = typeof v === 'number' ? v.toLocaleString('vi-VN') : (typeof v === 'object' ? JSON.stringify(v) : v);
      tableHtml += `<tr><td><strong>${k}</strong></td><td>${displayVal}</td></tr>`;
    }
    tableHtml += '</tbody></table>';

    body.innerHTML = `
      <div style="margin-bottom: 12px; background: #F1F5F9; padding: 12px; border-radius: 8px;">
        <span class="badge-priority ${(iss.priority_class || 'trung-binh').toLowerCase()}" style="margin-bottom: 6px;">${iss.priority}</span>
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
"""

if 'loadAISuggestions()' not in js:
    target_export = '  // -------------------------------------------------------------\n  // Exports & Reset\n  // -------------------------------------------------------------'
    js = js.replace(target_export, new_methods + '\n' + target_export)
    print("Added new methods")

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
with open('app.js', 'w', encoding='utf-8') as f:
    f.write(js)
with open('public/static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Synchronized all JS files successfully!")
