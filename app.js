/**
 * Kẹo Cute - AI Data Processing Agent Frontend Controller
 */

// Global App State
const state = {
  currentStep: 1, // 1: Intro, 2: Business Context, 3: Upload, 4: Cleaning, 5: Preview/Approval, 6: Dashboard
  context: {
    business_name: 'Kẹo Cute',
    business_type: 'F&B / Bánh kẹo & Đồ uống',
    additional_info: ''
  },
  filename: '',
  inspection: null,
  rawPreview: [],
  cleanedPreview: [],
  diffData: null,
  auditLog: [],
  stats: null,
  dashboardData: null,
  iteration: 1,
  charts: {
    waveChart: null,
    donutChart: null
  }
};

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  initIcons();
  setupNavigation();
  setupBusinessContext();
  setupUpload();
  setupCleaningControls();
  setupApprovalLoop();
  setupExport();
});

function initIcons() {
  if (window.lucide) {
    lucide.createIcons();
  }
}

// =================== NAVIGATION & STEP MANAGEMENT ===================
function setupNavigation() {
  // Dock buttons
  document.querySelectorAll('.dock-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetStep = parseInt(btn.dataset.step);
      if (isNaN(targetStep)) return;

      // Validate step transitions
      if (targetStep >= 4 && !state.inspection) {
        showToast('Vui lòng hoàn thành bước tải file hoặc chọn dữ liệu mẫu trước nhé! 🍬', 'warning');
        return;
      }
      if (targetStep >= 5 && !state.cleanedPreview.length) {
        showToast('Vui lòng chạy bước làm sạch dữ liệu trước khi xem trước nhé!', 'warning');
        return;
      }
      if (targetStep === 6 && (!state.dashboardData || !state.dashboardData.status)) {
        showToast('Vui lòng phê duyệt bản xem trước trước khi xem báo cáo!', 'warning');
        return;
      }
      goToStep(targetStep);
    });
  });

  // Start button in Intro -> Goes to Step 2 (Business Context)
  const btnStart = document.getElementById('btn-start-guide');
  if (btnStart) {
    btnStart.addEventListener('click', () => {
      goToStep(2);
    });
  }
}

