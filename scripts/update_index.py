import re
import os

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Hero section
hero_html = '''        <!-- ======================================================== -->
        <!-- STEP 1: KẾT NỐI DỮ LIỆU                                  -->
        <!-- ======================================================== -->
        <section id="step-1-content" class="step-pane">
          <!-- FLOWER HAPPY 3D PASTEL HERO SECTION -->
          <div class="flower-hero-section">
            <div class="floating-gem gem-1"></div>
            <div class="floating-gem gem-2"></div>
            <div class="floating-gem gem-3"></div>
            <div class="floating-gem gem-4"></div>

            <div class="flower-hero-card">
              <div class="flower-hero-header">
                <div class="flower-brand">
                  <div class="flower-logo-icon">✨</div>
                  <span class="flower-brand-name">Flower Happy</span>
                </div>
                <div class="flower-nav-links">
                  <span>Giải pháp</span>
                  <span>Dịch vụ</span>
                  <span>Báo cáo</span>
                  <span class="flower-nav-pill">Không gian mở</span>
                </div>
              </div>

              <div class="flower-hero-body">
                <h1 class="flower-hero-title">Welcome to Flower Happy</h1>
                <p class="flower-hero-sub">Hệ sinh thái phân tích dữ liệu kinh doanh 3D thế hệ mới — Khám phá doanh thu, lợi nhuận và xu hướng tăng trưởng chuẩn xác</p>

                <div class="flower-search-box">
                  <i data-lucide="search" class="flower-search-icon"></i>
                  <input type="text" class="flower-search-input" placeholder="Tìm kiếm chỉ số, sản phẩm, ngành hàng hoặc vấn đề cốt lõi...">
                  <span class="flower-year-pill" id="hero-year-badge">2026</span>
                </div>
              </div>
            </div>

            <!-- 3 SERVICE CARDS (LINKING TO WORKFLOW STEPS) -->
            <div class="flower-services-grid">
              <div class="service-card service-card-1" onclick="app.goToStep(1)">
                <div class="service-sphere sphere-pink">
                  <i data-lucide="sparkles"></i>
                </div>
                <h4 class="service-card-title">Phân tích doanh thu</h4>
                <p class="service-card-desc">Kết nối đa nguồn dữ liệu, bóc tách doanh thu gộp, chiết khấu và giá trị đơn hàng trung bình.</p>
                <div class="service-card-footer">
                  <span class="step-indicator">Bước 1 • Khởi tạo</span>
                  <i data-lucide="arrow-right"></i>
                </div>
              </div>

              <div class="service-card service-card-2" onclick="app.goToStep(3)">
                <div class="service-sphere sphere-amber">
                  <i data-lucide="pie-chart"></i>
                </div>
                <h4 class="service-card-title">Lợi nhuận & biên lợi nhuận</h4>
                <p class="service-card-desc">Tính toán chính xác Lợi nhuận HĐKD, giá vốn COGS và tỷ suất ROS theo nhóm sản phẩm.</p>
                <div class="service-card-footer">
                  <span class="step-indicator">Bước 3 • Phân tích</span>
                  <i data-lucide="arrow-right"></i>
                </div>
              </div>

              <div class="service-card service-card-3" onclick="app.goToStep(4)">
                <div class="service-sphere sphere-purple">
                  <i data-lucide="trending-up"></i>
                </div>
                <h4 class="service-card-title">Xu hướng tăng trưởng</h4>
                <p class="service-card-desc">Bảng điều khiển điều hành 12 tháng, cảnh báo vấn đề ưu tiên và xuất tệp Excel/PDF.</p>
                <div class="service-card-footer">
                  <span class="step-indicator">Bước 4 • Báo cáo</span>
                  <i data-lucide="arrow-right"></i>
                </div>
              </div>
            </div>

            <!-- BRIDGE DECORATION MOTIF -->
            <div class="bridge-decoration">
              <div class="bridge-arch"></div>
              <div class="bridge-glow"></div>
            </div>
          </div>'''

target_step1 = '''        <!-- ======================================================== -->
        <!-- STEP 1: KẾT NỐI DỮ LIỆU                                  -->
        <!-- ======================================================== -->
        <section id="step-1-content" class="step-pane">'''

if target_step1 in html:
    html = html.replace(target_step1, hero_html)
    print("Replaced Step 1 with Hero section")
else:
    print("Target Step 1 not found or already replaced")

# 2. Empty Step 1 inputs
html = html.replace('value="Bán lẻ và phân phối nông sản chế biến"', 'value=""')
html = re.sub(r'<textarea id="input-biz-info"[^>]*>.*?</textarea>', '<textarea id="input-biz-info" class="form-textarea" rows="2" placeholder="Ví dụ: Thị trường miền Nam, hoạt động đa kênh từ 2018..."></textarea>', html, flags=re.DOTALL)
html = re.sub(r'<textarea id="input-questions"[^>]*>.*?</textarea>', '<textarea id="input-questions" class="form-textarea" rows="5" placeholder="Nhập từ 1 đến 8 câu hỏi, mỗi câu trên một dòng riêng biệt...&#10;Hoặc tích chọn nhanh từ danh sách AI gợi ý vấn đề cốt lõi bên dưới..."></textarea>', html, flags=re.DOTALL)
html = html.replace('3/8 câu', '0/8 câu')

