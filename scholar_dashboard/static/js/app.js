/**
 * UNISCHOLAR ANALYTICS PLATFORM — FRONTEND ENGINE
 * Connects modern dashboard UI with FastAPI scholar analytics engine.
 */

const state = {
  records: [],
  analytics: null,
  filter: {
    status: 'all',
    department: 'all',
    search: ''
  },
  pagination: {
    currentPage: 1,
    pageSize: 10
  },
  milestoneBannerDismissed: false,
  institution: 'University of Lagos',
  useMock: false,
  hasApiKey: false,
  uploadedRecords: [],
  activeModalStaff: null,
  deptChartInstance: null,
  distChartInstance: null,
  accountInfo: null
};

// Safe alias to prevent any undefined function reference
const updateKPIs = () => renderKPIs();

// DOM Elements
const elements = {
  statusPill: document.getElementById('statusPill'),
  statusText: document.getElementById('statusText'),
  institutionInput: document.getElementById('institutionInput'),
  mockToggle: document.getElementById('mockToggle'),
  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('fileInput'),
  sampleBtn: document.getElementById('sampleBtn'),
  runBtn: document.getElementById('runBtn'),
  uploadInfo: document.getElementById('uploadInfo'),
  uploadInfoText: document.getElementById('uploadInfoText'),
  progressContainer: document.getElementById('progressContainer'),
  progressFill: document.getElementById('progressFill'),
  progressStatus: document.getElementById('progressStatus'),
  progressPct: document.getElementById('progressPct'),
  
  // KPIs
  kpiTotalStaff: document.getElementById('kpiTotalStaff'),
  kpiMatchRate: document.getElementById('kpiMatchRate'),
  kpiTotalCitations: document.getElementById('kpiTotalCitations'),
  kpiAvgHIndex: document.getElementById('kpiAvgHIndex'),
  kpiVerifiedRatio: document.getElementById('kpiVerifiedRatio'),

  // Charts & Leaderboard
  deptChartCanvas: document.getElementById('deptChart'),
  distChartCanvas: document.getElementById('distChart'),
  leaderboardList: document.getElementById('leaderboardList'),

  // Table & Filters
  searchInput: document.getElementById('searchInput'),
  deptFilterSelect: document.getElementById('deptFilterSelect'),
  filterPills: document.querySelectorAll('.filter-pill'),
  tableBody: document.getElementById('rosterTableBody'),
  tableCountLabel: document.getElementById('tableCountLabel'),

  // Exports & Modals
  exportExcelBtn: document.getElementById('exportExcelBtn'),
  exportCsvBtn: document.getElementById('exportCsvBtn'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  settingsBtn: document.getElementById('settingsBtn'),
  configModal: document.getElementById('configModal'),
  candidateModal: document.getElementById('candidateModal'),
  candidateModalBody: document.getElementById('candidateModalBody'),
  candidateModalTitle: document.getElementById('candidateModalTitle'),

  // Credit / Quota elements
  creditBadge: document.getElementById('creditBadge'),
  creditText: document.getElementById('creditText'),
  creditAlertBanner: document.getElementById('creditAlertBanner'),
  creditAlertTitle: document.getElementById('creditAlertTitle'),
  creditAlertDesc: document.getElementById('creditAlertDesc'),
  creditAlertAction: document.getElementById('creditAlertAction'),
  modalSearchesLeft: document.getElementById('modalSearchesLeft'),
  modalPlanName: document.getElementById('modalPlanName'),
  modalMonthUsage: document.getElementById('modalMonthUsage'),
  modalAccountEmail: document.getElementById('modalAccountEmail'),
  modalCreditWarning: document.getElementById('modalCreditWarning'),
  refreshQuotaBtn: document.getElementById('refreshQuotaBtn'),

  // Individual profile search
  indivNameInput: document.getElementById('indivNameInput'),
  indivDeptInput: document.getElementById('indivDeptInput'),
  indivSubmitBtn: document.getElementById('indivSubmitBtn'),
  indivFeedback: document.getElementById('indivFeedback'),
  individualForm: document.getElementById('individualForm'),

  // Pagination elements
  paginationContainer: document.getElementById('paginationContainer'),
  paginationInfo: document.getElementById('paginationInfo'),
  prevPageBtn: document.getElementById('prevPageBtn'),
  nextPageBtn: document.getElementById('nextPageBtn'),
  pageNumbers: document.getElementById('pageNumbers'),

  // Milestone Banner elements
  milestoneBanner: document.getElementById('milestoneBanner'),
  milestoneBannerText: document.getElementById('milestoneBannerText'),
  milestoneDismissBtn: document.getElementById('milestoneDismissBtn'),
  milestoneDownloadCsvBtn: document.getElementById('milestoneDownloadCsvBtn'),
  milestoneDownloadExcelBtn: document.getElementById('milestoneDownloadExcelBtn')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  setupTheme();
  setupEventListeners();
  await checkSystemStatus();
});

