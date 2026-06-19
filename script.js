document.addEventListener('DOMContentLoaded', function() {
    const API_BASE = '/api';
    let token = localStorage.getItem('token');
    let username = localStorage.getItem('username');
    let currentTab = 'dashboard';
    let logsOffset = 0;
    const LOGS_LIMIT = 20;
    let logsTotal = 0;

    document.getElementById('currentDate').textContent = new Date().toLocaleDateString('ru-RU', {day:'numeric',month:'short',year:'numeric'});

    function checkAuth() {
        if (token) {
            document.getElementById('loginOverlay').style.display = 'none';
            document.getElementById('avatar').textContent = username ? username[0].toUpperCase() : 'A';
            loadDashboard();
            loadLogs();
            loadUrlStats();
            loadParsedFiles();
            return true;
        } else {
            document.getElementById('loginOverlay').style.display = 'flex';
            return false;
        }
    }

    document.getElementById('loginBtn').addEventListener('click', function() {
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value.trim();
        if (!username || !password) { showNotification('Заполните все поля', 'error'); return; }
        fetch(API_BASE + '/login', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({username, password})
        })
        .then(res => res.json())
        .then(data => {
            if (data.token) {
                token = data.token;
                username = data.username;
                localStorage.setItem('token', token);
                localStorage.setItem('username', username);
                document.getElementById('loginOverlay').style.display = 'none';
                document.getElementById('avatar').textContent = username[0].toUpperCase();
                loadDashboard(); loadLogs(); loadUrlStats(); loadParsedFiles();
                showNotification('Вход выполнен', 'success');
            } else {
                showNotification(data.error || 'Ошибка входа', 'error');
            }
        })
        .catch(() => showNotification('Ошибка соединения', 'error'));
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const tab = this.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById('tab-'+tab).classList.add('active');
            currentTab = tab;
            if (tab === 'dashboard') loadDashboard();
            if (tab === 'logs') loadLogs();
            if (tab === 'urlstats') loadUrlStats();
            if (tab === 'parser') loadParsedFiles();
        });
    });

    function apiFetch(url, opts={}) {
        opts.headers = opts.headers || {};
        opts.headers['Authorization'] = 'Bearer ' + token;
        return fetch(API_BASE + url, opts).then(res => {
            if (res.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                token = null;
                document.getElementById('loginOverlay').style.display = 'flex';
                showNotification('Сессия истекла', 'error');
                return Promise.reject('Unauthorized');
            }
            return res.json();
        });
    }

    function loadDashboard() {
        if (!token) return;
        apiFetch('/stats').then(data => {
            if (data.total_entries !== undefined) {
                document.getElementById('totalEntries').textContent = data.total_entries;
                document.getElementById('uniqueIps').textContent = data.unique_ips;
                document.getElementById('uniqueUrls').textContent = data.unique_urls;
            }
        }).catch(() => {});
    }

    function loadLogs() {
        if (!token) return;
        const ip = document.getElementById('filterIp').value;
        const dateFrom = document.getElementById('filterDateFrom').value;
        const dateTo = document.getElementById('filterDateTo').value;
        const keyword = document.getElementById('filterKeyword').value;
        const groupBy = document.getElementById('filterGroupBy').value;
        const url = document.getElementById('filterUrl').value;
        const params = new URLSearchParams();
        if (ip) params.append('ip', ip);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        if (keyword) params.append('keyword', keyword);
        if (groupBy) params.append('group_by', groupBy);
        if (url) params.append('url', url);
        params.append('limit', LOGS_LIMIT);
        params.append('offset', logsOffset);

        apiFetch('/logs?' + params.toString()).then(data => {
            if (data.data) {
                const tbody = document.getElementById('logsTableBody');
                tbody.innerHTML = '';
                if (data.data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:rgba(255,255,255,0.2);padding:2rem">Нет записей</td></tr>';
                } else {
                    data.data.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `<td class="monospace">${row.ip}</td><td>${row.date ? row.date.slice(0,16) : ''}</td><td>${row.method || ''}</td><td style="word-break:break-all">${row.url}</td><td>${row.status}</td><td>${row.size}</td>`;
                        tbody.appendChild(tr);
                    });
                }
                logsTotal = data.total || 0;
                document.getElementById('logsPagination').textContent = `Записи ${logsOffset+1}-${Math.min(logsOffset+LOGS_LIMIT, logsTotal)} из ${logsTotal}`;
                document.getElementById('logsPrev').disabled = (logsOffset === 0);
                document.getElementById('logsNext').disabled = (logsOffset + LOGS_LIMIT >= logsTotal);
            }
        }).catch(() => {});
    }

    document.getElementById('applyLogsFilter').addEventListener('click', function() {
        logsOffset = 0;
        loadLogs();
    });
    document.getElementById('logsPrev').addEventListener('click', function() {
        if (logsOffset > 0) { logsOffset -= LOGS_LIMIT; if (logsOffset < 0) logsOffset = 0; loadLogs(); }
    });
    document.getElementById('logsNext').addEventListener('click', function() {
        if (logsOffset + LOGS_LIMIT < logsTotal) { logsOffset += LOGS_LIMIT; loadLogs(); }
    });

    function loadUrlStats() {
        if (!token) return;
        apiFetch('/urls').then(data => {
            const tbody = document.getElementById('urlStatsBody');
            tbody.innerHTML = '';
            if (data.data && data.data.length) {
                data.data.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td style="word-break:break-all">${item.url}</td><td class="text-center" style="font-weight:600;color:#f0f4ff">${item.count}</td>`;
                    tr.style.cursor = 'pointer';
                    tr.addEventListener('click', function() {
                        document.getElementById('filterUrl').value = item.url;
                        document.querySelector('[data-tab="logs"]').click();
                        logsOffset = 0;
                        loadLogs();
                    });
                    tbody.appendChild(tr);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;color:rgba(255,255,255,0.2);padding:2rem">Нет данных</td></tr>';
            }
        }).catch(() => {});
    }

    function loadParsedFiles() {
        if (!token) return;
        apiFetch('/parse/files').then(data => {
            const ul = document.getElementById('parsedFilesList');
            ul.innerHTML = '';
            if (data.files && data.files.length) {
                data.files.forEach(f => { const li = document.createElement('li'); li.textContent = f; ul.appendChild(li); });
            } else {
                ul.innerHTML = '<li style="color:rgba(255,255,255,0.2)">Нет загруженных файлов</li>';
            }
        }).catch(() => {});
    }

    let parseInterval = null;
    document.getElementById('startParseBtn').addEventListener('click', function() {
        if (!token) return;
        apiFetch('/parse', {method:'POST'}).then(data => {
            if (data.task_id) {
                showNotification('Задача парсинга запущена', 'success');
                document.getElementById('parseStatus').textContent = 'Статус: запущена, ожидайте...';
                if (parseInterval) clearInterval(parseInterval);
                parseInterval = setInterval(() => pollParseStatus(data.task_id), 1000);
            }
        }).catch(() => showNotification('Ошибка запуска парсинга', 'error'));
    });

    function pollParseStatus(taskId) {
        apiFetch('/parse/status/' + taskId).then(data => {
            if (data.status) {
                document.getElementById('parseStatus').textContent = `Статус: ${data.status} (${data.progress || 0}%) – ${data.message || ''}`;
                document.getElementById('parseProgressFill').style.width = (data.progress || 0) + '%';
                if (data.processed) {
                    document.getElementById('parseFileSize').textContent = data.processed + ' files';
                }
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(parseInterval);
                    if (data.status === 'completed') {
                        showNotification('Парсинг завершён', 'success');
                        loadDashboard();
                        loadLogs();
                        loadUrlStats();
                        loadParsedFiles();
                    }
                }
            }
        }).catch(() => {});
    }

    function showNotification(msg, type='info') {
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        const div = document.createElement('div');
        div.className = 'notification ' + (type === 'error' ? 'error' : type === 'success' ? 'success' : '');
        div.innerHTML = `<i class="fas ${type==='error'?'fa-exclamation-circle':type==='success'?'fa-check-circle':'fa-info-circle'}"></i> ${msg}`;
        document.body.appendChild(div);
        setTimeout(() => { div.style.opacity = '0'; setTimeout(() => div.remove(), 300); }, 4000);
    }

    checkAuth();

    document.getElementById('loginPassword').addEventListener('keydown', function(e) { if (e.key==='Enter') document.getElementById('loginBtn').click(); });
    document.getElementById('loginUsername').addEventListener('keydown', function(e) { if (e.key==='Enter') document.getElementById('loginBtn').click(); });
});
