import csv
import requests
from io import StringIO
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

class TennisAnalyzer:
    def __init__(self):
        self.match_data = []
        self.analysis_results = {}
        
    def fetch_tennis_data(self, url):
        """Fetch tennis match data from the provided URL"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def analyze_match(self, data):
        """Analyze tennis match data and return statistics"""
        if not data:
            return None
            
        f = StringIO(data)
        reader = csv.DictReader(f)
        
        # Initialize counters
        stats = {
            'aces': {'server1': 0, 'server2': 0},
            'winners': {'server1': 0, 'server2': 0},
            'errors': {'server1': 0, 'server2': 0},
            'total_points': {'server1': 0, 'server2': 0},
            'total_games': 0,
            'rally_lengths': [],
            'matches_analyzed': 0
        }
        
        for row in reader:
            if not row.get('pbp'):
                continue
                
            stats['matches_analyzed'] += 1
            pbp_sequence = row.get('pbp', '')
            winner = row.get('winner', '')
            
            # Split by games (semicolon separated)
            games = pbp_sequence.split(';')
            stats['total_games'] += len(games)
            
            # Analyze each game
            for game in games:
                if not game:
                    continue
                    
                # Each character represents a shot/outcome
                rally_length = 0
                server_position = 1  # Start with server1
                
                for i, shot in enumerate(game):
                    if shot in 'SR':  # S=serve, R=return
                        rally_length += 1
                    elif shot == 'A':  # Ace
                        if server_position == 1:
                            stats['aces']['server1'] += 1
                        else:
                            stats['aces']['server2'] += 1
                        rally_length = 1
                    elif shot == 'D':  # Double fault (error by server)
                        if server_position == 1:
                            stats['errors']['server1'] += 1
                        else:
                            stats['errors']['server2'] += 1
                        rally_length = 1
                    elif shot in '.':  # End of point
                        if rally_length > 0:
                            stats['rally_lengths'].append(rally_length)
                        rally_length = 0
                        # Switch server for next point
                        server_position = 2 if server_position == 1 else 1
                
                # Handle end of game
                if rally_length > 0:
                    stats['rally_lengths'].append(rally_length)
            
            # Count match winners (simplified approach)
            if winner == '1':
                stats['total_points']['server1'] += 20  # Approximate points per match
            elif winner == '2':
                stats['total_points']['server2'] += 20
            
            # Limit analysis to first few matches for performance
            if stats['matches_analyzed'] >= 10:
                break
        
        # Calculate summary statistics
        total_aces = stats['aces']['server1'] + stats['aces']['server2']
        total_errors = stats['errors']['server1'] + stats['errors']['server2']
        
        stats['summary'] = {
            'total_aces': total_aces,
            'total_winners': 0,  # Not easily extractable from this format
            'total_errors': total_errors,
            'avg_rally_length': sum(stats['rally_lengths']) / len(stats['rally_lengths']) if stats['rally_lengths'] else 0,
            'matches_analyzed': stats['matches_analyzed'],
            'total_games': stats['total_games']
        }
        
        return stats

class TennisWebHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.analyzer = TennisAnalyzer()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.serve_html()
        elif self.path == '/analyze':
            self.serve_analysis()
        else:
            self.send_error(404)
    
    def serve_html(self):
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tennis Match Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }

        .analyze-section {
            text-align: center;
        }

        .analyze-button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }

        .analyze-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        }

        .analyze-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .results {
            display: none;
            margin-top: 30px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #667eea;
        }

        .stat-card h3 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }

        .player-comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }

        .player-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .player1 { border-left: 4px solid #4CAF50; }
        .player2 { border-left: 4px solid #FF9800; }

        .loading {
            text-align: center;
            color: #667eea;
            font-size: 1.1rem;
        }

        .error {
            color: #f44336;
            text-align: center;
            padding: 20px;
            background: #ffebee;
            border-radius: 8px;
            margin-top: 20px;
        }

        @media (max-width: 768px) {
            .player-comparison {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎾 Tennis Match Analyzer</h1>
            <p>Analyze point-by-point tennis match data with detailed statistics</p>
        </div>

        <div class="card">
            <div class="analyze-section">
                <h2>Match Analysis</h2>
                <p style="margin: 20px 0; color: #666;">
                    Click the button below to analyze a tennis match from the 2019 dataset
                </p>
                <button class="analyze-button" onclick="analyzeMatch()">
                    Analyze Tennis Match
                </button>
            </div>

            <div id="results" class="results">
                <h2>Match Statistics</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Aces</h3>
                        <div class="stat-number" id="total-aces">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Matches Analyzed</h3>
                        <div class="stat-number" id="matches-analyzed">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Games</h3>
                        <div class="stat-number" id="total-games">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Avg Rally Length</h3>
                        <div class="stat-number" id="avg-rally">-</div>
                    </div>
                </div>

                <h3 style="margin-top: 30px; text-align: center;">Player Comparison</h3>
                <div class="player-comparison">
                    <div class="player-card player1">
                        <h3>Server 1</h3>
                        <p>Aces: <strong id="p1-aces">-</strong></p>
                        <p>Errors: <strong id="p1-errors">-</strong></p>
                        <p>Points Won: <strong id="p1-points">-</strong></p>
                    </div>
                    <div class="player-card player2">
                        <h3>Server 2</h3>
                        <p>Aces: <strong id="p2-aces">-</strong></p>
                        <p>Errors: <strong id="p2-errors">-</strong></p>
                        <p>Points Won: <strong id="p2-points">-</strong></p>
                    </div>
                </div>
            </div>

            <div id="loading" class="loading" style="display: none;">
                Analyzing match data...
            </div>

            <div id="error" class="error" style="display: none;"></div>
        </div>
    </div>

    <script>
        async function analyzeMatch() {
            const button = document.querySelector('.analyze-button');
            const results = document.getElementById('results');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');

            // Reset UI
            results.style.display = 'none';
            error.style.display = 'none';
            loading.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Analyzing...';

            try {
                const response = await fetch('/analyze');
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // Update UI with results
                document.getElementById('total-aces').textContent = data.summary.total_aces;
                document.getElementById('matches-analyzed').textContent = data.summary.matches_analyzed;
                document.getElementById('total-games').textContent = data.summary.total_games;
                document.getElementById('avg-rally').textContent = data.summary.avg_rally_length.toFixed(1);

                document.getElementById('p1-aces').textContent = data.aces.server1;
                document.getElementById('p1-errors').textContent = data.errors.server1;
                document.getElementById('p1-points').textContent = data.total_points.server1;

                document.getElementById('p2-aces').textContent = data.aces.server2;
                document.getElementById('p2-errors').textContent = data.errors.server2;
                document.getElementById('p2-points').textContent = data.total_points.server2;

                results.style.display = 'block';

            } catch (err) {
                error.textContent = 'Error analyzing match: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                button.disabled = false;
                button.textContent = 'Analyze Another Match';
            }
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_analysis(self):
        url = "https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/pbp_matches_atp_main_current.csv"
        
        try:
            data = self.analyzer.fetch_tennis_data(url)
            if data:
                stats = self.analyzer.analyze_match(data)
                if stats:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(stats).encode())
                else:
                    self.send_error_json("Failed to analyze match data")
            else:
                self.send_error_json("Failed to fetch match data")
        except Exception as e:
            self.send_error_json(f"Analysis error: {str(e)}")
    
    def send_error_json(self, message):
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_response = json.dumps({"error": message})
        self.wfile.write(error_response.encode())

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TennisWebHandler)
    print(f"Tennis analyzer server running on http://0.0.0.0:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()