// Setup Event Listeners
function setupEventListeners() {
  // Theme toggle
  elements.themeToggleBtn.addEventListener('click', toggleTheme);

  // Settings modal (also refreshes quota on open)
  elements.settingsBtn.addEventListener('click', () => onSettingsOpen());
  document.getElementById('saveConfigBtn').addEventListener('click', saveConfiguration);

  // Mock toggle
  elements.mockToggle.addEventListener('change', (e) => {
    state.useMock = e.target.checked;
    updateStatusPill();
  });

  // Institution input
  elements.institutionInput.addEventListener('change', (e) => {
    state.institution = e.target.value;
  });

  // Sample data button
  elements.sampleBtn.addEventListener('click', loadSampleData);

  // File upload drag & drop
  elements.dropzone.addEventListener('click', () => elements.fileInput.click());
  elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('drag-active');
  });
  elements.dropzone.addEventListener('dragleave', () => elements.dropzone.classList.remove('drag-active'));
  elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('drag-active');
    if (e.dataTransfer.files.length) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });
  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
      handleFileUpload(e.target.files[0]);
    }
  });

  // Run discovery
  elements.runBtn.addEventListener('click', startBatchDiscovery);

  // Table filtering
  elements.searchInput.addEventListener('input', (e) => {
    state.filter.search = e.target.value.toLowerCase();
    state.pagination.currentPage = 1;
    renderTable();
  });

  elements.deptFilterSelect.addEventListener('change', (e) => {
    state.filter.department = e.target.value;
    state.pagination.currentPage = 1;
    renderTable();
  });

  elements.filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      elements.filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.filter.status = pill.dataset.status;
      state.pagination.currentPage = 1;
      renderTable();
    });
  });

  // Pagination navigation
  if (elements.prevPageBtn) {
    elements.prevPageBtn.addEventListener('click', () => {
      if (state.pagination.currentPage > 1) {
        state.pagination.currentPage--;
        renderTable();
      }
    });
  }

  if (elements.nextPageBtn) {
    elements.nextPageBtn.addEventListener('click', () => {
      state.pagination.currentPage++;
      renderTable();
    });
  }

  // Exports
  elements.exportExcelBtn.addEventListener('click', () => window.location.href = '/api/export/excel');
  elements.exportCsvBtn.addEventListener('click', () => window.location.href = '/api/export/csv');

  if (elements.milestoneDownloadCsvBtn) {
    elements.milestoneDownloadCsvBtn.addEventListener('click', () => window.location.href = '/api/export/csv');
  }

  if (elements.milestoneDownloadExcelBtn) {
    elements.milestoneDownloadExcelBtn.addEventListener('click', () => window.location.href = '/api/export/excel');
  }

  // Close modals on click outside or close button
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(modal);
    });
  });
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-backdrop');
      if (modal) closeModal(modal);
    });
  });

  // Manual author ID modal input save
  document.getElementById('manualMatchBtn').addEventListener('click', saveManualMatch);

  // Credit badge opens settings modal
  elements.creditBadge.addEventListener('click', () => {
    openModal(elements.configModal);
    fetchAccountInfo();
  });

  // Refresh quota button inside modal
  elements.refreshQuotaBtn.addEventListener('click', fetchAccountInfo);

  // Credit alert action (switch to demo mode)
  elements.creditAlertAction.addEventListener('click', () => {
    state.useMock = true;
    elements.mockToggle.checked = true;
    updateStatusPill();
    updateCreditBadge();
    elements.creditAlertBanner.style.display = 'none';
  });
}

// Check Backend Status
async function checkSystemStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    state.hasApiKey = data.has_api_key;
    state.institution = data.institution || 'University of Lagos';
    elements.institutionInput.value = state.institution;
    
    if (!state.hasApiKey) {
      state.useMock = true;
      elements.mockToggle.checked = true;
    }
    updateStatusPill();

    // Fetch credit / quota info from the free /api/account endpoint
    await fetchAccountInfo();
  } catch (err) {
    console.error('Failed to connect to backend API:', err);
    elements.statusText.textContent = 'API Offline';
  }
}

