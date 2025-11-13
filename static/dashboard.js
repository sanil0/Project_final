// Dashboard JavaScript Client - Simplified Version
// Only includes 4 functional charts that can be populated with real data

class DashboardClient {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.charts = {};
        this.refreshTimers = {};
        this.init();
    }

    async init() {
        console.log('🎯 Initializing Dashboard Client');
        this.setupCharts();
        this.startAutoRefresh();
    }

    setupCharts() {
        // 1. Traffic Chart - Line chart showing allowed vs blocked over time
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
                            fill: true,
                            borderWidth: 2
                        },
                        {
                            label: 'Blocked Requests',
                            data: [],
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4,
                            fill: true,
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
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

        // 2. Request Distribution - Doughnut showing allowed vs blocked ratio
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
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // 3. Risk Level Distribution - Pie chart showing risk levels
        const riskDistCtx = document.getElementById('riskDistChart');
        if (riskDistCtx) {
            this.charts.riskDist = new Chart(riskDistCtx, {
                type: 'pie',
                data: {
                    labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                        borderColor: ['#059669', '#d97706', '#dc2626'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // 4. Latency Trend - Line chart showing latency over time
        const latencyCtx = document.getElementById('latencyTrendChart');
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
                        pointBackgroundColor: '#f59e0b',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
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
    }

    async fetchMetrics() {
        try {
            const response = await axios.get('/dashboard/api/metrics', {
                withCredentials: true
            });
            this.updateMetrics(response.data);
        } catch (error) {
            console.error('❌ Error fetching metrics:', error);
        }
    }

    updateMetrics(data) {
        if (!data) return;

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

        const blockedIPsEl = document.getElementById('blockedIPs');
        if (blockedIPsEl) {
            blockedIPsEl.textContent = this.formatNumber(data.blocked_ips || 0);
        }

        // Update traffic chart with timeline data
        if (this.charts.traffic && data.traffic_timeline) {
            this.updateTrafficChart(data.traffic_timeline);
        }

        // Update request distribution chart (doughnut)
        if (this.charts.blockRate && data.traffic_timeline) {
            const totalAllowed = data.traffic_timeline.reduce((sum, item) => sum + (item.allowed || 0), 0);
            const totalBlocked = data.traffic_timeline.reduce((sum, item) => sum + (item.blocked || 0), 0);
            this.charts.blockRate.data.datasets[0].data = [totalAllowed, totalBlocked];
            this.charts.blockRate.update('none');
        }

        // Update risk distribution chart
        if (this.charts.riskDist && data.risk_distribution) {
            const dist = data.risk_distribution;
            this.charts.riskDist.data.datasets[0].data = [
                dist.low || 0,
                dist.medium || 0,
                dist.high || 0
            ];
            this.charts.riskDist.update('none');
        }

        // Update latency trend chart
        if (this.charts.latency && data.latency_trend) {
            this.updateLatencyChart(data.latency_trend);
        }
    }

    updateTrafficChart(timeline) {
        if (!timeline || timeline.length === 0) return;

        const labels = timeline.map(item => {
            const time = new Date(item.timestamp);
            return time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        });
        const allowed = timeline.map(item => item.allowed || 0);
        const blocked = timeline.map(item => item.blocked || 0);

        this.charts.traffic.data.labels = labels;
        this.charts.traffic.data.datasets[0].data = allowed;
        this.charts.traffic.data.datasets[1].data = blocked;
        this.charts.traffic.update('none');
    }

    updateLatencyChart(latencyTrend) {
        if (!latencyTrend || latencyTrend.length === 0) return;

        const labels = latencyTrend.map((_, i) => `${i * 5}min`);
        const latencies = latencyTrend.map(l => l.latency || 0);

        this.charts.latency.data.labels = labels;
        this.charts.latency.data.datasets[0].data = latencies;
        this.charts.latency.update('none');
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
        console.log('📊 Starting auto-refresh (every 30 seconds)');
        this.fetchMetrics();
        this.refreshTimers.metrics = setInterval(() => this.fetchMetrics(), this.refreshInterval);
    }

    stopAutoRefresh() {
        Object.values(this.refreshTimers).forEach(timer => clearInterval(timer));
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
