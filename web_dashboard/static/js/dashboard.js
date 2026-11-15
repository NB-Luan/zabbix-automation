// dashboard.js - Realtime Operations Center & Remote Chaos Lab Controller

let responseChart = null;
let connChart = null;
let countdown = 5;
let logPollTimer = null;
let isSimulationActive = false;

// Initialize when DOM ready
document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initCharts();
    
    // Initial fetch
    fetchMetrics();
    fetchProblems();
    fetchLogs();

    // 5-second polling interval for metrics & problems
    setInterval(() => {
        countdown--;
        if (countdown <= 0) {
            countdown = 5;
            fetchMetrics();
            fetchProblems();
            flashRefreshDot();
        }
        document.getElementById("countdownSec").innerText = `${countdown}s`;
    }, 1000);

    // 2-second polling for terminal logs
    setInterval(fetchLogs, 2000);
});

// =============================================================================
// Live Clock
// =============================================================================
function initClock() {
    const updateTime = () => {
        const now = new Date();
        const str = now.toLocaleTimeString('en-GB', { hour12: false });
        const el = document.getElementById("currentTime");
        if (el) el.innerText = str;
    };
    updateTime();
    setInterval(updateTime, 1000);
}

function flashRefreshDot() {
    const dot = document.getElementById("refreshDot");
    if (!dot) return;
    dot.classList.add("scale-150", "bg-white");
    setTimeout(() => {
        dot.classList.remove("scale-150", "bg-white");
    }, 300);
}

// =============================================================================
// Chart.js Setup
// =============================================================================
function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#e2e8f0',
                bodyColor: '#38bdf8',
                borderColor: '#334155',
                borderWidth: 1,
                padding: 10,
                displayColors: false
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.04)', drawBorder: false },
                ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
            },
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } }
            }
        }
    };

    // Latency Chart
    const ctxResp = document.getElementById('responseChart').getContext('2d');
    const gradResp = ctxResp.createLinearGradient(0, 0, 0, 240);
    gradResp.addColorStop(0, 'rgba(56, 189, 248, 0.35)');
    gradResp.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

    responseChart = new Chart(ctxResp, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Response Time (ms)',
                data: [],
                borderColor: '#38bdf8',
                backgroundColor: gradResp,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: '#38bdf8'
            }]
        },
        options: commonOptions
    });

    // Connections Chart
    const ctxConn = document.getElementById('connChart').getContext('2d');
    const gradConn = ctxConn.createLinearGradient(0, 0, 0, 240);
    gradConn.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
    gradConn.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    connChart = new Chart(ctxConn, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Active Connections',
                data: [],
                borderColor: '#10b981',
                backgroundColor: gradConn,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: '#10b981'
            }]
        },
        options: commonOptions
    });
}