function updateStatusPill() {
  elements.statusPill.className = 'status-pill';
  if (state.useMock) {
    elements.statusPill.classList.add('mock');
    elements.statusText.textContent = 'Mock / Demo Mode Active';
  } else if (state.hasApiKey) {
    elements.statusPill.classList.add('connected');
    elements.statusText.textContent = 'SerpApi Connected';
  } else {
    elements.statusText.textContent = 'SerpApi Key Needed (Using Demo)';
  }
}

// Fetch account / credit quota from the free SerpApi account endpoint
async function fetchAccountInfo() {
  try {
    const mockParam = state.useMock ? '&use_mock=true' : '';
    const res = await fetch(`/api/account?${mockParam}`);
    const data = await res.json();
    state.accountInfo = data;
    updateCreditBadge();
    updateModalAccountCard();
    showCreditAlertBanner();
  } catch (err) {
    console.error('Failed to fetch account/credit info:', err);
    elements.creditText.textContent = 'Credits: N/A';
  }
}

// Update topbar credit badge with remaining searches and severity color
function updateCreditBadge() {
  const info = state.accountInfo;
  const badge = elements.creditBadge;
  badge.className = 'credit-pill';

  if (!info) {
    elements.creditText.textContent = 'Credits: N/A';
    return;
  }

  if (info.is_mock || state.useMock) {
    badge.classList.add('mock');
    elements.creditText.textContent = '∞ Demo Mode';
    return;
  }

  const status = info.status || 'healthy';
  const left = info.total_searches_left;

  if (left === null || left === undefined) {
    elements.creditText.textContent = 'Credits: N/A';
    return;
  }

  badge.classList.add(status);
  elements.creditText.textContent = `${Number(left).toLocaleString()} left`;
}

// Update the account quota card inside the settings modal
function updateModalAccountCard() {
  const info = state.accountInfo;
  if (!info) return;

  const left = info.total_searches_left;
  const status = info.status || 'healthy';

  // Remaining searches
  elements.modalSearchesLeft.textContent = (left !== null && left !== undefined)
    ? Number(left).toLocaleString()
    : 'N/A';
  elements.modalSearchesLeft.className = 'account-item-val highlight';
  if (['low', 'critical', 'depleted'].includes(status)) {
    elements.modalSearchesLeft.classList.add(status);
  }

  // Plan name
  elements.modalPlanName.textContent = info.plan_name || '—';

  // Monthly usage
  if (info.searches_per_month && info.this_month_usage !== undefined) {
    elements.modalMonthUsage.textContent = `${Number(info.this_month_usage).toLocaleString()} / ${Number(info.searches_per_month).toLocaleString()}`;
  } else {
    elements.modalMonthUsage.textContent = info.this_month_usage !== undefined
      ? Number(info.this_month_usage).toLocaleString()
      : '—';
  }

  // Account email
  elements.modalAccountEmail.textContent = info.account_email || '—';

  // Warning text
  if (info.warning) {
    elements.modalCreditWarning.textContent = info.warning;
    elements.modalCreditWarning.className = 'account-card-warning';
    if (['critical', 'depleted'].includes(status)) {
      elements.modalCreditWarning.classList.add(status);
    }
    elements.modalCreditWarning.style.display = 'block';
  } else {
    elements.modalCreditWarning.style.display = 'none';
  }
}

// Show or hide the warning banner at the top of the ingestion panel
function showCreditAlertBanner() {
  const info = state.accountInfo;
  if (!info || !info.warning || info.is_mock || state.useMock) {
    elements.creditAlertBanner.style.display = 'none';
    return;
  }

  const status = info.status || '';
  elements.creditAlertBanner.className = 'credit-alert-banner';
  if (['critical', 'depleted'].includes(status)) {
    elements.creditAlertBanner.classList.add(status);
  }

  if (status === 'depleted') {
    elements.creditAlertTitle.textContent = '🚫 Credit Balance Depleted';
    elements.creditAlertDesc.textContent = info.warning;
  } else if (status === 'critical') {
    elements.creditAlertTitle.textContent = '🔴 Critically Low Credits';
    elements.creditAlertDesc.textContent = info.warning;
  } else {
    elements.creditAlertTitle.textContent = '⚠️ Low Credit Warning';
    elements.creditAlertDesc.textContent = info.warning;
  }

  elements.creditAlertBanner.style.display = 'flex';
}