function goToStep(stepNum) {
  state.currentStep = stepNum;

  // Update view visibility
  document.querySelectorAll('.step-view').forEach(view => {
    view.classList.add('hidden');
  });
  const targetView = document.getElementById(`view-step-${stepNum}`);
  if (targetView) {
    targetView.classList.remove('hidden');
    targetView.classList.add('animate-fadeIn');
  }

  // Update dock active state
  document.querySelectorAll('.dock-btn').forEach(btn => {
    if (parseInt(btn.dataset.step) === stepNum) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update step indicator pills
  document.querySelectorAll('.step-pill').forEach(pill => {
    const s = parseInt(pill.dataset.step);
    pill.classList.remove('active', 'completed');
    if (s === stepNum) {
      pill.classList.add('active');
    } else if (s < stepNum) {
      pill.classList.add('completed');
    }
  });

  initIcons();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =================== BUSINESS CONTEXT (BỐI CẢNH DOANH NGHIỆP) ===================
function setupBusinessContext() {
  const bizTypeInput = document.getElementById('ctx-business-type');
  const bizNameInput = document.getElementById('ctx-business-name');
  const addInfoInput = document.getElementById('ctx-additional-info');
  const errorMsg = document.getElementById('ctx-type-error');
  const btnSave = document.getElementById('btn-save-context');

  // Quick select pills for Business Type
  document.querySelectorAll('.biz-type-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.biz-type-pill').forEach(p => {
        p.classList.remove('active', 'bg-[#BE7B68]', 'text-white', 'border-[#BE7B68]');
        p.classList.add('bg-[#FCFAF6]', 'text-[#63534B]', 'border-[#BE7B68]/20');
      });

      pill.classList.add('active', 'bg-[#BE7B68]', 'text-white', 'border-[#BE7B68]');
      pill.classList.remove('bg-[#FCFAF6]', 'text-[#63534B]', 'border-[#BE7B68]/20');

      const val = pill.dataset.val;
      if (val === 'Khác') {
        bizTypeInput.value = '';
        bizTypeInput.placeholder = 'Nhập loại hình kinh doanh cụ thể của bạn...';
        bizTypeInput.focus();
      } else {
        bizTypeInput.value = val;
      }

      if (errorMsg) errorMsg.classList.add('hidden');
      bizTypeInput.classList.remove('border-[#C0392B]');
    });
  });

  bizTypeInput.addEventListener('input', () => {
    if (bizTypeInput.value.trim() && errorMsg) {
      errorMsg.classList.add('hidden');
      bizTypeInput.classList.remove('border-[#C0392B]');
    }
  });

  // Save Context and Proceed to Step 3 (File Upload)
  if (btnSave) {
    btnSave.addEventListener('click', async () => {
      const bizType = bizTypeInput.value.trim();
      const bizName = bizNameInput.value.trim() || 'Kẹo Cute';
      const addInfo = addInfoInput.value.trim();

      // VALIDATION: Business Type is MANDATORY
      if (!bizType) {
        if (errorMsg) errorMsg.classList.remove('hidden');
        bizTypeInput.classList.add('border-[#C0392B]');
        bizTypeInput.focus();
        showToast('⚠️ Loại hình doanh nghiệp là bắt buộc. Vui lòng chọn hoặc nhập nhé!', 'warning');
        return;
      }

      showLoader('Đang lưu bối cảnh doanh nghiệp...');

      try {
        const res = await fetch('/api/context', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            business_name: bizName,
            business_type: bizType,
            additional_info: addInfo
          })
        });
        const data = await res.json();
        hideLoader();

        if (data.status === 'success') {
          state.context = data.context;

          // Update Context banners and Header
          updateContextDisplay();

          showToast(`Đã thiết lập bối cảnh: ${bizName} (${bizType})! ✨`, 'success');
          goToStep(3); // Advance to Upload
        } else {
          showToast(data.message || 'Lỗi khi lưu bối cảnh', 'error');
        }
      } catch (err) {
        hideLoader();
        showToast('Lỗi kết nối máy chủ', 'error');
      }
    });
  }
}

function updateContextDisplay() {
  const activeName = document.getElementById('active-biz-name');
  const activeType = document.getElementById('active-biz-type');
  const headerBrand = document.getElementById('header-brand-name');
  const dashName = document.getElementById('dash-business-name');
  const dashType = document.getElementById('dash-business-type');

  if (activeName) activeName.innerText = state.context.business_name || 'Kẹo Cute';
  if (activeType) activeType.innerText = state.context.business_type || 'F&B / Bánh kẹo & Đồ uống';
  if (headerBrand) headerBrand.innerText = state.context.business_name || 'Kẹo Cute';
  if (dashName) dashName.innerText = `${state.context.business_name || 'Kẹo Cute'} Data Dashboard`;
  if (dashType) dashType.innerText = state.context.business_type || 'F&B / Bánh kẹo & Đồ uống';
}

// =================== FILE UPLOAD & SAMPLE DATA ===================
function setupUpload() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const btnSample = document.getElementById('btn-load-sample');

  // Drag and drop handlers
  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  });

  dropzone.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  // Sample data button
  if (btnSample) {
    btnSample.addEventListener('click', (e) => {
      e.stopPropagation();
      loadSampleData();
    });
  }

  // Proceed to Step 4 (Làm sạch)
  const btnToClean = document.getElementById('btn-to-clean');
  if (btnToClean) {
    btnToClean.addEventListener('click', () => {
      goToStep(4);
    });
  }
}

async function loadSampleData() {
  showLoader('Đang tạo dữ liệu mẫu Kẹo Cute ngọt ngào...');
  try {
    const res = await fetch('/api/sample', { method: 'POST' });
    const data = await res.json();
    hideLoader();

    if (data.status === 'success') {
      applyLoadedData(data);
      showToast('Đã nạp thành công 120 đơn hàng mẫu của Kẹo Cute! ✨', 'success');
    } else {
      showToast(data.message || 'Lỗi khi tải mẫu', 'error');
    }
  } catch (err) {
    hideLoader();
    showToast('Lỗi kết nối máy chủ localhost', 'error');
  }
}

