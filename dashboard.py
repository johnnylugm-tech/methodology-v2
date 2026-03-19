#!/usr/bin/env python3
"""
Dashboard - Unified Interface for Agent Monitor

封裝 v2/v3 Dashboard 功能
"""

from flask import Flask, render_template_string, jsonify, request
from datetime import datetime
import os

DEFAULT_PORT = 8080


class Dashboard:
    """統一 Dashboard 介面"""
    
    def __init__(self, mode="full"):
        """
        初始化 Dashboard
        
        Args:
            mode: "light" (v2) 或 "full" (v3)
        """
        self.mode = mode
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """設定路由"""
        
        @self.app.route('/')
        def index():
            if self.mode == "light":
                return self._light_html()
            else:
                return self._full_html()
        
        @self.app.route('/api/agents')
        def agents():
            return jsonify(self._get_agents())
        
        @self.app.route('/api/metrics')
        def metrics():
            return jsonify(self._get_metrics())
        
        @self.app.route('/api/alerts')
        def alerts():
            return jsonify(self._get_alerts())
        
        @self.app.route('/health')
        def health():
            return jsonify({'status': 'healthy', 'mode': self.mode})
    
    def _get_agents(self):
        """獲取 Agent 列表"""
        return [
            {"id": "agent-001", "name": "Code Generator", "status": "running", "health": 92},
            {"id": "agent-002", "name": "Reviewer", "status": "running", "health": 88},
            {"id": "agent-003", "name": "Tester", "status": "idle", "health": 95},
        ]
    
    def _get_metrics(self):
        """獲取指標"""
        return {
            "requests": 850,
            "success_rate": 96.2,
            "latency": 0.8,
            "cost_daily": 8.50
        }
    
    def _get_alerts(self):
        """獲取警報"""
        return [
            {"level": "warning", "title": "High Latency", "message": "P95 > 3s", "time": "15 min ago"}
        ]
    
    def _light_html(self):
        """輕量版 HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Agent Monitor v2</title>
    <style>
        body { font-family: system-ui; background: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }
        h1 { color: #58a6ff; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
        .stat { background: #161b22; padding: 20px; border-radius: 8px; }
        .stat .label { color: #8b949e; font-size: 12px; }
        .stat .value { font-size: 28px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🚀 Agent Monitor v2 (Light)</h1>
    <div class="stats">
        <div class="stat"><div class="label">REQUESTS</div><div class="value">{{ m.requests }}</div></div>
        <div class="stat"><div class="label">SUCCESS RATE</div><div class="value">{{ m.success_rate }}%</div></div>
        <div class="stat"><div class="label">LATENCY</div><div class="value">{{ m.latency }}s</div></div>
        <div class="stat"><div class="label">DAILY COST</div><div class="value">${{ m.cost_daily }}</div></div>
    </div>
</body>
</html>
""".replace("{{ m.requests }}", str(self._get_metrics()["requests"])).replace("{{ m.success_rate }}", str(self._get_metrics()["success_rate"])).replace("{{ m.latency }}", str(self._get_metrics()["latency"])).replace("{{ m.cost_daily }}", str(self._get_metrics()["cost_daily"]))
    
    def _full_html(self):
        """完整版 HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Agent Monitor v3</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f0f23; color: #fff; }
        .header { background: #1a1a3e; padding: 20px 30px; }
        .header h1 { font-size: 24px; }
        .header h1 span { color: #00d4ff; }
        .container { padding: 20px 30px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
        .stat { background: linear-gradient(135deg, #1a1a3e, #16213e); padding: 20px; border-radius: 16px; }
        .stat .label { color: #888; font-size: 13px; }
        .stat .value { font-size: 36px; font-weight: bold; background: linear-gradient(90deg, #fff, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .card { background: #1a1a3e; padding: 20px; border-radius: 16px; }
        .card h2 { color: #888; font-size: 16px; margin-bottom: 15px; }
        .chart { height: 280px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Agent <span>Monitor</span> v3 (Full)</h1>
    </div>
    <div class="container">
        <div class="stats">
            <div class="stat"><div class="label">Total Requests</div><div class="value">1,250</div></div>
            <div class="stat"><div class="label">Success Rate</div><div class="value">94.5%</div></div>
            <div class="stat"><div class="label">Avg Latency</div><div class="value">1.2s</div></div>
            <div class="stat"><div class="label">Daily Cost</div><div class="value">$12.50</div></div>
        </div>
        <div class="grid">
            <div class="card">
                <h2>📈 Cost Trend</h2>
                <div id="chart" class="chart"></div>
            </div>
            <div class="card">
                <h2>⚠️ Alerts</h2>
                <div style="color: #888;">No active alerts</div>
            </div>
        </div>
    </div>
    <script>
        var chart = echarts.init(document.getElementById('chart'));
        chart.setOption({
            xAxis: { type: 'category', data: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], axisLine: {lineStyle:{color:'#333'}}, axisLabel:{color:'#888'} },
            yAxis: { type: 'value', axisLine: {lineStyle:{color:'#333'}}, axisLabel:{color:'#888',formatter:'$'+'{value}'}, splitLine:{lineStyle:{color:'#222'}} },
            series: [{ data: [10,12,8,15,11,12,5], type:'line', smooth:true, lineStyle:{color:'#00d4ff'}, itemStyle:{color:'#00d4ff'}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(0,212,255,0.3)'},{offset:1,color:'rgba(0,212,255,0)'}]}} }],
            tooltip: { trigger:'axis', backgroundColor:'#1a1a3e', borderColor:'#333', textStyle:{color:'#fff'} }
        });
        window.addEventListener('resize', function() { chart.resize(); });
    </script>
</body>
</html>
"""
    
    def run(self, host='0.0.0.0', port=None):
        """啟動 Dashboard"""
        if port is None:
            port = DEFAULT_PORT
        
        print(f"\n🚀 Agent Monitor Dashboard ({self.mode})")
        print(f"   URL: http://localhost:{port}\n")
        
        self.app.run(host=host, port=port, debug=False)


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    import sys
    
    mode = "full"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    dashboard = Dashboard(mode=mode)
    dashboard.run()