// =============================================================================
// Metrics Fetcher & Card Updates
// =============================================================================
async function fetchMetrics() {
    try {
        const res = await fetch("/api/metrics");
        const json = await res.json();
        if (json.status !== "ok") return;

        const d = json.data;

        // Update Values
        document.getElementById("val_response_ms").innerText = d.response_ms;
        document.getElementById("val_active_conn").innerText = d.active_conn;
        document.getElementById("val_error_5xx").innerText = d.error_5xx;
        document.getElementById("val_zombie_procs").innerText = d.zombie_procs;
        document.getElementById("val_failed_units").innerText = d.failed_units;
        document.getElementById("val_disk_io_util").innerText = d.disk_io_util;

        // Card 1: Response Time Badge
        const badgeResp = document.getElementById("badge_response_ms");
        if (d.response_ms > 500) {
            badgeResp.className = "text-amber-400 font-semibold flex items-center gap-1";
            badgeResp.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Slow (${d.response_ms}ms)`;
        } else {
            badgeResp.className = "text-emerald-400 font-semibold flex items-center gap-1";
            badgeResp.innerHTML = `<i class="fa-solid fa-check text-[10px]"></i> Fast`;
        }

        // Card 3: 5xx Error Badge
        const badge5xx = document.getElementById("badge_error_5xx");
        if (d.error_5xx > 0) {
            badge5xx.className = "text-rose-400 font-semibold flex items-center gap-1";
            badge5xx.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Alert!`;
        } else {
            badge5xx.className = "text-emerald-400 font-semibold";
            badge5xx.innerText = "Zero Error";
        }

        // Card 4: Zombie Procs Badge
        const badgeZombie = document.getElementById("badge_zombie_procs");
        if (d.zombie_procs > 0) {
            badgeZombie.className = "text-amber-400 font-semibold flex items-center gap-1";
            badgeZombie.innerHTML = `<i class="fa-solid fa-skull"></i> Found ${d.zombie_procs}`;
        } else {
            badgeZombie.className = "text-emerald-400 font-semibold";
            badgeZombie.innerText = "Clean";
        }

        // Card 5: Failed Units Badge
        const badgeFailed = document.getElementById("badge_failed_units");
        if (d.failed_units > 0) {
            badgeFailed.className = "text-rose-400 font-semibold flex items-center gap-1";
            badgeFailed.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${d.failed_units} Failed`;
        } else {
            badgeFailed.className = "text-emerald-400 font-semibold";
            badgeFailed.innerText = "Normal";
        }

        // Update Charts (Keep last 15 rolling points)
        updateChartPoint(responseChart, d.updated_at, d.response_ms);
        updateChartPoint(connChart, d.updated_at, d.active_conn);

    } catch (err) {
        console.error("fetchMetrics error:", err);
    }
}

function updateChartPoint(chart, label, value) {
    if (!chart) return;
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);
    if (chart.data.labels.length > 15) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update('none');
}

// =============================================================================
// Zabbix Problems Fetcher
// =============================================================================
async function fetchProblems() {
    try {
        const res = await fetch("/api/problems");
        const json = await res.json();
        if (json.status !== "ok") return;

        const problems = json.problems || [];
        const banner = document.getElementById("healthBanner");
        const iconBox = document.getElementById("healthIconBox");
        const title = document.getElementById("healthTitle");
        const desc = document.getElementById("healthDesc");
        const countBadge = document.getElementById("healthCountBadge");
        const container = document.getElementById("problemsContainer");

        if (problems.length === 0) {
            // Normal State
            banner.className = "p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between transition-all duration-500 shadow-lg shadow-emerald-950/20";
            iconBox.className = "w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg shadow-inner";
            iconBox.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            title.className = "text-sm font-bold text-emerald-300";
            title.innerText = "Tất Cả Hệ Thống Hoạt Động Bình Thường";
            desc.innerText = "0 sự cố đang diễn ra trên máy chủ VM2 web-server. Tất cả các trigger Zabbix đều ở mức an toàn.";
            countBadge.className = "hidden sm:flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
            countBadge.innerText = "0 Active Alerts";
            container.classList.add("hidden");
            container.innerHTML = "";
        } else {
            // Problem State
            banner.className = "p-4 rounded-2xl bg-rose-950/40 border border-rose-500/50 flex items-center justify-between transition-all duration-500 shadow-xl shadow-rose-950/40 alert-pulse";
            iconBox.className = "w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center text-lg shadow-inner";
            iconBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            title.className = "text-sm font-bold text-rose-300";
            title.innerText = `CẢNH BÁO: Phát hiện ${problems.length} sự cố đang hoạt động trên Web Server!`;
            desc.innerText = "Một hoặc nhiều trigger của Zabbix Server đã bị kích hoạt. Xem danh sách sự cố bên dưới.";
            countBadge.className = "flex items-center px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40";
            countBadge.innerText = `${problems.length} Active Problem${problems.length > 1 ? 's' : ''}`;

            // Render Problem Cards
            let html = "";
            problems.forEach(p => {
                let badgeClass = "severity-warning";
                if (p.severity === "High") badgeClass = "severity-high";
                else if (p.severity === "Disaster") badgeClass = "severity-disaster";
                else if (p.severity === "Average") badgeClass = "severity-average";

                html += `
                <div class="p-3.5 rounded-xl bg-cardBg border border-slate-800 flex flex-wrap items-center justify-between gap-3 shadow-md hover:border-slate-700 transition-colors">
                    <div class="flex items-center space-x-3">
                        <span class="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${badgeClass}">
                            ${p.severity}
                        </span>
                        <div>
                            <h4 class="text-sm font-semibold text-slate-100">${escapeHtml(p.name)}</h4>
                            <p class="text-xs text-slate-400">Trigger ID: ${p.id} &bull; Xuất hiện lúc: ${p.time}</p>
                        </div>
                    </div>
                    <div class="flex items-center space-x-3 text-xs text-slate-400">
                        <span class="font-mono bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800 flex items-center gap-1.5">
                            <i class="fa-regular fa-clock text-rose-400"></i> ${p.duration}
                        </span>
                    </div>
                </div>
                `;
            });
            container.innerHTML = html;
            container.classList.remove("hidden");
        }
    } catch (err) {
        console.error("fetchProblems error:", err);
    }
}

// =============================================================================
// Chaos Engineering Panel (SSH Triggers)
// =============================================================================
async function triggerSimulation(mode) {
    if (isSimulationActive) {
        alert("Một tiến trình giả lập sự cố đang chạy. Vui lòng đợi hoàn tất!");
        return;
    }

    setButtonsState(true);

    try {
        const res = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: mode })
        });
        const json = await res.json();

        if (res.status === 409) {
            alert(json.message);
            setButtonsState(false);
            return;
        }

        if (json.status !== "started") {
            alert(`Lỗi khởi chạy: ${json.message || 'Không xác định'}`);
            setButtonsState(false);
            return;
        }

        // Poll logs immediately
        fetchLogs();
    } catch (err) {
        alert(`Lỗi kết nối API: ${err}`);
        setButtonsState(false);
    }
}

function setButtonsState(disabled) {
    isSimulationActive = disabled;
    ["btnStorm", "btnStress", "btnOutage"].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = disabled;
    });
}

// =============================================================================
// Live Terminal Logs & SSH Status
// =============================================================================
async function fetchLogs() {
    try {
        const res = await fetch("/api/logs");
        const json = await res.json();
        
        // Update Running Indicator
        const simDot = document.getElementById("simDot");
        const simStatusText = document.getElementById("simStatusText");

        if (json.is_running) {
            setButtonsState(true);
            simDot.className = "w-2 h-2 rounded-full bg-amber-400 animate-ping";
            simStatusText.className = "text-amber-400 font-semibold";
            simStatusText.innerText = `Đang chạy: ${json.current_task || 'Task'}`;
        } else {
            if (isSimulationActive) {
                // Just finished!
                setButtonsState(false);
                // Refresh problems immediately to reflect changes
                setTimeout(fetchProblems, 1000);
            }
            simDot.className = "w-2 h-2 rounded-full bg-slate-500";
            simStatusText.className = "text-slate-400";
            simStatusText.innerText = "Idle";
        }

        // Render Terminal Lines
        const term = document.getElementById("terminalBody");
        if (!term) return;

        const isScrolledToBottom = term.scrollHeight - term.clientHeight <= term.scrollTop + 50;

        const linesHtml = (json.logs || []).map(line => {
            let cls = "";
            if (line.includes("[ERROR]") || line.includes("FAILED")) cls = "terminal-line-error";
            else if (line.includes("[TASK FINISHED]") || line.includes("SUCCESS")) cls = "terminal-line-success";
            else if (line.includes("[SSH]")) cls = "terminal-line-info";
            else if (line.includes("WARNING") || line.includes("Notice")) cls = "terminal-line-warn";

            return `<div class="${cls}">${escapeHtml(line)}</div>`;
        }).join("");

        term.innerHTML = linesHtml;

        // Auto-scroll to bottom if user hasn't scrolled up
        if (isScrolledToBottom) {
            term.scrollTop = term.scrollHeight;
        }

    } catch (err) {
        console.error("fetchLogs error:", err);
    }
}

async function clearLogs() {
    try {
        await fetch("/api/logs/clear", { method: "POST" });
        fetchLogs();
    } catch (err) {
        console.error("clearLogs error:", err);
    }
}

// Utility: HTML Escaping
function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