async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  showLoader(`Đang đọc tệp "${file.name}"...`);
  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    hideLoader();

    if (data.status === 'success') {
      applyLoadedData(data);
      showToast(`Tải tệp "${data.filename}" thành công!`, 'success');
    } else {
      showToast(data.message || 'Lỗi tải tệp', 'error');
    }
  } catch (err) {
    hideLoader();
    showToast('Không thể kết nối đến API localhost', 'error');
  }
}

function applyLoadedData(data) {
  state.filename = data.filename;
  state.inspection = data.inspection;
  state.rawPreview = data.preview;
  if (data.context) {
    state.context = data.context;
    updateContextDisplay();
  }

  // Show uploaded summary section
  document.getElementById('upload-initial-state').classList.add('hidden');
  document.getElementById('upload-success-state').classList.remove('hidden');

  document.getElementById('loaded-filename').innerText = data.filename;
  document.getElementById('loaded-rows').innerText = `${data.total_rows} dòng`;
  document.getElementById('loaded-cols').innerText = `${data.total_cols} cột`;

  // Quality card
  const health = data.inspection.health_score;
  document.getElementById('health-score-val').innerText = `${health}%`;
  document.getElementById('health-bar').style.width = `${health}%`;
  document.getElementById('missing-count').innerText = data.inspection.missing_cells;
  document.getElementById('dup-count').innerText = data.inspection.duplicate_rows;
  document.getElementById('messy-phone-count').innerText = data.inspection.messy_phones;
  document.getElementById('messy-name-count').innerText = data.inspection.messy_names;

  // Render raw preview table
  renderTable('raw-data-table', data.preview, data.inspection.columns);
  initIcons();
}

// =================== DATA CLEANING CONTROLS ===================
function setupCleaningControls() {
  // Suggestion tags for AI Prompt
  document.querySelectorAll('.ai-suggest-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const input = document.getElementById('ai-custom-prompt');
      const text = pill.dataset.prompt;
      if (input.value) {
        input.value += `, ${text}`;
      } else {
        input.value = text;
      }
    });
  });

  // Run AI Processing Button
  document.getElementById('btn-run-process').addEventListener('click', runDataProcessing);
}

async function runDataProcessing() {
  const options = {
    remove_duplicates: document.getElementById('opt-duplicates').checked,
    missing_action: document.querySelector('input[name="missing_opt"]:checked').value,
    trim_whitespace: document.getElementById('opt-whitespace').checked,
    format_names: document.getElementById('opt-names').checked,
    normalize_phone: document.getElementById('opt-phone').checked,
    standardize_dates: document.getElementById('opt-dates').checked,
    clean_currency: document.getElementById('opt-currency').checked,
    custom_prompt: document.getElementById('ai-custom-prompt').value
  };

  showProcessingModal();

  try {
    const res = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options)
    });
    const data = await res.json();

    setTimeout(() => {
      hideProcessingModal();
      if (data.status === 'success') {
        state.stats = data.stats;
        state.auditLog = data.auditLog;
        state.diffData = data.diff;
        state.cleanedPreview = data.preview;
        state.iteration = data.iteration;

        renderPreviewView(data);
        goToStep(5); // Advance to Preview & Approval
        showToast('AI Agent Kẹo Cute đã xử lý xong dữ liệu! Hãy xem trước và phản hồi.', 'success');
      } else {
        showToast(data.message || 'Lỗi khi xử lý dữ liệu', 'error');
      }
    }, 1400);
  } catch (err) {
    hideProcessingModal();
    showToast('Lỗi kết nối máy chủ', 'error');
  }
}