// File Upload Handler
async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  elements.uploadInfo.style.display = 'block';
  elements.uploadInfoText.textContent = `Analyzing ${file.name}...`;

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    const data = await res.json();
    state.uploadedRecords = data.extracted_records;
    elements.uploadInfoText.textContent = `Loaded ${data.extracted_count} staff records from ${data.filename} (${data.detected_name_col || 'Name'} & ${data.detected_dept_col || 'Dept'})`;
    elements.runBtn.disabled = false;
    elements.runBtn.textContent = `🚀 Run Discovery for ${data.extracted_count} Staff`;
  } catch (err) {
    alert(`File upload error: ${err.message}`);
    elements.uploadInfo.style.display = 'none';
  }
}

// Load Pre-built Sample Data
async function loadSampleData() {
  try {
    const res = await fetch('/api/sample');
    const data = await res.json();
    state.uploadedRecords = data.extracted_records;
    elements.uploadInfo.style.display = 'block';
    elements.uploadInfoText.textContent = `Loaded sample chemistry & sciences roster (${data.extracted_count} faculty members)`;
    elements.runBtn.disabled = false;
    elements.runBtn.textContent = `🚀 Run Discovery for ${data.extracted_count} Staff`;
  } catch (err) {
    alert('Failed to load sample data.');
  }
}

// Start Batch Discovery
async function startBatchDiscovery() {
  if (!state.uploadedRecords || state.uploadedRecords.length === 0) {
    alert('Please upload a file or load sample data first.');
    return;
  }

  elements.runBtn.disabled = true;
  elements.progressContainer.classList.add('active');
  elements.progressFill.style.width = '0%';
  elements.progressPct.textContent = '0%';
  elements.progressStatus.textContent = 'Initializing discovery query engine...';

  // Poll progress in background
  const pollInterval = setInterval(async () => {
    try {
      const sRes = await fetch('/api/status');
      const sData = await sRes.json();
      elements.progressFill.style.width = `${sData.progress}%`;
      elements.progressPct.textContent = `${Math.round(sData.progress)}%`;
      elements.progressStatus.textContent = sData.current_status;
      if (!sData.is_running && sData.progress >= 100) {
        clearInterval(pollInterval);
      }
    } catch (e) {}
  }, 400);

  try {
    const res = await fetch('/api/discover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        records: state.uploadedRecords,
        institution: elements.institutionInput.value,
        use_mock: state.useMock
      })
    });

    clearInterval(pollInterval);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Discovery failed');
    }

    const data = await res.json();
    state.records = data.records;
    state.analytics = data.analytics;

    // Update account/credit info returned after discovery
    if (data.account) {
      state.accountInfo = data.account;
      updateCreditBadge();
      updateModalAccountCard();
      showCreditAlertBanner();
    }

    elements.progressFill.style.width = '100%';
    elements.progressPct.textContent = '100%';
    elements.progressStatus.textContent = 'Discovery completed!';

    setTimeout(() => {
      elements.progressContainer.classList.remove('active');
    }, 2500);

    renderAll();
  } catch (err) {
    clearInterval(pollInterval);
    alert(`Discovery failed: ${err.message}`);
    elements.progressContainer.classList.remove('active');
  } finally {
    elements.runBtn.disabled = false;
  }
}

// Render Entire Dashboard
function renderAll() {
  state.pagination.currentPage = 1;
  renderKPIs();
  populateDepartmentFilter();
  renderCharts();
  renderLeaderboard();
  renderTable();
  elements.exportExcelBtn.disabled = false;
  elements.exportCsvBtn.disabled = false;
}

// Render KPI Cards
function renderKPIs() {
  const kpis = state.analytics?.kpis || {};
  elements.kpiTotalStaff.textContent = kpis.total_staff || 0;
  elements.kpiMatchRate.textContent = `${kpis.match_rate || 0}%`;
  elements.kpiTotalCitations.textContent = (kpis.total_citations_all || 0).toLocaleString();
  elements.kpiAvgHIndex.textContent = kpis.avg_h_index || '0.0';
  elements.kpiVerifiedRatio.textContent = `${kpis.verified_count || 0} / ${kpis.total_staff || 0} Verified`;
}

// Populate Department Dropdown
function populateDepartmentFilter() {
  const depts = new Set(state.records.map(r => r.department || 'Unassigned'));
  elements.deptFilterSelect.innerHTML = '<option value="all">All Departments</option>';
  depts.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    elements.deptFilterSelect.appendChild(opt);
  });
}

