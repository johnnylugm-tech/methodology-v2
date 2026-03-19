#!/usr/bin/env python3
"""
Unified Dashboard - Model Router + Agent Monitor

整合式監控儀表板
"""

from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timedelta
import os

app = Flask(__name__)

DEFAULT_PORT = 8080

# ============================================================================
# Mock Data - Model Router
# ============================================================================

def get_model_router_stats():
    """Model Router 指標"""
    return {
        "total_requests": 8500,
        "active_models": 5,
        "cost_daily": 45.50,
        "cost_monthly": 1350.00,
        "cache_hit_rate": 0.68,
        "avg_latency": 1.2,
        "models": [
            {"name": "GPT-4", "requests": 2500, "cost": 25.00},
            {"name": "Claude-3", "requests": 3000, "cost": 12.00},
            {"name": "Gemini", "requests": 2000, "cost": 5.50},
            {"name": "MiniMax", "requests": 1000, "cost": 3.00},
        ]
    }

def get_model_cost_trend():
    """Model Router 成本趨勢"""
    days = 14
    return {
        "dates": [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(days-1, -1, -1)],
        "costs": [40 + i * 2 + (i % 3) * 5 for i in range(days)]
    }

# ============================================================================
# Mock Data - Agent Monitor
# ============================================================================

def get_agent_monitor_stats():
    """Agent Monitor 指標"""
    return {
        "total_agents": 8,
        "running": 5,
        "idle": 2,
        "failed": 1,
        "health_avg": 82,
        "tasks_completed": 156,
        "cost_daily": 12.50
    }

def get_agents():
    """Agent 列表"""
    return [
        {"id": "agent-001", "name": "Code Generator", "status": "running", "health": 92},
        {"id": "agent-002", "name": "Code Reviewer", "status": "running", "health": 88},
        {"id": "agent-003", "name": "Tester", "status": "running", "health": 95},
        {"id": "agent-004", "name": "Deployer", "status": "failed", "health": 45},
        {"id": "agent-005", "name": "Researcher", "status": "idle", "health": 85},
        {"id": "agent-006", "name": "Writer", "status": "idle", "health": 90},
    ]

def get_alerts():
    """警報列表"""
    return [
        {"level": "critical", "title": "Deployer Failed", "message": "Agent Deployer health < 50", "time": "10 min ago"},
        {"level": "warning", "title": "High Cost", "message": "Daily cost > $40", "time": "30 min ago"},
        {"level": "info", "title": "Cache Hit Rate", "message": "Cache hit rate dropped to 68%", "time": "1 hour ago"},
    ]