// =================== PREVIEW & APPROVAL LOOP ===================
function setupApprovalLoop() {
  // Preview tabs
  document.querySelectorAll('.preview-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preview-tab-btn').forEach(b => {
        b.classList.remove('bg-white', 'text-[#3A2E2B]', 'shadow-sm', 'font-semibold');
        b.classList.add('text-[#7D6B63]');
      });
      btn.classList.add('bg-white', 'text-[#3A2E2B]', 'shadow-sm', 'font-semibold');
      btn.classList.remove('text-[#7D6B63]');

      const tabId = btn.dataset.tab;
      document.querySelectorAll('.preview-tab-content').forEach(c => c.classList.add('hidden'));
      document.getElementById(`tab-content-${tabId}`).classList.remove('hidden');
    });
  });

  // Client Approves!
  document.getElementById('btn-approve-data').addEventListener('click', async () => {
    showLoader('Đang hoàn tất và xây dựng báo cáo phân tích...');
    try {
      const res = await fetch('/api/approve', { method: 'POST' });
      const data = await res.json();
      hideLoader();

      if (data.status === 'success') {
        state.dashboardData = data;
        renderDashboard(data);
        goToStep(6); // Advance to Final Dashboard
        showToast('🎉 Bản sửa đã được phê duyệt thành công!', 'success');
      } else {
        showToast(data.message || 'Lỗi phê duyệt', 'error');
      }
    } catch (e) {
      hideLoader();
      showToast('Lỗi kết nối máy chủ', 'error');
    }
  });

  // Client Rejects / Requests Re-processing!
  const rejectBtn = document.getElementById('btn-reject-data');
  const rejectDrawer = document.getElementById('reprocess-drawer');

  rejectBtn.addEventListener('click', () => {
    rejectDrawer.classList.toggle('hidden');
    if (!rejectDrawer.classList.contains('hidden')) {
      rejectDrawer.scrollIntoView({ behavior: 'smooth' });
    }
  });

  document.getElementById('btn-cancel-reprocess').addEventListener('click', () => {
    rejectDrawer.classList.add('hidden');
  });

  // Quick feedback tag pills
  document.querySelectorAll('.feedback-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const feedbackInput = document.getElementById('reprocess-feedback-text');
      const val = tag.dataset.text;
      if (feedbackInput.value) {
        feedbackInput.value += `\n- ${val}`;
      } else {
        feedbackInput.value = `- ${val}`;
      }
    });
  });

  // Submit Re-processing
  document.getElementById('btn-submit-reprocess').addEventListener('click', async () => {
    const feedbackText = document.getElementById('reprocess-feedback-text').value.trim();
    if (!feedbackText) {
      showToast('Vui lòng nhập ghi chú hoặc chọn lý do cần xử lý lại nhé!', 'warning');
      return;
    }

    showProcessingModal('AI Agent Kẹo Cute đang hiệu chỉnh & xử lý lại...');

    try {
      const res = await fetch('/api/reprocess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedbackText })
      });
      const data = await res.json();

      setTimeout(() => {
        hideProcessingModal();
        if (data.status === 'success') {
          state.stats = data.stats;
          state.auditLog = data.auditLog;
          state.diffData = data.diff;
          state.cleanedPreview = data.preview;
          state.iteration = data.iteration;

          rejectDrawer.classList.add('hidden');
          document.getElementById('reprocess-feedback-text').value = '';

          renderPreviewView(data);
          showToast(data.message || 'Đã xử lý lại theo yêu cầu! Mời bạn kiểm tra lại.', 'success');
        } else {
          showToast(data.message || 'Lỗi khi xử lý lại', 'error');
        }
      }, 1300);
    } catch (e) {
      hideProcessingModal();
      showToast('Lỗi kết nối máy chủ', 'error');
    }
  });
}

