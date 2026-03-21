"""Observability Dashboard for methodology-v2"""
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from observability import MetricsCollector, Observer, TRACE_DIR

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>methodology-v2 Observability</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #1a1a2e; color: #eee; }
        h1 { color: #00d4ff; }
        .card { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .metric { font-size: 24px; color: #00ff88; }
        .log { background: #0f0f23; padding: 10px; margin: 5px 0; font-family: monospace; }
        .error { color: #ff4757; }
        .success { color: #2ed573; }
    </style>
</head>
<body>
    <h1>🔍 methodology-v2 Observability</h1>
    
    <div class="card">
        <h2>📊 Metrics</h2>
        <div id="metrics"></div>
    </div>
    
    <div class="card">
        <h2>📝 Logs</h2>
        <div id="logs"></div>
    </div>
    
    <script>
        async function update() {
            const resp = await fetch('/api/data');
            const data = await resp.json();
            
            // Metrics
            let m = '<table>';
            for (const [k, v] of Object.entries(data.metrics.counters)) {
                m += `<tr><td>${k}</td><td class="metric">${v}</td></tr>`;
            }
            for (const [k, v] of Object.entries(data.metrics.gauges)) {
                m += `<tr><td>${k}</td><td class="metric">${v}</td></tr>`;
            }
            m += '</table>';
            document.getElementById('metrics').innerHTML = m;
            
            // Logs
            let l = '';
            for (const log of data.logs.slice(-10)) {
                const cls = log.event.includes('error') ? 'error' : 'success';
                l += `<div class="log ${cls}">[${log.timestamp}] ${log.event}: ${JSON.stringify(log.data)}</div>`;
            }
            document.getElementById('logs').innerHTML = l;
        }
        
        setInterval(update, 2000);
        update();
    </script>
</body>
</html>
"""

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = {
                "metrics": MetricsCollector.get_all(),
                "logs": Observer.get_logs()
            }
            self.wfile.write(json.dumps(data, indent=2).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
    
    def log_message(self, format, *args):
        pass

def run(port=8080):
    print(f"🚀 Dashboard: http://localhost:{port}")
    HTTPServer(('', port), Handler).serve_forever()

if __name__ == "__main__":
    run()
