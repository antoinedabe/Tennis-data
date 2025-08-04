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
    
    def get_match_list(self, data):
        """Get list of matches with basic info for selection"""
        if not data:
            return []
            
        f = StringIO(data)
        reader = csv.DictReader(f)
        
        matches = []
        for i, row in enumerate(reader):
            if i >= 50:  # Limit to first 50 matches for performance
                break
                
            match_info = {
                'id': i,
                'date': row.get('date', 'Unknown'),
                'tournament': row.get('tny_name', 'Unknown Tournament'),
                'player1': row.get('server1', 'Player 1'),
                'player2': row.get('server2', 'Player 2'),
                'winner': row.get('winner', ''),
                'score': row.get('score', 'N/A'),
                'duration': row.get('wh_minutes', 'N/A')
            }
            matches.append(match_info)
        
        return matches
    
    def analyze_single_match(self, data, match_id):
        """Analyze a specific tennis match by ID"""
        if not data:
            return None
            
        f = StringIO(data)
        reader = csv.DictReader(f)
        
        # Find the specific match
        target_match = None
        for i, row in enumerate(reader):
            if i == match_id:
                target_match = row
                break
        
        if not target_match:
            return None
        
        # Initialize counters for single match
        stats = {
            'aces': {'player1': 0, 'player2': 0},
            'winners': {'player1': 0, 'player2': 0},
            'errors': {'player1': 0, 'player2': 0},
            'double_faults': {'player1': 0, 'player2': 0},
            'rally_lengths': [],
            'match_info': {
                'date': target_match.get('date', 'Unknown'),
                'tournament': target_match.get('tny_name', 'Unknown Tournament'),
                'player1': target_match.get('server1', 'Player 1'),
                'player2': target_match.get('server2', 'Player 2'),
                'winner': target_match.get('winner', ''),
                'score': target_match.get('score', 'N/A'),
                'duration': target_match.get('wh_minutes', 'N/A')
            }
        }
        
        pbp_sequence = target_match.get('pbp', '')
        if not pbp_sequence:
            return stats
        
        # Split by games (semicolon separated)
        games = pbp_sequence.split(';')
        total_games = len([g for g in games if g])
        
        # Analyze each game
        for game in games:
            if not game:
                continue
                
            # Each character represents a shot/outcome
            rally_length = 0
            server_position = 1  # Start with player1 serving
            
            for shot in game:
                if shot in 'SR':  # S=serve, R=return
                    rally_length += 1
                elif shot == 'A':  # Ace
                    if server_position == 1:
                        stats['aces']['player1'] += 1
                    else:
                        stats['aces']['player2'] += 1
                    rally_length = 1
                elif shot == 'D':  # Double fault
                    if server_position == 1:
                        stats['double_faults']['player1'] += 1
                        stats['errors']['player1'] += 1
                    else:
                        stats['double_faults']['player2'] += 1
                        stats['errors']['player2'] += 1
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
        
        # Calculate summary statistics
        total_aces = stats['aces']['player1'] + stats['aces']['player2']
        total_errors = stats['errors']['player1'] + stats['errors']['player2']
        total_double_faults = stats['double_faults']['player1'] + stats['double_faults']['player2']
        
        stats['summary'] = {
            'total_aces': total_aces,
            'total_errors': total_errors,
            'total_double_faults': total_double_faults,
            'total_games': total_games,
            'avg_rally_length': sum(stats['rally_lengths']) / len(stats['rally_lengths']) if stats['rally_lengths'] else 0,
            'total_rallies': len(stats['rally_lengths'])
        }
        
        return stats

class TennisWebHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.analyzer = TennisAnalyzer()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.serve_html()
        elif self.path == '/matches':
            self.serve_match_list()
        elif self.path.startswith('/analyze/'):
            match_id = self.path.split('/')[-1]
            try:
                self.serve_single_match_analysis(int(match_id))
            except ValueError:
                self.send_error(400)
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

        .matches-list {
            margin-top: 30px;
        }

        .matches-container {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-top: 15px;
        }

        .match-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }

        .match-item:hover {
            background-color: #f8f9fa;
        }

        .match-item:last-child {
            border-bottom: none;
        }

        .match-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }

        .match-players {
            font-weight: bold;
            color: #333;
        }

        .match-date {
            color: #666;
            font-size: 0.9rem;
        }

        .match-details-info {
            color: #555;
            font-size: 0.9rem;
        }

        .match-details {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        .match-details h4 {
            margin: 0 0 10px 0;
            color: #333;
        }

        .match-details p {
            margin: 5px 0;
            color: #666;
        }

        .winner-indicator {
            color: #4CAF50;
            font-weight: bold;
        }

        @media (max-width: 768px) {
            .player-comparison {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }

            .match-header {
                flex-direction: column;
                align-items: flex-start;
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
            <div class="matches-section">
                <h2>Available Tennis Matches</h2>
                <p style="margin: 20px 0; color: #666;">
                    Select a match from the list below to view detailed analysis
                </p>
                <button class="analyze-button" onclick="loadMatches()" id="load-matches-btn">
                    Load Tennis Matches
                </button>
                
                <div id="matches-list" class="matches-list" style="display: none;">
                    <h3>Select a Match to Analyze:</h3>
                    <div id="matches-container" class="matches-container">
                        <!-- Matches will be loaded here -->
                    </div>
                </div>
            </div>

            <div id="results" class="results">
                <h2 id="match-title">Match Analysis</h2>
                <div id="match-details" class="match-details">
                    <!-- Match details will be displayed here -->
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Aces</h3>
                        <div class="stat-number" id="total-aces">-</div>
                    </div>
                    <div class="stat-card">
                        <h3>Double Faults</h3>
                        <div class="stat-number" id="double-faults">-</div>
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

                <h3 style="margin-top: 30px; text-align: center;">Player Statistics</h3>
                <div class="player-comparison">
                    <div class="player-card player1">
                        <h3 id="player1-name">Player 1</h3>
                        <p>Aces: <strong id="p1-aces">-</strong></p>
                        <p>Double Faults: <strong id="p1-double-faults">-</strong></p>
                        <p>Errors: <strong id="p1-errors">-</strong></p>
                    </div>
                    <div class="player-card player2">
                        <h3 id="player2-name">Player 2</h3>
                        <p>Aces: <strong id="p2-aces">-</strong></p>
                        <p>Double Faults: <strong id="p2-double-faults">-</strong></p>
                        <p>Errors: <strong id="p2-errors">-</strong></p>
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
        let matchesData = [];

        async function loadMatches() {
            const button = document.getElementById('load-matches-btn');
            const matchesList = document.getElementById('matches-list');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');

            // Reset UI
            error.style.display = 'none';
            loading.style.display = 'block';
            button.disabled = true;
            button.textContent = 'Loading Matches...';

            try {
                const response = await fetch('/matches');
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                matchesData = data;
                displayMatches(data);
                matchesList.style.display = 'block';

            } catch (err) {
                error.textContent = 'Error loading matches: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                button.disabled = false;
                button.textContent = 'Refresh Matches';
            }
        }

        function displayMatches(matches) {
            const container = document.getElementById('matches-container');
            container.innerHTML = '';

            matches.forEach(match => {
                const matchDiv = document.createElement('div');
                matchDiv.className = 'match-item';
                matchDiv.onclick = () => analyzeMatch(match.id);

                const winner = match.winner === '1' ? match.player1 : 
                              match.winner === '2' ? match.player2 : 'Unknown';

                matchDiv.innerHTML = `
                    <div class="match-header">
                        <div class="match-players">${match.player1} vs ${match.player2}</div>
                        <div class="match-date">${match.date}</div>
                    </div>
                    <div class="match-details-info">
                        ${match.tournament} | Score: ${match.score} | Winner: <span class="winner-indicator">${winner}</span>
                        ${match.duration !== 'N/A' ? ` | Duration: ${match.duration} min` : ''}
                    </div>
                `;

                container.appendChild(matchDiv);
            });
        }

        async function analyzeMatch(matchId) {
            const results = document.getElementById('results');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');

            // Reset UI
            results.style.display = 'none';
            error.style.display = 'none';
            loading.style.display = 'block';

            try {
                const response = await fetch(`/analyze/${matchId}`);
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // Update match details
                const matchInfo = data.match_info;
                const winner = matchInfo.winner === '1' ? matchInfo.player1 : 
                              matchInfo.winner === '2' ? matchInfo.player2 : 'Draw';

                document.getElementById('match-title').textContent = 
                    `${matchInfo.player1} vs ${matchInfo.player2}`;
                
                const matchDetails = document.getElementById('match-details');
                matchDetails.innerHTML = `
                    <h4>${matchInfo.tournament}</h4>
                    <p><strong>Date:</strong> ${matchInfo.date}</p>
                    <p><strong>Score:</strong> ${matchInfo.score}</p>
                    <p><strong>Winner:</strong> <span class="winner-indicator">${winner}</span></p>
                    ${matchInfo.duration !== 'N/A' ? `<p><strong>Duration:</strong> ${matchInfo.duration} minutes</p>` : ''}
                `;
                matchDetails.style.display = 'block';

                // Update statistics
                document.getElementById('total-aces').textContent = data.summary.total_aces;
                document.getElementById('double-faults').textContent = data.summary.total_double_faults;
                document.getElementById('total-games').textContent = data.summary.total_games;
                document.getElementById('avg-rally').textContent = data.summary.avg_rally_length.toFixed(1);

                // Update player names and stats
                document.getElementById('player1-name').textContent = matchInfo.player1;
                document.getElementById('player2-name').textContent = matchInfo.player2;
                
                document.getElementById('p1-aces').textContent = data.aces.player1;
                document.getElementById('p1-double-faults').textContent = data.double_faults.player1;
                document.getElementById('p1-errors').textContent = data.errors.player1;

                document.getElementById('p2-aces').textContent = data.aces.player2;
                document.getElementById('p2-double-faults').textContent = data.double_faults.player2;
                document.getElementById('p2-errors').textContent = data.errors.player2;

                results.style.display = 'block';

            } catch (err) {
                error.textContent = 'Error analyzing match: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
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
    
    def serve_match_list(self):
        url = "https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/pbp_matches_atp_main_current.csv"
        
        try:
            data = self.analyzer.fetch_tennis_data(url)
            if data:
                matches = self.analyzer.get_match_list(data)
                if matches:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(matches).encode())
                else:
                    self.send_error_json("No matches found")
            else:
                self.send_error_json("Failed to fetch match data")
        except Exception as e:
            self.send_error_json(f"Error getting matches: {str(e)}")
    
    def serve_single_match_analysis(self, match_id):
        url = "https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/pbp_matches_atp_main_current.csv"
        
        try:
            data = self.analyzer.fetch_tennis_data(url)
            if data:
                stats = self.analyzer.analyze_single_match(data, match_id)
                if stats:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(stats).encode())
                else:
                    self.send_error_json("Failed to analyze match or match not found")
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