function renderPreviewView(data) {
  // Update version iteration badge
  const iterBadge = document.getElementById('preview-iteration-badge');
  if (iterBadge) {
    iterBadge.innerText = `Phiên bản làm sạch #${data.iteration}`;
  }

  // Stats highlight cards
  document.getElementById('preview-final-rows').innerText = data.stats.final_rows;
  document.getElementById('preview-changed-cells').innerText = data.stats.rows_changed;
  document.getElementById('preview-final-health').innerText = `${data.stats.final_health}%`;
  document.getElementById('preview-total-actions').innerText = data.audit_log.length;

  // Render Cleaned Data Table
  renderTable('cleaned-data-table', data.preview, data.columns);

  // Render Diff View
  renderDiffView(data.diff);

  // Render Audit Log
  renderAuditLog(data.audit_log);

  initIcons();
}

function renderDiffView(diff) {
  const container = document.getElementById('diff-content-list');
  container.innerHTML = '';

  if (!diff || !diff.sample_diffs || diff.sample_diffs.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-[#96847B]">
        <i data-lucide="check-check" class="w-10 h-10 mx-auto text-[#7E9682] mb-2"></i>
        <p class="font-medium">Dữ liệu hoàn toàn khớp và đã đạt độ sạch tối ưu!</p>
      </div>`;
    return;
  }

  diff.sample_diffs.forEach(item => {
    const changesHtml = Object.keys(item.changes).map(col => `
      <div class="flex items-center gap-2 text-xs py-1 border-b border-[#BE7B68]/10 last:border-0">
        <span class="font-semibold text-[#63534B] min-w-[120px]">${col}:</span>
        <span class="diff-old">${item.changes[col].old || '(trống)'}</span>
        <span class="text-[#96847B]">➔</span>
        <span class="diff-new">${item.changes[col].new || '(trống)'}</span>
      </div>
    `).join('');

    const card = document.createElement('div');
    card.className = 'p-3 bg-[#FCFAF6] rounded-xl border border-[#BE7B68]/15';
    card.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-bold text-[#BE7B68] bg-[#F7EBE8] px-2 py-0.5 rounded-full">Dòng #${item.row_index}</span>
        <span class="text-[11px] text-[#96847B]">${Object.keys(item.changes).length} trường được sửa</span>
      </div>
      <div class="space-y-1">${changesHtml}</div>
    `;
    container.appendChild(card);
  });
}

function renderAuditLog(logItems) {
  const container = document.getElementById('audit-log-list');
  container.innerHTML = '';

  logItems.forEach((item, idx) => {
    const el = document.createElement('div');
    el.className = 'flex items-start gap-3 p-3 bg-[#FCFAF6] rounded-xl border border-[#BE7B68]/10';
    el.innerHTML = `
      <div class="w-6 h-6 rounded-full bg-[#BE7B68]/15 text-[#BE7B68] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
        ${idx + 1}
      </div>
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-[#BE7B68] bg-[#F7EBE8] px-2 py-0.5 rounded-full">${item.badge}</span>
        </div>
        <p class="text-xs text-[#63534B] mt-1">${item.message}</p>
      </div>
    `;
    container.appendChild(el);
  });
}