# 3. Add AI suggestions panel after business context panel
ai_suggestions_block = '''          <!-- AI SUGGESTIONS PANEL (Auto populated upon data upload) -->
          <div id="ai-suggestions-panel" class="panel-card" style="display: none; border: 1.5px solid #BBF7D0; background: #F0FDF4; margin-top: 16px;">
            <div class="panel-header" style="margin-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <i data-lucide="sparkles" style="color: #16A34A; width: 20px; height: 20px;"></i>
                <div>
                  <h3 class="panel-title" style="color: #14532D; font-size: 15px;">AI gợi ý vấn đề cốt lõi từ dữ liệu tải lên</h3>
                  <span style="font-size: 12px; color: #166534;">Tích chọn câu hỏi bên dưới để tự động điền vào danh sách câu hỏi phân tích</span>
                </div>
              </div>
              <button class="btn btn-secondary" style="font-size: 12px; padding: 4px 10px; background: #FFFFFF; border-color: #86EFAC; color: #15803D;" onclick="app.reloadAISuggestions()">
                <i data-lucide="refresh-cw"></i> Tạo lại gợi ý
              </button>
            </div>
            <div id="ai-suggestions-list" class="ai-suggestions-list" style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">
              <!-- Suggestions checkboxes rendered here -->
            </div>
          </div>
'''
target_after_biz = '<!-- Data Ingestion Section -->'
if target_after_biz in html and 'id="ai-suggestions-panel"' not in html:
    html = html.replace(target_after_biz, ai_suggestions_block + '\n          ' + target_after_biz)
    print("Added AI suggestions panel")

# 4. In Step 2, add visible Column Mapping Table
mapping_table_block = '''            <!-- Visible Column Mapping Table -->
            <div style="margin-top: 24px; border-top: 1px solid #E2E8F0; padding-top: 16px;">
              <h4 style="font-size: 13.5px; font-weight: 700; color: #1E3A8A; margin-bottom: 8px;">
                Bảng đối soát & ánh xạ chi tiết các chỉ số tài chính (Column Mapping)
              </h4>
              <p style="font-size: 12px; color: #64748B; margin-bottom: 12px;">
                Bảng đối soát minh bạch các cột định lượng trong tệp dữ liệu, độ tin cậy nhận diện và vai trò tham gia vào công thức tính Doanh thu thuần & Lợi nhuận.
              </p>
              <div class="table-container">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th style="width: 200px;">Vai trò tài chính</th>
                      <th style="width: 180px;">Cột phát hiện trong dữ liệu</th>
                      <th style="width: 110px;">Độ tin cậy</th>
                      <th>Giá trị mẫu</th>
                      <th>Vai trò trong công thức tính toán</th>
                    </tr>
                  </thead>
                  <tbody id="column-mapping-tbody">
                    <!-- Populated dynamically -->
                  </tbody>
                </table>
              </div>
            </div>
'''
target_step2_roles = '<!-- Audit Log Section -->'
if target_step2_roles in html and 'id="column-mapping-tbody"' not in html:
    # insert before Audit Log Section panel-card
    idx = html.find(target_step2_roles)
    # find the previous closing </div> before that
    card_close = html.rfind('</div>', 0, idx)
    html = html[:card_close] + mapping_table_block + html[card_close:]
    print("Added Column Mapping Table")

# 5. In Step 4, add the Issues To Resolve Table
issues_block = '''          <!-- I. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT (RED HEADER BAR) -->
          <div class="issues-table-panel">
            <div class="issues-header-bar">
              <div style="display: flex; align-items: center; gap: 10px;">
                <i data-lucide="alert-octagon" style="width: 22px; height: 22px;"></i>
                <span>I. NHỮNG VẤN ĐỀ CẦN GIẢI QUYẾT (xếp theo mức độ ưu tiên – số liệu cập nhật tự động)</span>
              </div>
              <span id="issues-count-badge" style="background: rgba(255,255,255,0.25); padding: 3px 12px; border-radius: 9999px; font-size: 12px; font-weight: 700;">0 vấn đề</span>
            </div>
            
            <div class="table-container">
              <table class="issues-table">
                <thead>
                  <tr>
                    <th style="width: 120px;">Mức độ</th>
                    <th style="width: 200px;">Vấn đề</th>
                    <th>Bằng chứng từ số liệu</th>
                    <th style="width: 180px;">Tác động</th>
                    <th style="width: 320px;">Đề xuất hành động</th>
                  </tr>
                </thead>
                <tbody id="issues-table-tbody">
                  <!-- Rendered dynamically -->
                </tbody>
              </table>
            </div>

            <div class="issues-footnote">
              💡 <strong>Ghi chú kiểm chứng:</strong> Toàn bộ các phát hiện và con số trên được tính toán tự động trực tiếp từ tệp dữ liệu đã làm sạch. Nhấp vào <em>"Xem số liệu"</em> tại mỗi dòng để truy vết bảng chi tiết số liệu gốc.
            </div>
          </div>

          <!-- Traceability Modal for Issues -->
          <div id="issue-modal" class="modal-overlay" onclick="if(event.target===this) app.closeIssueModal()">
            <div style="background: #FFF; border-radius: 12px; max-width: 650px; width: 100%; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);">
              <div style="padding: 16px 20px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
                <h4 id="issue-modal-title" style="font-size: 15px; font-weight: 700; color: #0F172A;">Chi tiết số liệu truy vết</h4>
                <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 12px;" onclick="app.closeIssueModal()">✕ Đóng</button>
              </div>
              <div id="issue-modal-body" style="padding: 20px; overflow-y: auto; font-size: 13px; line-height: 1.6;">
              </div>
            </div>
          </div>
'''
target_step4_findings = '<!-- Top Findings Table -->'
if target_step4_findings in html and 'id="issues-table-tbody"' not in html:
    html = html.replace(target_step4_findings, issues_block + '\n          ' + target_step4_findings)
    print("Added Issues to Resolve Table")

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
with open('public/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Synchronized all HTML files successfully.")