// Render Charts with Chart.js
function renderCharts() {
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';

  // 1. Department Citations Chart — Display all extracted departments
  const deptData = state.analytics?.departments || [];
  const deptFullNames = deptData.map(d => d.department || 'Unassigned');
  const deptLabels = deptData.map(d => d.department && d.department.length > 20 ? d.department.substring(0, 18) + '...' : (d.department || 'Unassigned'));
  const deptCitations = deptData.map(d => d.total_citations || 0);

  if (state.deptChartInstance) {
    state.deptChartInstance.destroy();
  }

  state.deptChartInstance = new Chart(elements.deptChartCanvas, {
    type: 'bar',
    data: {
      labels: deptLabels,
      datasets: [{
        label: 'Total Citations',
        data: deptCitations,
        backgroundColor: 'rgba(59, 130, 246, 0.75)',
        borderColor: '#3b82f6',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: function(context) {
              const idx = context[0].dataIndex;
              return deptFullNames[idx] || context[0].label;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { color: textColor, font: { family: 'Inter', size: 11 } },
          grid: { display: false }
        },
        y: {
          ticks: { color: textColor, font: { family: 'Inter', size: 11 } },
          grid: { color: gridColor }
        }
      }
    }
  });

  // 2. h-Index Distribution Chart
  const dist = state.analytics?.distribution || { labels: [], counts: [] };
  if (state.distChartInstance) {
    state.distChartInstance.destroy();
  }

  state.distChartInstance = new Chart(elements.distChartCanvas, {
    type: 'doughnut',
    data: {
      labels: dist.labels,
      datasets: [{
        data: dist.counts,
        backgroundColor: [
          '#64748b', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#8b5cf6'
        ],
        borderWidth: 2,
        borderColor: isDark ? '#0f172a' : '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: textColor, font: { family: 'Inter', size: 11 }, boxWidth: 12 }
        }
      },
      cutout: '65%'
    }
  });
}

// Render Top Impact Leaderboard
function renderLeaderboard() {
  const leaders = state.analytics?.leaderboard || [];
  elements.leaderboardList.innerHTML = '';

  if (leaders.length === 0) {
    elements.leaderboardList.innerHTML = '<div class="empty-state"><p>No faculty metrics discovered yet.</p></div>';
    return;
  }

  leaders.forEach(item => {
    const row = document.createElement('div');
    row.className = 'leaderboard-row';
    const rankClass = item.rank === 1 ? 'top-1' : (item.rank === 2 ? 'top-2' : (item.rank === 3 ? 'top-3' : ''));
    const rankDisplay = item.rank === 1 ? '🥇' : (item.rank === 2 ? '🥈' : (item.rank === 3 ? '🥉' : item.rank));

    row.innerHTML = `
      <div class="leaderboard-author">
        <span class="leaderboard-rank ${rankClass}">${rankDisplay}</span>
        <div class="leaderboard-meta">
          <span class="leaderboard-name">${escapeHtml(item.staff_name)}</span>
          <span class="leaderboard-dept">${escapeHtml(item.department || 'General')}</span>
        </div>
      </div>
      <div class="leaderboard-stats">
        <div class="stat-group">
          <span class="stat-label">Citations</span>
          <span class="stat-num">${item.citations_all.toLocaleString()}</span>
        </div>
        <div class="stat-group">
          <span class="stat-label">h-Index</span>
          <span class="stat-num">${item.h_index_all}</span>
        </div>
        ${item.profile_url ? `<a href="${item.profile_url}" target="_blank" class="btn btn-secondary btn-sm" title="View Google Scholar">🔗</a>` : ''}
      </div>
    `;
    elements.leaderboardList.appendChild(row);
  });
}

// Render Staff Roster Table with Live Filtering & Pagination (10 per page)
function renderTable() {
  const filtered = state.records.filter(r => {
    // Search filter
    const matchesSearch = !state.filter.search || 
      (r.staff_name && r.staff_name.toLowerCase().includes(state.filter.search)) ||
      (r.profile_name && r.profile_name.toLowerCase().includes(state.filter.search)) ||
      (r.department && r.department.toLowerCase().includes(state.filter.search));

    // Department filter
    const matchesDept = state.filter.department === 'all' || r.department === state.filter.department;

    // Status filter
    let matchesStatus = true;
    const status = (r.match_status || '').toLowerCase();
    if (state.filter.status === 'verified') {
      matchesStatus = status === 'verified';
    } else if (state.filter.status === 'needs') {
      matchesStatus = status === 'needs verification';
    } else if (state.filter.status === 'unmatched') {
      matchesStatus = status === 'no profile found' || status.includes('error');
    }

    return matchesSearch && matchesDept && matchesStatus;
  });

  const pageSize = state.pagination.pageSize || 10;
  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  
  if (state.pagination.currentPage > totalPages) {
    state.pagination.currentPage = totalPages;
  }
  if (state.pagination.currentPage < 1) {
    state.pagination.currentPage = 1;
  }

  const startIdx = (state.pagination.currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, totalItems);
  const paged = filtered.slice(startIdx, endIdx);

  elements.tableBody.innerHTML = '';

  if (totalItems === 0) {
    elements.tableCountLabel.textContent = `Showing 0 faculty`;
    if (elements.paginationContainer) elements.paginationContainer.style.display = 'none';
    elements.tableBody.innerHTML = `
      <tr>
        <td colspan="9">
          <div class="empty-state">
            <span class="empty-icon">🔍</span>
            <p>No matching faculty records found.</p>
          </div>
        </td>
      </tr>
    `;
    checkMilestoneBanner();
    return;
  }

  // Update table count & pagination bar
  const isFiltered = totalItems !== state.records.length;
  elements.tableCountLabel.textContent = `Showing ${startIdx + 1}–${endIdx} of ${totalItems} faculty${isFiltered ? ` (${state.records.length} total)` : ''}`;

  if (elements.paginationContainer) {
    elements.paginationContainer.style.display = totalItems > pageSize ? 'flex' : 'none';
    if (elements.paginationInfo) {
      elements.paginationInfo.textContent = `Showing ${startIdx + 1}–${endIdx} of ${totalItems} faculty (Page ${state.pagination.currentPage} of ${totalPages})`;
    }
    if (elements.prevPageBtn) elements.prevPageBtn.disabled = (state.pagination.currentPage === 1);
    if (elements.nextPageBtn) elements.nextPageBtn.disabled = (state.pagination.currentPage === totalPages);

    if (elements.pageNumbers) {
      elements.pageNumbers.innerHTML = '';
      const startPage = Math.max(1, state.pagination.currentPage - 2);
      const endPage = Math.min(totalPages, startPage + 4);
      for (let p = startPage; p <= endPage; p++) {
        const btn = document.createElement('button');
        btn.className = `page-num-btn ${p === state.pagination.currentPage ? 'active' : ''}`;
        btn.textContent = p;
        btn.onclick = () => {
          state.pagination.currentPage = p;
          renderTable();
        };
        elements.pageNumbers.appendChild(btn);
      }
    }
  }

  paged.forEach(row => {
    const tr = document.createElement('tr');
    
    // Status Badge
    let badgeClass = 'badge-needs';
    let statusText = row.match_status || 'Needs verification';
    if (statusText.toLowerCase() === 'verified') {
      badgeClass = 'badge-verified';
    } else if (statusText.toLowerCase() === 'no profile found' || statusText.toLowerCase().includes('error')) {
      badgeClass = 'badge-unmatched';
    }

    tr.innerHTML = `
      <td>
        <div style="font-weight: 700; color: var(--text-main); font-size: 14px;">${escapeHtml(row.staff_name)}</div>
        ${row.profile_name && row.profile_name !== row.staff_name ? `<div style="font-size: 11px; color: var(--text-muted); font-weight: 500;">Scholar: ${escapeHtml(row.profile_name)}</div>` : ''}
        ${row.affiliation ? `<div style="font-size: 11px; color: var(--text-faint); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(row.affiliation)}">${escapeHtml(row.affiliation)}</div>` : ''}
      </td>
      <td>
        <span class="dept-badge">${escapeHtml(row.department || 'General')}</span>
      </td>
      <td style="text-align: right; font-weight: 700; color: var(--text-main); font-size: 14px;">
        ${(row.citations_all || 0).toLocaleString()}
      </td>
      <td style="text-align: right; font-weight: 600; color: var(--accent-primary); font-size: 14px;">
        ${(row.citations_recent || 0).toLocaleString()}
      </td>
      <td style="text-align: right; font-weight: 700; color: var(--text-main); font-size: 14px;">
        ${row.h_index_all || 0}
      </td>
      <td style="text-align: right; font-weight: 600; color: var(--accent-warning); font-size: 14px;">
        ${row.h_index_recent || 0}
      </td>
      <td style="text-align: right; font-weight: 700; color: var(--text-main); font-size: 14px;">
        ${row.i10_index_all || 0}
      </td>
      <td style="text-align: right; font-weight: 600; color: var(--accent-purple); font-size: 14px;">
        ${row.i10_index_recent || 0}
      </td>
      <td style="text-align: center;">
        <div style="display: flex; gap: 6px; justify-content: center; align-items: center; flex-wrap: wrap;">
          <span class="badge ${badgeClass}" style="cursor: pointer" onclick="toggleVerifyStatus('${row.id}')" title="Click to toggle status">
            ${statusText === 'Verified' ? '✓ Verified' : (statusText === 'Needs verification' ? '⚠ Review' : '✕ Unmatched')}
          </span>
          ${row.profile_url ? `<a href="${row.profile_url}" target="_blank" class="btn btn-secondary btn-xs" title="Open Google Scholar">🔗</a>` : ''}
          <button class="btn btn-secondary btn-xs" onclick="openDisambiguationModal('${row.id}')" title="Review candidate profiles">
            Review (${row.candidate_count || (row.candidates ? row.candidates.length : 0)})
          </button>
        </div>
      </td>
    `;
    elements.tableBody.appendChild(tr);
  });

  checkMilestoneBanner();
}

// 30+ Records Milestone Alert Banner Management
function checkMilestoneBanner() {
  if (!elements.milestoneBanner) return;
  const total = state.records.length;
  if (total >= 30 && !state.milestoneBannerDismissed) {
    if (elements.milestoneBannerText) {
      elements.milestoneBannerText.textContent = `You have accumulated ${total} faculty profiles in this session. We recommend downloading your report (CSV / Excel) to safeguard your data before proceeding.`;
    }
    elements.milestoneBanner.style.display = 'flex';
  } else {
    elements.milestoneBanner.style.display = 'none';
  }
}

window.dismissMilestoneBanner = function() {
  state.milestoneBannerDismissed = true;
  if (elements.milestoneBanner) {
    elements.milestoneBanner.style.display = 'none';
  }
};

// Add Individual Faculty Profile Handler
window.handleAddIndividual = async function() {
  if (!elements.indivNameInput) return;
  const name = elements.indivNameInput.value.trim();
  const dept = elements.indivDeptInput ? elements.indivDeptInput.value.trim() : '';
  if (!name) return;

  elements.indivSubmitBtn.disabled = true;
  const originalText = elements.indivSubmitBtn.textContent;
  elements.indivSubmitBtn.textContent = '⏳ Searching...';

  if (elements.indivFeedback) {
    elements.indivFeedback.style.display = 'block';
    elements.indivFeedback.className = 'individual-feedback info';
    elements.indivFeedback.textContent = `Searching Google Scholar profile for ${name}...`;
  }

  try {
    const res = await fetch('/api/individual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        department: dept,
        institution: elements.institutionInput.value.trim(),
        use_mock: state.useMock
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to search individual profile');
    }

    const data = await res.json();
    const newRec = data.record;

    // Insert into state.records at top if not present, or replace
    const existingIdx = state.records.findIndex(r => r.id === newRec.id || (r.staff_name && r.staff_name.toLowerCase() === newRec.staff_name.toLowerCase()));
    if (existingIdx >= 0) {
      state.records[existingIdx] = newRec;
    } else {
      state.records.unshift(newRec);
    }

    state.analytics = data.analytics;
    if (data.account) {
      state.accountInfo = data.account;
      updateCreditBadge();
      updateModalAccountCard();
      showCreditAlertBanner();
    }

    // Refresh all UI widgets & jump to page 1 for immediate visibility
    state.pagination.currentPage = 1;
    elements.exportExcelBtn.disabled = false;
    elements.exportCsvBtn.disabled = false;
    renderKPIs();
    renderCharts();
    renderLeaderboard();
    populateDepartmentFilter();
    renderTable();

    // Positive feedback
    if (elements.indivFeedback) {
      elements.indivFeedback.className = 'individual-feedback success';
      elements.indivFeedback.textContent = `✓ Successfully added ${newRec.staff_name} (${(newRec.citations_all || 0).toLocaleString()} Citations, h-index ${newRec.h_index_all || 0})`;
    }
    elements.indivNameInput.value = '';
    if (elements.indivDeptInput) elements.indivDeptInput.value = '';

    setTimeout(() => {
      if (elements.indivFeedback) elements.indivFeedback.style.display = 'none';
    }, 5000);

  } catch (err) {
    console.error('Error adding individual profile:', err);
    if (elements.indivFeedback) {
      elements.indivFeedback.className = 'individual-feedback error';
      elements.indivFeedback.textContent = `❌ ${err.message}`;
    }
  } finally {
    elements.indivSubmitBtn.disabled = false;
    elements.indivSubmitBtn.textContent = originalText;
  }
};

// Toggle Verification Status
window.toggleVerifyStatus = async function(staffId) {
  const staff = state.records.find(r => r.id === staffId);
  if (!staff) return;

  const newStatus = staff.match_status === 'Verified' ? 'Needs verification' : 'Verified';
  try {
    const res = await fetch('/api/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        staff_id: staffId,
        status: newStatus
      })
    });
    const data = await res.json();
    staff.match_status = newStatus;
    state.analytics = data.analytics;
    renderKPIs();
    renderTable();
  } catch (err) {
    alert('Failed to update status');
  }
};

