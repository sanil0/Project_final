// Dashboard JavaScript Client
// Handles Chart.js visualization, API calls, and real-time data updates

class DashboardClient {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.charts = {};
        this.refreshTimers = {};
        this.init();
    }

    async init() {
        console.log('Initializing Dashboard Client');
        this.setupCharts();
        this.startAutoRefresh();
    }

    setupCharts() {
        // Traffic Chart
        const trafficCtx = document.getElementById('trafficChart');
        if (trafficCtx) {
            this.charts.traffic = new Chart(trafficCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Allowed Requests',
                            data: [],
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Blocked Requests',
                            data: [],
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        title: {
                            display: true,
                            text: 'Traffic Over Time'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Requests'
                            }
                        }
                    }
                }
            });
        }

        // Block Rate Chart
        const blockRateCtx = document.getElementById('blockRateChart');
        if (blockRateCtx) {
            this.charts.blockRate = new Chart(blockRateCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Allowed', 'Blocked'],
                    datasets: [{
                        data: [0, 0],
                        backgroundColor: ['#10b981', '#ef4444'],
                        borderColor: ['#059669', '#dc2626'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: 'Block Rate Distribution'
                        }
                    }
                }
            });
        }

        // Request Rate Chart
        const requestRateCtx = document.getElementById('requestRateChart');
        if (requestRateCtx) {
            this.charts.requestRate = new Chart(requestRateCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Requests/sec',
                        data: [],
                        backgroundColor: '#3b82f6',
                        borderColor: '#1d4ed8',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Request Rate'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Risk Distribution Chart
        const riskDistCtx = document.getElementById('riskDistributionChart');
        if (riskDistCtx) {
            this.charts.riskDist = new Chart(riskDistCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Low', 'Medium', 'High', 'Critical'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#7c2d12'],
                        borderColor: ['#059669', '#d97706', '#dc2626', '#5a1d0b'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: 'Risk Score Distribution'
                        }
                    }
                }
            });
        }

        // Attack Type Chart
        const attackTypeCtx = document.getElementById('attackTypeChart');
        if (attackTypeCtx) {
            this.charts.attackType = new Chart(attackTypeCtx, {
                type: 'bar',
                data: {
                    labels: ['DDoS', 'SQL Injection', 'XSS', 'Brute Force', 'Bot'],
                    datasets: [{
                        label: 'Count',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: '#8b5cf6',
                        borderColor: '#6d28d9',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Attack Types'
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Latency Chart
        const latencyCtx = document.getElementById('latencyChart');
        if (latencyCtx) {
            this.charts.latency = new Chart(latencyCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Latency (ms)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#f59e0b'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        title: {
                            display: true,
                            text: 'Latency Trend'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Milliseconds'
                            }
                        }
                    }
                }
            });
        }

        // Allowed vs Blocked Chart
        const allowedBlockedCtx = document.getElementById('allowedBlockedChart');
        if (allowedBlockedCtx) {
            this.charts.allowedBlocked = new Chart(allowedBlockedCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Allowed',
                            data: [],
                            backgroundColor: '#10b981'
                        },
                        {
                            label: 'Blocked',
                            data: [],
                            backgroundColor: '#ef4444'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    async fetchMetrics() {
        try {
            const response = await axios.get('/dashboard/api/metrics', {
                withCredentials: true
            });
            this.updateMetrics(response.data);
        } catch (error) {
            console.error('Error fetching metrics:', error);
        }
    }

    updateMetrics(data) {
        // Update metric cards
        const totalRequestsEl = document.getElementById('totalRequests');
        if (totalRequestsEl) {
            totalRequestsEl.textContent = this.formatNumber(data.total_requests || 0);
        }

        const blockedRequestsEl = document.getElementById('blockedRequests');
        if (blockedRequestsEl) {
            blockedRequestsEl.textContent = this.formatNumber(data.blocked_requests || 0);
        }

        const blockRateEl = document.getElementById('blockRate');
        if (blockRateEl) {
            blockRateEl.textContent = (data.block_rate || 0).toFixed(2) + '%';
        }

        const latencyEl = document.getElementById('latency');
        if (latencyEl) {
            latencyEl.textContent = (data.latency || 0).toFixed(2) + 'ms';
        }

        const blockedIPsEl = document.getElementById('blockedIPs');
        if (blockedIPsEl) {
            blockedIPsEl.textContent = this.formatNumber(data.blocked_ips || 0);
        }

        // Update traffic chart
        if (this.charts.traffic && data.traffic_timeline) {
            this.updateTrafficChart(data.traffic_timeline);
        }

        // Update block rate chart
        if (this.charts.blockRate) {
            this.charts.blockRate.data.datasets[0].data = [
                data.allowed_requests || 0,
                data.blocked_requests || 0
            ];
            this.charts.blockRate.update('none');
        }
    }

    updateTrafficChart(timeline) {
        if (!timeline || timeline.length === 0) return;

        const labels = timeline.map(item => 
            new Date(item.timestamp).toLocaleTimeString()
        );
        const allowed = timeline.map(item => item.allowed || 0);
        const blocked = timeline.map(item => item.blocked || 0);

        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = allowed;
        this.charts.traffic.data.datasets[1].data = blocked;
        this.charts.traffic.update('none');
    }

    async fetchTrafficData(timeRange = '24h') {
        try {
            const response = await axios.get(`/dashboard/api/traffic?time_range=${timeRange}`, {
                withCredentials: true
            });
            this.updateTrafficCharts(response.data);
        } catch (error) {
            console.error('Error fetching traffic data:', error);
        }
    }

    updateTrafficCharts(data) {
        if (!data) return;

        // Update request rate chart
        if (this.charts.requestRate && data.request_rates) {
            const labels = data.request_rates.map((_, i) => `${i * 5}m`);
            const rates = data.request_rates.map(r => r.rate || 0);
            this.charts.requestRate.data.labels = labels;
            this.charts.requestRate.data.datasets[0].data = rates;
            this.charts.requestRate.update('none');
        }

        // Update risk distribution chart
        if (this.charts.riskDist && data.risk_distribution) {
            const dist = data.risk_distribution;
            this.charts.riskDist.data.datasets[0].data = [
                dist.low || 0,
                dist.medium || 0,
                dist.high || 0,
                dist.critical || 0
            ];
            this.charts.riskDist.update('none');
        }

        // Update latency chart
        if (this.charts.latency && data.latency_trend) {
            const labels = data.latency_trend.map((_, i) => `${i * 5}m`);
            const latencies = data.latency_trend.map(l => l.latency || 0);
            this.charts.latency.data.labels = labels;
            this.charts.latency.data.datasets[0].data = latencies;
            this.charts.latency.update('none');
        }

        // Update allowed vs blocked chart
        if (this.charts.allowedBlocked && data.timeline) {
            const labels = data.timeline.map(t => 
                new Date(t.timestamp).toLocaleTimeString()
            );
            const allowed = data.timeline.map(t => t.allowed || 0);
            const blocked = data.timeline.map(t => t.blocked || 0);
            this.charts.allowedBlocked.data.labels = labels;
            this.charts.allowedBlocked.data.datasets[0].data = allowed;
            this.charts.allowedBlocked.data.datasets[1].data = blocked;
            this.charts.allowedBlocked.update('none');
        }
    }

    async fetchSecurityData() {
        try {
            const response = await axios.get('/dashboard/api/detection-events', {
                withCredentials: true
            });
            this.updateSecurityTable(response.data);
        } catch (error) {
            console.error('Error fetching security data:', error);
        }
    }

    updateSecurityTable(data) {
        const tableBody = document.getElementById('securityEventsTable');
        if (!tableBody) return;

        tableBody.innerHTML = '';
        if (data.events && Array.isArray(data.events)) {
            data.events.slice(0, 10).forEach(event => {
                const row = document.createElement('tr');
                row.className = 'border-t border-gray-200 hover:bg-gray-50';
                row.innerHTML = `
                    <td class="px-4 py-3 text-sm text-gray-900">${event.timestamp || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-900">${event.ip || '-'}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="px-2 py-1 text-xs font-medium rounded ${this.getRiskBadgeClass(event.risk_score)}">
                            ${event.attack_type || 'Unknown'}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-900">${(event.risk_score || 0).toFixed(1)}</td>
                `;
                tableBody.appendChild(row);
            });
        }
    }

    async fetchBlockedIPs() {
        try {
            const response = await axios.get('/dashboard/api/blocked-ips', {
                withCredentials: true
            });
            this.updateBlockedIPsTable(response.data);
        } catch (error) {
            console.error('Error fetching blocked IPs:', error);
        }
    }

    updateBlockedIPsTable(data) {
        const tableBody = document.getElementById('blockedIPsTable');
        if (!tableBody) return;

        tableBody.innerHTML = '';
        if (data.blocked_ips && Array.isArray(data.blocked_ips)) {
            data.blocked_ips.slice(0, 10).forEach(ip => {
                const row = document.createElement('tr');
                row.className = 'border-t border-gray-200 hover:bg-gray-50';
                row.innerHTML = `
                    <td class="px-4 py-3 text-sm font-mono text-gray-900">${ip.address || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-900">${ip.reason || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-900">${ip.request_count || 0}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${ip.blocked_since || '-'}</td>
                `;
                tableBody.appendChild(row);
            });
        }
    }

    async fetchMaliciousIPs() {
        try {
            const response = await axios.get('/dashboard/api/detection-events', {
                withCredentials: true
            });
            this.updateMaliciousIPsTable(response.data);
        } catch (error) {
            console.error('Error fetching malicious IPs:', error);
        }
    }

    updateMaliciousIPsTable(data) {
        const tableBody = document.getElementById('maliciousIPsTable');
        if (!tableBody) return;

        tableBody.innerHTML = '';
        if (data.top_ips && Array.isArray(data.top_ips)) {
            data.top_ips.slice(0, 10).forEach(ip => {
                const row = document.createElement('tr');
                row.className = 'border-t border-gray-200 hover:bg-gray-50';
                row.innerHTML = `
                    <td class="px-4 py-3 text-sm font-mono text-gray-900">${ip.address || '-'}</td>
                    <td class="px-4 py-3 text-sm text-gray-900">${ip.attack_count || 0}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="px-2 py-1 text-xs font-medium rounded ${this.getRiskBadgeClass(ip.risk_score)}">
                            ${(ip.risk_score || 0).toFixed(1)}
                        </span>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    }

    getRiskBadgeClass(riskScore) {
        if (riskScore >= 80) return 'bg-red-100 text-red-800';
        if (riskScore >= 60) return 'bg-orange-100 text-orange-800';
        if (riskScore >= 40) return 'bg-yellow-100 text-yellow-800';
        return 'bg-green-100 text-green-800';
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    startAutoRefresh() {
        // Determine which page we're on
        const path = window.location.pathname;

        if (path === '/dashboard') {
            // Overview page
            this.refreshTimers.metrics = setInterval(() => this.fetchMetrics(), this.refreshInterval);
            this.fetchMetrics();
        } else if (path === '/dashboard/traffic') {
            // Traffic page
            this.refreshTimers.traffic = setInterval(() => this.fetchTrafficData('24h'), this.refreshInterval);
            this.fetchTrafficData('24h');
        } else if (path === '/dashboard/security') {
            // Security page - refresh every 10 seconds
            const shortInterval = 10000;
            this.refreshTimers.security = setInterval(() => {
                this.fetchSecurityData();
                this.fetchMaliciousIPs();
            }, shortInterval);
            this.fetchSecurityData();
            this.fetchMaliciousIPs();
        }
    }

    stopAutoRefresh() {
        Object.values(this.refreshTimers).forEach(timer => clearInterval(timer));
    }

    handleTimeRangeChange(range) {
        this.stopAutoRefresh();
        this.fetchTrafficData(range);
        this.startAutoRefresh();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardClient();
});

// Handle page visibility to pause/resume updates
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        window.dashboard?.stopAutoRefresh();
    } else {
        window.dashboard?.startAutoRefresh();
    }
});