# ============================================================================
# HTML Template
# ============================================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Dashboard - Model Router + Agent Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f23; color: #fff; }
        
        .header { background: #1a1a3e; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; }
        .header h1 { font-size: 24px; font-weight: 600; }
        .header h1 span { color: #00d4ff; }
        .header .time { color: #888; font-size: 14px; }
        
        .container { padding: 20px 30px; }
        
        .section-title { font-size: 18px; color: #888; margin: 20px 0 15px 0; padding-left: 10px; border-left: 3px solid #00d4ff; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: linear-gradient(135deg, #1a1a3e 0%, #16213e 100%); padding: 20px; border-radius: 16px; border: 1px solid #2a2a5e; }
        .stat-card .label { color: #888; font-size: 13px; text-transform: uppercase; }
        .stat-card .value { font-size: 32px; font-weight: bold; margin: 10px 0; background: linear-gradient(90deg, #fff, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .stat-card .trend { font-size: 13px; }
        .trend.up { color: #00ff88; }
        .trend.down { color: #ff4757; }
        
        .dual-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        
        .card { background: #1a1a3e; border-radius: 16px; padding: 20px; border: 1px solid #2a2a5e; }
        .card h2 { font-size: 16px; color: #888; margin-bottom: 20px; }
        
        .chart-container { height: 280px; width: 100%; }
        
        .agents-list { display: flex; flex-direction: column; gap: 10px; }
        .agent-item { background: #16213e; padding: 12px 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; }
        .status-dot.running { background: #00ff88; }
        .status-dot.idle { background: #ffc107; }
        .status-dot.failed { background: #ff4757; }
        
        .alert-list { display: flex; flex-direction: column; gap: 10px; }
        .alert-item { padding: 12px; border-radius: 10px; border-left: 4px solid; }
        .alert-item.critical { border-color: #ff4757; background: rgba(255,71,87,0.1); }
        .alert-item.warning { border-color: #ffc107; background: rgba(255,193,7,0.1); }
        .alert-item.info { border-color: #00d4ff; background: rgba(0,212,255,0.1); }
        
        .model-list { display: flex; flex-direction: column; gap: 8px; }
        .model-item { background: #16213e; padding: 10px 15px; border-radius: 8px; display: flex; justify-content: space-between; }
        
        .tab-bar { display: flex; gap: 10px; margin-bottom: 15px; }
        .tab { padding: 8px 16px; background: #16213e; border: none; border-radius: 8px; color: #888; cursor: pointer; }
        .tab.active { background: #00d4ff; color: #0f0f23; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Unified <span>Dashboard</span></h1>
        <span class="time">{{ time }}</span>
    </div>
    
    <div class="container">
        <!-- Model Router Stats -->
        <div class="section-title">📡 Model Router</div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Requests</div>
                <div class="value">{{ mr.total_requests }}</div>
                <div class="trend up">↑ 15%</div>
            </div>
            <div class="stat-card">
                <div class="label">Active Models</div>
                <div class="value">{{ mr.active_models }}</div>
                <div class="trend">4 providers</div>
            </div>
            <div class="stat-card">
                <div class="label">Daily Cost</div>
                <div class="value">${{ mr.cost_daily }}</div>
                <div class="trend up">↑ $5</div>
            </div>
            <div class="stat-card">
                <div class="label">Cache Hit Rate</div>
                <div class="value">{{ (mr.cache_hit_rate * 100) | int }}%</div>
                <div class="trend down">↓ 5%</div>
            </div>
        </div>
        
        <div class="dual-grid">
            <div class="card">
                <h2>📈 Cost Trend</h2>
                <div id="costChart" class="chart-container"></div>
            </div>
            <div class="card">
                <h2>🤖 Model Usage</h2>
                <div class="model-list">
                    {% for model in mr.models %}
                    <div class="model-item">
                        <span>{{ model.name }}</span>
                        <span style="color: #888;">{{ model.requests }} reqs / ${{ model.cost }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- Agent Monitor Stats -->
        <div class="section-title">🤖 Agent Monitor</div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Agents</div>
                <div class="value">{{ am.total_agents }}</div>
                <div class="trend">5 running</div>
            </div>
            <div class="stat-card">
                <div class="label">Health Score</div>
                <div class="value">{{ am.health_avg }}</div>
                <div class="trend up">↑ 3</div>
            </div>
            <div class="stat-card">
                <div class="label">Tasks Completed</div>
                <div class="value">{{ am.tasks_completed }}</div>
                <div class="trend up">↑ 12</div>
            </div>
            <div class="stat-card">
                <div class="label">Daily Cost</div>
                <div class="value">${{ am.cost_daily }}</div>
                <div class="trend">Stable</div>
            </div>
        </div>
        
        <div class="dual-grid">
            <div class="card">
                <h2>👥 Agent Status</h2>
                <div class="agents-list">
                    {% for agent in agents %}
                    <div class="agent-item">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="status-dot {{ agent.status }}"></div>
                            <span>{{ agent.name }}</span>
                        </div>
                        <span style="color: {% if agent.health >= 80 %}#00ff88{% elif agent.health >= 50 %}#ffc107{% else %}#ff4757{% endif %};">{{ agent.health }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
            <div class="card">
                <h2>⚠️ Alerts</h2>
                <div class="alert-list">
                    {% for alert in alerts %}
                    <div class="alert-item {{ alert.level }}">
                        <div style="font-weight: 600;">{{ alert.title }}</div>
                        <div style="font-size: 12px; opacity: 0.8;">{{ alert.message }}</div>
                        <div style="font-size: 11px; opacity: 0.5; margin-top: 5px;">{{ alert.time }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        var costChart = echarts.init(document.getElementById('costChart'));
        
        var option = {
            backgroundColor: 'transparent',
            grid: { top: 20, right: 20, bottom: 30, left: 50 },
            xAxis: {
                type: 'category',
                data: {{ cost_trend.dates | safe }},
                axisLine: { lineStyle: { color: '#333' } },
                axisLabel: { color: '#888' }
            },
            yAxis: {
                type: 'value',
                axisLine: { lineStyle: { color: '#333' } },
                axisLabel: { color: '#888', formatter: '$' + '{value}' },
                splitLine: { lineStyle: { color: '#222' } }
            },
            series: [{
                data: {{ cost_trend.costs | safe }},
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: { color: '#00d4ff', width: 3 },
                itemStyle: { color: '#00d4ff' },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(0,212,255,0.3)' },
                            { offset: 1, color: 'rgba(0,212,255,0)' }
                        ]
                    }
                }
            }],
            tooltip: { trigger: 'axis', backgroundColor: '#1a1a3e', borderColor: '#333', textStyle: { color: '#fff' } }
        };
        
        costChart.setOption(option);
        window.addEventListener('resize', function() { costChart.resize(); });
    </script>
</body>
</html>
"""

# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML,
        time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        mr=get_model_router_stats(),
        am=get_agent_monitor_stats(),
        agents=get_agents(),
        alerts=get_alerts(),
        cost_trend=get_model_cost_trend()
    )

@app.route('/api/model-router')
def api_model_router():
    return jsonify(get_model_router_stats())

@app.route('/api/agent-monitor')
def api_agent_monitor():
    return jsonify({
        "stats": get_agent_monitor_stats(),
        "agents": get_agents(),
        "alerts": get_alerts()
    })

@app.route('/api/cost-trend')
def api_cost_trend():
    return jsonify(get_model_cost_trend())

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', DEFAULT_PORT))
    print(f"\n🚀 Unified Dashboard")
    print(f"   URL: http://localhost:{port}")
    print(f"   Model Router: http://localhost:{port}/api/model-router")
    print(f"   Agent Monitor: http://localhost:{port}/api/agent-monitor\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
