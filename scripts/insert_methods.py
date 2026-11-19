with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

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
"""

target = "  exportFile(type) {"
if target in js:
    js = js.replace(target, new_methods + "\n  " + target)
    with open('static/app.js', 'w', encoding='utf-8') as f:
        f.write(js)
    with open('app.js', 'w', encoding='utf-8') as f:
        f.write(js)
    with open('public/static/app.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Inserted methods and synchronized app.js successfully!")
else:
    print("Target exportFile(type) not found")