// Open Disambiguation Modal
window.openDisambiguationModal = function(staffId) {
  const staff = state.records.find(r => r.id === staffId);
  if (!staff) return;

  state.activeModalStaff = staff;
  elements.candidateModalTitle.textContent = `Candidate Review: ${staff.staff_name}`;
  elements.candidateModalBody.innerHTML = '';

  const candidates = staff.candidates || [];
  if (candidates.length === 0) {
    elements.candidateModalBody.innerHTML = `
      <div class="empty-state">
        <p>No candidate profiles were automatically discovered for this faculty member.</p>
        <p style="font-size: 12px; color: var(--text-muted)">You can paste their Google Scholar Author ID below.</p>
      </div>
    `;
  } else {
    candidates.forEach((cand, idx) => {
      const isCurrent = cand.author_id === staff.author_id;
      const card = document.createElement('div');
      card.className = `candidate-card ${isCurrent ? 'selected' : ''}`;
      card.innerHTML = `
        <div class="candidate-info">
          <span class="candidate-name">${escapeHtml(cand.name)} ${isCurrent ? '(Active Match)' : ''}</span>
          <span class="candidate-affil">${escapeHtml(cand.affiliations || 'No affiliation stated')}</span>
          ${cand.email ? `<span class="candidate-email">✉️ ${escapeHtml(cand.email)}</span>` : ''}
          ${cand.author_id ? `<span style="font-size: 10px; color: var(--text-faint)">ID: ${cand.author_id}</span>` : ''}
        </div>
        <div>
          ${isCurrent 
            ? '<span class="badge badge-verified">✓ Selected</span>' 
            : `<button class="btn btn-primary btn-sm" onclick="selectCandidate('${cand.author_id}', '${escapeHtml(cand.name)}', '${escapeHtml(cand.affiliations || '')}')">Select This</button>`
          }
        </div>
      `;
      elements.candidateModalBody.appendChild(card);
    });
  }

  document.getElementById('manualAuthorIdInput').value = staff.author_id || '';
  openModal(elements.candidateModal);
};