// =================== FINAL DASHBOARD & VISUALS ===================
function renderDashboard(data) {
  // Update Business context on dashboard
  const dashName = document.getElementById('dash-business-name');
  const dashType = document.getElementById('dash-business-type');
  if (dashName && data.summary.business_name) {
    dashName.innerText = `${data.summary.business_name} Data Dashboard`;
  }
  if (dashType && data.summary.business_type) {
    dashType.innerText = data.summary.business_type;
  }

  // Top metric cards
  document.getElementById('dash-records-val').innerText = data.summary.total_records;
  document.getElementById('dash-compliance-val').innerText = data.summary.compliance_score;
  document.getElementById('dash-fixed-val').innerText = data.summary.fixed_issues;

  // Card 2 (Dynamic: Total Revenue, Quantity, or Phone)
  if (data.card2) {
    const card2Icon = document.getElementById('dash-card2-icon');
    const card2Title = document.getElementById('dash-card2-title');
    const card2Val = document.getElementById('dash-card2-val');
    const card2Sub = document.getElementById('dash-card2-sub');
    if (card2Icon) card2Icon.innerText = data.card2.icon || '💰';
    if (card2Title) card2Title.innerText = data.card2.title || 'Tổng doanh thu';
    if (card2Val) card2Val.innerText = data.card2.val || '0 đ';
    if (card2Sub) card2Sub.innerText = data.card2.sub || 'Doanh thu chuẩn hóa';
  }

  // Card 5 (Dynamic: Product Count, Categories, or Issues)
  if (data.card5) {
    const card5Icon = document.getElementById('dash-card5-icon');
    const card5Title = document.getElementById('dash-card5-title');
    const card5Val = document.getElementById('dash-card5-val');
    const card5Sub = document.getElementById('dash-card5-sub');
    if (card5Icon) card5Icon.innerText = data.card5.icon || '🏷️';
    if (card5Title) card5Title.innerText = data.card5.title || 'Mặt hàng';
    if (card5Val) card5Val.innerText = data.card5.val || '0';
    if (card5Sub) card5Sub.innerText = data.card5.sub || 'Không còn lỗi nào';
  }

  // Wave Chart Title & Subtitle & Dynamic Legends
  if (data.wave_chart) {
    const waveTitle = document.getElementById('dash-wave-title');
    const waveSub = document.getElementById('dash-wave-sub');
    const waveLegends = document.getElementById('dash-wave-legends');
    if (waveTitle && data.wave_chart.title) waveTitle.innerText = data.wave_chart.title;
    if (waveSub && data.wave_chart.sub) waveSub.innerText = data.wave_chart.sub;

    if (waveLegends && data.wave_chart.legends) {
      const colors = ['#BE7B68', '#DFAB7B', '#7E9682'];
      waveLegends.innerHTML = data.wave_chart.legends.map((leg, idx) => `
        <span class="inline-flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-full" style="background-color: ${colors[idx % colors.length]};"></span>
          <span>${leg}</span>
        </span>
      `).join('');
    }
  }

  // Donut Chart Title & Subtitle
  if (data.donut_chart) {
    const donutTitle = document.getElementById('dash-donut-title');
    const donutSub = document.getElementById('dash-donut-sub');
    if (donutTitle && data.donut_chart.title) donutTitle.innerText = data.donut_chart.title;
    if (donutSub && data.donut_chart.sub) donutSub.innerText = data.donut_chart.sub;
  }

  // Upcoming items card list
  const upcomingContainer = document.getElementById('dash-upcoming-list');
  upcomingContainer.innerHTML = '';
  data.upcoming_items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'flex items-center justify-between py-2 border-b border-[#BE7B68]/10 last:border-0 text-xs';
    div.innerHTML = `
      <span class="text-[#63534B]">${item.title}</span>
      <span class="font-bold text-[#BE7B68]">${item.count}</span>
    `;
    upcomingContainer.appendChild(div);
  });

  // Summary description
  const summaryDesc = document.getElementById('dash-summary-desc');
  if (summaryDesc && data.summary && data.summary.summary_desc) {
    summaryDesc.innerText = data.summary.summary_desc;
  }

  // Render Charts matching the image!
  renderWaveChart(data.wave_chart);
  renderDonutChart(data.donut_chart);

  // Render Full Table with search
  window.currentCleanedFullData = data.table_data;
  window.currentCleanedColumns = data.columns;
  renderTable('final-data-table', data.table_data.slice(0, 30), data.columns);

  // Setup search filter for final table
  const searchInput = document.getElementById('final-table-search');
  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderTable('final-data-table', window.currentCleanedFullData.slice(0, 30), window.currentCleanedColumns);
      return;
    }
    const filtered = window.currentCleanedFullData.filter(row => {
      return Object.values(row).some(v => String(v).toLowerCase().includes(q));
    });
    renderTable('final-data-table', filtered.slice(0, 30), window.currentCleanedColumns);
  });

  initIcons();
}

