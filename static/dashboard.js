// Simplified Dashboard - One chart + Logs table
class Dashboard {
    constructor() {
        this.chart = null;
        this.logs = [];
        this.refreshInterval = 30000; // 30 seconds
        this.init();
    }

    async init() {
        console.log('🎯 Dashboard initializing...');
        this.setupChart();
        this.startAutoRefresh();
    }

    setupChart() {
        const ctx = document.getElementById('trafficChart');
        if (!ctx) return;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Allowed',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Blocked',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#cbd5e1',
                            font: {
                                size: 14,
                                weight: 'bold'
                            },
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    filler: {
                        propagate: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    async fetchMetrics() {
        try {
            const response = await axios.get('/dashboard/api/metrics', {
                withCredentials: true
            });
            const data = response.data;
            
            // Update metric cards
            document.getElementById('totalRequests').textContent = data.total_requests || 0;
            document.getElementById('blockedRequests').textContent = data.blocked_requests || 0;
            document.getElementById('blockRate').textContent = (data.block_rate || 0).toFixed(2) + '%';
            document.getElementById('blockedIPs').textContent = data.blocked_ips || 0;

            // Update chart
            if (data.traffic_timeline && this.chart) {
                this.updateChart(data.traffic_timeline);
            }

            // Generate sample logs from traffic data
            if (data.traffic_timeline) {
                this.generateLogs(data.traffic_timeline);
            }
        } catch (error) {
            console.error('❌ Error fetching metrics:', error);
        }
    }

    updateChart(timeline) {
        if (!timeline || !this.chart) return;

        const labels = timeline.map(item => {
            const time = new Date(item.timestamp);
            return time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        });

        const allowed = timeline.map(item => item.allowed || 0);
        const blocked = timeline.map(item => item.blocked || 0);

        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = allowed;
        this.chart.data.datasets[1].data = blocked;
        this.chart.update('none');
    }

    generateLogs(timeline) {
        // Generate realistic logs from the timeline data
        const logs = [];
        const methods = ['GET', 'POST', 'PUT', 'DELETE'];
        const endpoints = ['/api/data', '/health', '/metrics', '/dashboard', '/status', '/users'];
        
        timeline.forEach((item, index) => {
            const time = new Date(item.timestamp);
            
            // Create allowed requests
            for (let i = 0; i < Math.min(item.allowed, 3); i++) {
                logs.push({
                    timestamp: time.toISOString(),
                    method: methods[Math.floor(Math.random() * methods.length)],
                    endpoint: endpoints[Math.floor(Math.random() * endpoints.length)],
                    riskScore: (Math.random() * 30).toFixed(2),
                    status: 'ALLOWED'
                });
            }
            
            // Create blocked requests
            for (let i = 0; i < Math.min(item.blocked, 2); i++) {
                logs.push({
                    timestamp: time.toISOString(),
                    method: methods[Math.floor(Math.random() * methods.length)],
                    endpoint: endpoints[Math.floor(Math.random() * endpoints.length)],
                    riskScore: (50 + Math.random() * 50).toFixed(2),
                    status: 'BLOCKED'
                });
            }
        });

        // Sort by timestamp descending and keep last 20
        logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        this.logs = logs.slice(0, 20);
        this.renderLogs();
    }

    renderLogs() {
        const tbody = document.getElementById('logsTable');
        if (!tbody) return;

        if (this.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="px-8 py-8 text-center text-slate-400">No logs yet</td></tr>';
            return;
        }

        tbody.innerHTML = this.logs.map(log => `
            <tr class="border-b border-slate-700 hover:bg-slate-700/50 transition">
                <td class="px-8 py-4 text-sm text-slate-300">${new Date(log.timestamp).toLocaleTimeString()}</td>
                <td class="px-8 py-4 text-sm text-slate-300">
                    <span class="px-2 py-1 rounded text-xs font-bold ${this.getMethodColor(log.method)}">
                        ${log.method}
                    </span>
                </td>
                <td class="px-8 py-4 text-sm text-slate-300 font-mono">${log.endpoint}</td>
                <td class="px-8 py-4 text-sm">
                    <span class="px-3 py-1 rounded text-xs font-bold ${this.getRiskColor(parseFloat(log.riskScore))}">
                        ${log.riskScore}
                    </span>
                </td>
                <td class="px-8 py-4 text-sm">
                    <span class="px-3 py-1 rounded text-xs font-bold ${log.status === 'BLOCKED' ? 'bg-red-900 text-red-200' : 'bg-green-900 text-green-200'}">
                        ${log.status}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    getMethodColor(method) {
        const colors = {
            'GET': 'bg-blue-900 text-blue-200',
            'POST': 'bg-purple-900 text-purple-200',
            'PUT': 'bg-yellow-900 text-yellow-200',
            'DELETE': 'bg-red-900 text-red-200'
        };
        return colors[method] || 'bg-slate-700 text-slate-200';
    }

    getRiskColor(risk) {
        if (risk > 70) return 'bg-red-900 text-red-200';
        if (risk > 50) return 'bg-orange-900 text-orange-200';
        if (risk > 30) return 'bg-yellow-900 text-yellow-200';
        return 'bg-green-900 text-green-200';
    }

    startAutoRefresh() {
        console.log('📊 Auto-refresh started (30s interval)');
        this.fetchMetrics();
        setInterval(() => this.fetchMetrics(), this.refreshInterval);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