// Select Candidate from Modal
window.selectCandidate = async function(authorId, name, affiliation) {
  if (!state.activeModalStaff) return;
  try {
    const res = await fetch('/api/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        staff_id: state.activeModalStaff.id,
        author_id: authorId,
        profile_name: name,
        affiliation: affiliation,
        status: 'Verified',
        use_mock: state.useMock
      })
    });
    const data = await res.json();
    
    // Update local record
    const idx = state.records.findIndex(r => r.id === state.activeModalStaff.id);
    if (idx !== -1) {
      state.records[idx] = data.record;
    }
    state.analytics = data.analytics;

    closeModal(elements.candidateModal);
    renderAll();
  } catch (err) {
    alert(`Failed to assign profile: ${err.message}`);
  }
};

// Save Manual Author ID Match
async function saveManualMatch() {
  const manualId = document.getElementById('manualAuthorIdInput').value.trim();
  if (!manualId || !state.activeModalStaff) return;

  // Extract author ID if full URL pasted (e.g. ?user=XXXXX)
  let cleanId = manualId;
  if (manualId.includes('user=')) {
    const match = manualId.match(/user=([^&]+)/);
    if (match) cleanId = match[1];
  }

  await selectCandidate(cleanId, state.activeModalStaff.staff_name, state.activeModalStaff.department);
}

// Modal Helpers
function openModal(modal) {
  modal.classList.add('open');
}

function closeModal(modal) {
  modal.classList.remove('open');
}

// Save Configuration
async function saveConfiguration() {
  const apiKey = document.getElementById('configApiKey').value.trim();
  const institution = document.getElementById('configInstitution').value.trim();

  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, institution: institution })
    });
    closeModal(elements.configModal);
    await checkSystemStatus();
    alert('Configuration saved.');
  } catch (err) {
    alert('Failed to save configuration.');
  }
}

// Settings modal also triggers fresh account fetch when opened
function onSettingsOpen() {
  openModal(elements.configModal);
  fetchAccountInfo();
}

// Theme Toggle
function setupTheme() {
  const saved = localStorage.getItem('unischolar_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('unischolar_theme', next);
  updateThemeIcon(next);
  if (state.analytics) {
    renderCharts();
  }
}

function updateThemeIcon(theme) {
  elements.themeToggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Utility: Escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