function renderWaveChart(waveData) {
  const ctx = document.getElementById('waveChartCanvas').getContext('2d');
  if (state.charts.waveChart) {
    state.charts.waveChart.destroy();
  }

  // Smooth gradients in terracotta, caramel sand, and sage
  const gradTerracotta = ctx.createLinearGradient(0, 0, 0, 240);
  gradTerracotta.addColorStop(0, 'rgba(190, 123, 104, 0.7)');
  gradTerracotta.addColorStop(1, 'rgba(190, 123, 104, 0.15)');

  const gradSand = ctx.createLinearGradient(0, 0, 0, 240);
  gradSand.addColorStop(0, 'rgba(223, 171, 123, 0.75)');
  gradSand.addColorStop(1, 'rgba(223, 171, 123, 0.18)');

  const gradSage = ctx.createLinearGradient(0, 0, 0, 240);
  gradSage.addColorStop(0, 'rgba(126, 150, 130, 0.7)');
  gradSage.addColorStop(1, 'rgba(126, 150, 130, 0.15)');

  const leg1 = (waveData.legends && waveData.legends[0]) ? waveData.legends[0] : 'Số lượt đơn';
  const leg2 = (waveData.legends && waveData.legends[1]) ? waveData.legends[1] : 'Sản lượng';
  const leg3 = (waveData.legends && waveData.legends[2]) ? waveData.legends[2] : 'Doanh số';

  state.charts.waveChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: waveData.labels,
      datasets: [
        {
          label: leg1,
          data: waveData.series1,
          borderColor: '#BE7B68',
          backgroundColor: gradTerracotta,
          borderWidth: 2.2,
          fill: true,
          tension: 0.45,
          pointRadius: 0
        },
        {
          label: leg2,
          data: waveData.series2,
          borderColor: '#DFAB7B',
          backgroundColor: gradSand,
          borderWidth: 2,
          fill: true,
          tension: 0.45,
          pointRadius: 0
        },
        {
          label: leg3,
          data: waveData.series3,
          borderColor: '#7E9682',
          backgroundColor: gradSage,
          borderWidth: 2,
          fill: true,
          tension: 0.45,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#3A2E2B',
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 11 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              const idx = context.dataIndex;
              const dsIdx = context.datasetIndex;
              const dsLabel = context.dataset.label || '';
              if (dsIdx === 0) {
                const count = waveData.series1_raw ? waveData.series1_raw[idx] : waveData.series1[idx];
                return ` ${dsLabel}: ${count} đơn`;
              } else if (dsIdx === 1) {
                const qty = waveData.series2_raw ? waveData.series2_raw[idx] : waveData.series2[idx];
                return ` ${dsLabel}: ${qty} SP`;
              } else {
                const rev = waveData.series3_raw ? waveData.series3_raw[idx] : waveData.series3[idx];
                let revFmt = rev;
                if (typeof rev === 'number') {
                  revFmt = rev >= 1e6 ? `${(rev/1e6).toFixed(1)} Tr đ` : `${Math.round(rev).toLocaleString()} đ`;
                }
                return ` ${dsLabel}: ${revFmt}`;
              }
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#96847B', font: { size: 11 } }
        },
        y: {
          grid: { color: 'rgba(190, 123, 104, 0.08)' },
          ticks: { color: '#96847B', font: { size: 11 } }
        }
      }
    }
  });
}

function renderDonutChart(donutData) {
  const ctx = document.getElementById('donutChartCanvas').getContext('2d');
  if (state.charts.donutChart) {
    state.charts.donutChart.destroy();
  }

  const colors = ['#7E9682', '#BE7B68', '#DFAB7B', '#B4998C', '#D49586', '#A38476'];

  state.charts.donutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: donutData.labels,
      datasets: [{
        data: donutData.values,
        backgroundColor: colors.slice(0, donutData.labels.length),
        borderWidth: 2,
        borderColor: '#FFFFFF',
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'right',
          labels: {
            boxWidth: 10,
            usePointStyle: true,
            pointStyle: 'circle',
            font: { size: 11 },
            color: '#63534B'
          }
        },
        tooltip: {
          backgroundColor: '#3A2E2B',
          titleFont: { size: 12, weight: 'bold' },
          bodyFont: { size: 11 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const val = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? Math.round((val / total) * 100) : 0;
              return ` ${label}: ${val} giao dịch (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

// =================== EXPORT & RESET ===================
function setupExport() {
  const triggerDocxExport = () => {
    window.location.href = '/api/export/docx';
    showToast('Đang tạo và tải xuống bản Báo cáo Word (.docx) chuyên nghiệp...', 'success');
  };

  const btnExportDocx = document.getElementById('btn-export-docx');
  if (btnExportDocx) {
    btnExportDocx.addEventListener('click', triggerDocxExport);
  }

  const btnCardExportDocx = document.getElementById('btn-card-export-docx');
  if (btnCardExportDocx) {
    btnCardExportDocx.addEventListener('click', triggerDocxExport);
  }

  document.getElementById('btn-export-excel').addEventListener('click', () => {
    window.location.href = '/api/export/xlsx';
    showToast('Đang tải xuống tệp Excel hoàn thiện...', 'success');
  });

  document.getElementById('btn-export-csv').addEventListener('click', () => {
    window.location.href = '/api/export/csv';
    showToast('Đang tải xuống tệp CSV...', 'success');
  });

  document.getElementById('btn-export-json').addEventListener('click', () => {
    window.location.href = '/api/export/json';
    showToast('Đang tải xuống tệp JSON...', 'success');
  });

  // Reset Button
  document.getElementById('btn-reset-workflow').addEventListener('click', async () => {
    if (confirm('Bạn có chắc chắn muốn làm mới và xử lý tệp dữ liệu khác không?')) {
      await fetch('/api/reset', { method: 'POST' });
      window.location.reload();
    }
  });
}

// =================== HELPER UTILITIES ===================
function renderTable(tableId, rows, columns) {
  const table = document.getElementById(tableId);
  if (!table) return;

  if (!rows || rows.length === 0) {
    table.innerHTML = `<tr><td class="text-center py-6 text-[#96847B]">Chưa có dữ liệu</td></tr>`;
    return;
  }

  const cols = columns || Object.keys(rows[0]);

  let headerHtml = '<thead><tr>';
  cols.forEach(col => {
    headerHtml += `<th>${col}</th>`;
  });
  headerHtml += '</tr></thead>';

  let bodyHtml = '<tbody>';
  rows.forEach(row => {
    bodyHtml += '<tr>';
    cols.forEach(col => {
      const rawVal = row[col] !== undefined && row[col] !== null ? row[col] : '';
      let displayVal = rawVal;
      if (typeof rawVal === 'number' && Number.isInteger(rawVal) && Math.abs(rawVal) >= 1000) {
        displayVal = rawVal.toLocaleString('vi-VN');
      }
      bodyHtml += `<td>${displayVal}</td>`;
    });
    bodyHtml += '</tr>';
  });
  bodyHtml += '</tbody>';

  table.innerHTML = headerHtml + bodyHtml;
}

function showLoader(msg = 'Đang xử lý...') {
  const el = document.getElementById('global-loader');
  document.getElementById('global-loader-text').innerText = msg;
  el.classList.remove('hidden');
}

function hideLoader() {
  document.getElementById('global-loader').classList.add('hidden');
}

function showProcessingModal(title = 'AI Agent Kẹo Cute đang làm việc...') {
  document.getElementById('ai-modal-title').innerText = title;
  document.getElementById('ai-process-modal').classList.remove('hidden');
}

function hideProcessingModal() {
  document.getElementById('ai-process-modal').classList.add('hidden');
}

function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  const bgColors = {
    success: 'bg-[#7E9682] text-white',
    error: 'bg-[#C0392B] text-white',
    warning: 'bg-[#DFAB7B] text-[#3A2E2B]',
    info: 'bg-[#BE7B68] text-white'
  };

  toast.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-2xl shadow-xl flex items-center gap-3 text-sm font-medium transition-all duration-300 transform translate-y-4 opacity-0 ${bgColors[type] || bgColors.info}`;
  toast.innerHTML = `<span>🍬</span><span>${msg}</span>`;

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  }, 20);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-4');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
