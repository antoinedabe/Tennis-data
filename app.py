import csv
import requests
from io import StringIO
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import re


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

    def get_all_dataset_urls(self):
        """Get URLs for all available tennis datasets"""
        base_url = "https://raw.githubusercontent.com/JeffSackmann/tennis_pointbypoint/master/"
        slam_base_url = "https://raw.githubusercontent.com/JeffSackmann/tennis_slam_pointbypoint/master/"

        datasets = {
            "ATP Main Draw (Current)":
            base_url + "pbp_matches_atp_main_current.csv",
            "ATP Qualifying (Current)":
            base_url + "pbp_matches_atp_qual_current.csv",
            "ATP Challenger Main":
            base_url + "pbp_matches_ch_main_current.csv",
            "ITF Futures Main": base_url + "pbp_matches_fu_main_current.csv",
            "ATP Main Draw (Archive)":
            base_url + "pbp_matches_atp_main_archive.csv",
            "ATP Qualifying (Archive)":
            base_url + "pbp_matches_atp_qual_archive.csv",
            "ATP Challenger (Archive)":
            base_url + "pbp_matches_ch_main_archive.csv",
            "ITF Futures (Archive)":
            base_url + "pbp_matches_fu_main_archive.csv"
        }

        # Add Grand Slam datasets for recent years
        grand_slam_years = ["2021"]
        grand_slams = {
            "ausopen": "Australian Open",
            "rolandgarros": "French Open",
            "wimbledon": "Wimbledon",
            "usopen": "US Open"
        }

        for year in grand_slam_years:
            for slug, label in grand_slams.items():
                dataset_name = f"{label} {year}"
                datasets[
                    dataset_name] = f"{slam_base_url}{year}-{slug}-matches.csv"

        return datasets

    def fetch_all_tennis_data(self, selected_datasets=None):
        """Fetch data from multiple tennis datasets"""
        all_datasets = self.get_all_dataset_urls()

        if selected_datasets:
            # Filter to only selected datasets
            datasets_to_fetch = {
                k: v
                for k, v in all_datasets.items() if k in selected_datasets
            }
        else:
            # Use primary datasets by default
            datasets_to_fetch = {
                "ATP Main Draw (Current)":
                all_datasets["ATP Main Draw (Current)"],
                "ATP Main Draw (Archive)":
                all_datasets["ATP Main Draw (Archive)"],
                "Australian Open 2022":
                all_datasets.get("Australian Open 2022", ""),
                "French Open 2022":
                all_datasets.get("French Open 2022", ""),
                "Wimbledon 2022":
                all_datasets.get("Wimbledon 2022", ""),
                "Us Open 2022":
                all_datasets.get("Us Open 2022", "")
            }

        combined_data = []
        successful_datasets = []

        for dataset_name, url in datasets_to_fetch.items():
            if not url:
                continue

            print(f"Fetching {dataset_name}...")
            data = self.fetch_tennis_data(url)

            if data:
                # Parse the CSV data
                try:
                    f = StringIO(data)
                    reader = csv.DictReader(f)
                    dataset_matches = []

                    for row in reader:
                        # Add dataset source to each match
                        row['dataset_source'] = dataset_name
                        dataset_matches.append(row)

                    combined_data.extend(dataset_matches)
                    successful_datasets.append(dataset_name)
                    print(
                        f"✓ Loaded {len(dataset_matches)} matches from {dataset_name}"
                    )

                except Exception as e:
                    print(f"Error parsing {dataset_name}: {str(e)}")
            else:
                print(f"✗ Failed to load {dataset_name}")

        print(
            f"\nTotal matches loaded: {len(combined_data)} from {len(successful_datasets)} datasets"
        )
        return combined_data, successful_datasets

    def get_match_list(self, data=None, combined_data=None):
        """Get list of matches with basic info for selection"""
        if combined_data is None:
            if data:
                # Legacy single dataset mode
                f = StringIO(data)
                reader = csv.DictReader(f)
                matches = []
                for i, row in enumerate(reader):
                    if i >= 50:  # Limit to first 50 matches for performance
                        pass

                    match_info = {
                        'id': i,
                        'original_index': i,
                        'date': row.get('date', 'Unknown'),
                        'tournament': row.get('tny_name',
                                              'Unknown Tournament'),
                        'player1': row.get('server1', 'Player 1'),
                        'player2': row.get('server2', 'Player 2'),
                        'winner': row.get('winner', ''),
                        'score': row.get('score', 'N/A'),
                        'duration': row.get('wh_minutes', 'N/A'),
                        'dataset_source': 'Single Dataset'
                    }
                    matches.append(match_info)
                return matches
            else:
                # Fetch from multiple sources
                combined_data, successful_datasets = self.fetch_all_tennis_data(
                )

        if not combined_data:
            return []

        matches = []
        for i, row in enumerate(combined_data):
            if i >= 200:  # Increased limit for multiple datasets
                pass

            match_info = {
                'id': i,
                'date': row.get('date', 'Unknown'),
                'tournament': row.get('tny_name', 'Unknown Tournament'),
                'player1': row.get('server1', 'Player 1'),
                'player2': row.get('server2', 'Player 2'),
                'winner': row.get('winner', ''),
                'score': row.get('score', 'N/A'),
                'duration': row.get('wh_minutes', 'N/A'),
                'dataset_source': row.get('dataset_source', 'Unknown Dataset')
            }
            matches.append(match_info)

        return matches

    def analyze_single_match(self, data=None, match_id=0, combined_data=None):
        """Analyze a specific tennis match by ID with game-by-game breakdown"""
        if combined_data is None:
            if data:
                # Legacy single dataset mode
                f = StringIO(data)
                reader = csv.DictReader(f)
                # Find the specific match
                target_match = None
                for i, row in enumerate(reader):
                    if i == match_id:
                        target_match = row
                        break
            else:
                # Fetch from multiple sources
                combined_data, successful_datasets = self.fetch_all_tennis_data(
                )
                if not combined_data or match_id >= len(combined_data):
                    return None
                target_match = combined_data[match_id]
        else:
            if match_id >= len(combined_data):
                return None
            target_match = combined_data[match_id]

        if not target_match:
            return None

        # Initialize counters for single match
        stats = {
            'aces': {
                'player1': 0,
                'player2': 0
            },
            'winners': {
                'player1': 0,
                'player2': 0
            },
            'errors': {
                'player1': 0,
                'player2': 0
            },
            'double_faults': {
                'player1': 0,
                'player2': 0
            },
            'rally_lengths': [],
            'games': [],  # Game-by-game breakdown
            'match_info': {
                'date': target_match.get('date', 'Unknown'),
                'tournament': target_match.get('tny_name',
                                               'Unknown Tournament'),
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
        # Analyze each game
        for game_idx, game in enumerate(games):
            if not game:
                continue

            game_stats = {
                'game_number': game_idx + 1,
                'server': 1 if game_idx % 2 == 0 else 2,  # Alternate server
                'game_info': [],
                'aces': {
                    'player1': 0,
                    'player2': 0
                },
                'double_faults': {
                    'player1': 0,
                    'player2': 0
                },
                'errors': {
                    'player1': 0,
                    'player2': 0
                },
                'rally_lengths': [],
                'score_progression':
                []  # Track tennis scoring throughout the game
            }

            # Parse each point in the game
            current_point = []
            rally_length = 0
            server_position = game_stats[
                'server']  # Use the actual server for this game
            point_server = server_position  # Track who's serving this specific point

            for shot in game:
                print('current point' + shot)
                if shot in 'SR':  # S=serve, R=return
                    current_point.append({
                        'shot':
                        shot,
                        'player':
                        point_server if shot == 'S' else
                        (2 if point_server == 1 else 1),
                        'description':
                        'Serve' if shot == 'S' else 'Return'
                    })
                    rally_length += 1
                    # Calculate tennis score after this point
                    current_score = self._calculate_tennis_score(
                        rally_length, point_server if shot == 'S' else
                        (2 if point_server == 1 else 1), game_stats['server'])
                    print(current_score)
                elif shot == 'A':  # Ace - server wins point
                    current_point.append({
                        'shot': shot,
                        'player': point_server,
                        'description': 'Ace',
                        'point_end': True,
                        'winner': point_server,
                        'winner_code': 'A'  # Ace from server
                    })
                    rally_length += 1
                    current_score = self._calculate_tennis_score(
                        rally_length, point_server, game_stats['server'])
                    if point_server == 1:
                        game_stats['aces']['player1'] += 1
                        stats['aces']['player1'] += 1
                    else:
                        game_stats['aces']['player2'] += 1
                        stats['aces']['player2'] += 1
                    rally_length += 1
                    current_score = self._calculate_tennis_score(
                        rally_length, point_server if shot == 'S' else
                        (2 if point_server == 1 else 1), game_stats['server'])
                elif shot == 'D':  # Double fault - returner wins point
                    current_point.append({
                        'shot': shot,
                        'player': point_server,
                        'description': 'Double Fault',
                        'point_end': True,
                        'winner': 2 if point_server == 1 else 1,
                        'winner_code':
                        'D'  # Double fault gives point to returner
                    })
                    if point_server == 1:
                        game_stats['double_faults']['player1'] += 1
                        game_stats['errors']['player1'] += 1
                        stats['double_faults']['player1'] += 1
                        stats['errors']['player1'] += 1
                    else:
                        game_stats['double_faults']['player2'] += 1
                        game_stats['errors']['player2'] += 1
                        stats['double_faults']['player2'] += 1
                        stats['errors']['player2'] += 1
                    rally_length += 1
                    current_score = self._calculate_tennis_score(
                        rally_length, 2 if point_server == 1 else 1,
                        game_stats['server'])
                elif shot in '.':  # End of point - determine winner based on last shot
                    if current_point:
                        # Determine point winner and code
                        point_winner = None
                        winner_code = 'S'  # Default to server wins

                        # Check if there was already a definitive end (ace or double fault)
                        if not any(s.get('point_end') for s in current_point):
                            # No ace or double fault, determine winner based on rally
                            last_shot_player = current_point[-1][
                                'player'] if current_point else point_server
                            # If the rally ended normally, the last player to hit wins the point
                            point_winner = last_shot_player
                            winner_code = 'S' if point_winner == point_server else 'R'
                        else:
                            # Point already has winner from ace/double fault
                            point_end_shot = next(s for s in current_point
                                                  if s.get('point_end'))
                            point_winner = point_end_shot['winner']
                            winner_code = point_end_shot['winner_code']

                        print('server')

                        print(game_stats['server'])

                        # Calculate tennis score after this point
                        current_score = self._calculate_tennis_score(
                            rally_length, point_winner, game_stats['server'])
                        print(current_score)

                        # Add winner info to the point
                        point_data = {
                            'game_number': len(game_stats['game_info']) + 1,
                            'rally_length': rally_length,
                            'shots': current_point.copy(),
                            'winner': point_winner,
                            'winner_code': winner_code,
                            'server': point_server,
                            'score_after':
                            current_score if current_score else {
                                "player1": "0",
                                "player2": "0",
                                "status": "playing"
                            }
                        }

                        game_stats['game_info'].append(point_data)
                        game_stats['score_progression'].append(current_score)
                        if rally_length > 0:
                            game_stats['rally_lengths'].append(rally_length)
                            stats['rally_lengths'].append(rally_length)

                    current_point = []
                    rally_length = 0
                    # Switch server for next point (alternate within the game)
                    point_server = 2 if point_server == 1 else 1
                else:
                    # Other shots (winners, errors, etc.)
                    current_player = point_server if len(
                        current_point) % 2 == 0 else (
                            2 if point_server == 1 else 1)
                    current_point.append({
                        'shot':
                        shot,
                        'player':
                        current_player,
                        'description':
                        self._get_shot_description(shot)
                    })
                    rally_length += 1

            # Handle end of game if there's an unfinished point
            if current_point and rally_length > 0:
                # Determine winner for unfinished point
                last_shot_player = current_point[-1][
                    'player'] if current_point else point_server
                point_winner = last_shot_player
                winner_code = 'S' if point_winner == point_server else 'R'

                point_data = {
                    'game_number': len(game_stats['game_info']) + 1,
                    'rally_length': rally_length,
                    'shots': current_point.copy(),
                    'winner': point_winner,
                    'winner_code': winner_code,
                    'server': point_server,
                }
                game_stats['score_progression'].append(current_score)

                game_stats['game_info'].append(point_data)
                game_stats['rally_lengths'].append(rally_length)
                stats['rally_lengths'].append(rally_length)
            print(rally_length)
            stats['games'].append(game_stats)

        # Calculate summary statistics
        total_aces = stats['aces']['player1'] + stats['aces']['player2']
        total_errors = stats['errors']['player1'] + stats['errors']['player2']
        total_double_faults = stats['double_faults']['player1'] + stats[
            'double_faults']['player2']

        stats['summary'] = {
            'total_aces':
            total_aces,
            'total_errors':
            total_errors,
            'total_double_faults':
            total_double_faults,
            'total_games':
            len(stats['games']),
            'avg_rally_length':
            sum(stats['rally_lengths']) /
            len(stats['rally_lengths']) if stats['rally_lengths'] else 0,
            'total_rallies':
            len(stats['rally_lengths'])
        }

        return stats

    def _get_shot_description(self, shot):
        """Get description for shot codes"""
        shot_map = {
            'A': 'Ace',
            'D': 'Double Fault',
            'S': 'Serve',
            'R': 'Return',
            'W': 'Winner',
            'E': 'Error',
            'F': 'Forehand',
            'B': 'Backhand',
            'V': 'Volley',
            'O': 'Overhead',
            'L': 'Lob'
        }
        return shot_map.get(shot, f'Shot ({shot})')

    def _calculate_tennis_score(self, points_so_far, current_point_winner,
                                game_server):
        """Calculate tennis score (15, 30, 40, Advantage, Game) after each point"""
        # Count points won by each player including the current point
        player1_points = 0
        player2_points = 0

        print('points_so_far')
        print(points_so_far)
        print('current_point_winner')
        print(current_point_winner)
        print('game_server')
        print(game_server)

        # Count all previous points
        while points_so_far > 0:
            if current_point_winner == 1:
                player1_points += 1
            elif current_point_winner == 2:
                player2_points += 1
            points_so_far -= 1

        print('player1_points')

        print(player1_points)
        print('player2_points')

        print(player2_points)

        # Convert to tennis scoring display
        def points_to_tennis_score(points):
            score_map = {0: "0", 1: "15", 2: "30", 3: "40"}
            return score_map.get(points, "40")

        # Handle special scoring situations
        if player1_points >= 3 and player2_points >= 3:
            # Deuce and advantage situations
            if player1_points == player2_points:
                return {
                    "player1": "Deuce",
                    "player2": "Deuce",
                    "status": "deuce"
                }
            elif player1_points > player2_points:
                return {
                    "player1": "Advantage",
                    "player2": "40",
                    "status": "advantage_p1"
                }
            else:
                return {
                    "player1": "40",
                    "player2": "Advantage",
                    "status": "advantage_p2"
                }

        # Check for game completion
        if player1_points >= 4 and player1_points - player2_points >= 2:
            return {
                "player1": "Game",
                "player2": points_to_tennis_score(player2_points),
                "status": "game_p1"
            }
        elif player2_points >= 4 and player2_points - player1_points >= 2:
            return {
                "player1": points_to_tennis_score(player1_points),
                "player2": "Game",
                "status": "game_p2"
            }

        # Regular scoring (before deuce)
        return {
            "player1": points_to_tennis_score(player1_points),
            "player2": points_to_tennis_score(player2_points),
            "status": "playing"
        }


class TennisWebHandler(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.analyzer = TennisAnalyzer()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            self.serve_html()

        elif path == '/matches':
            self.serve_match_list()

        elif path.startswith('/analyze/') and '/' in path[9:]:
            # Format: /analyze/{match_id}/{game_id}
            parts = path.strip('/').split('/')
            if len(parts) == 3:
                try:
                    match_id = int(parts[1])
                    game_id = int(parts[2])
                    self.serve_game_analysis(match_id, game_id)
                except (ValueError, IndexError):
                    self.send_error(400)
            else:
                self.send_error(400)

        elif path.startswith('/analyze/'):
            parts = path.strip('/').split('/')
            if len(parts) == 2:
                try:
                    match_id = int(parts[1])
                    self.serve_single_match_analysis(match_id)
                except ValueError:
                    self.send_error(400)
            else:
                self.send_error(400)

        else:
            self.send_error(404)

    def serve_single_match_analysis(self, match_id):
        try:
            data = self.analyzer.analyze_single_match(match_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_error_json(f"Error analyzing match: {str(e)}")

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

        .games-section {
            margin-top: 30px;
        }

        .games-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }

        .game-item {
            background: #f8f9fa;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .game-item:hover {
            background: #e9ecef;
            border-color: #667eea;
            transform: translateY(-2px);
        }

        .game-number {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }

        .game-server {
            font-size: 0.9rem;
            color: #666;
        }

        .game-details {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        .points-section {
            margin-top: 20px;
        }

        .points-container {
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-top: 15px;
        }

        .point-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            background: white;
        }

        .point-item:last-child {
            border-bottom: none;
        }

        .point-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .point-number {
            font-weight: bold;
            color: #667eea;
        }

        .rally-length {
            color: #666;
            font-size: 0.9rem;
        }

        .shots-sequence {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .shot-item {
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #333;
        }

        .shot-item.player1 {
            background: #d4edda;
            border-left: 3px solid #4CAF50;
        }

        .shot-item.player2 {
            background: #f8d7da;
            border-left: 3px solid #FF9800;
        }

        .shot-item.point-end {
            background: #fff3cd;
            border-left: 3px solid #FFC107;
            font-weight: bold;
        }

        .tennis-score {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 8px 12px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .tennis-score.deuce {
            background: #fff3cd;
            border-color: #ffc107;
        }

        .tennis-score.advantage {
            background: #d1ecf1;
            border-color: #bee5eb;
        }

        .tennis-score.game-won {
            background: #d4edda;
            border-color: #c3e6cb;
        }

        .score-evolution {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }

        .score-evolution h4 {
            margin-top: 0;
            margin-bottom: 15px;
            color: #495057;
        }

        .matches-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .filter-section {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .filter-section label {
            font-weight: bold;
            color: #667eea;
        }

        #year-filter {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            background: white;
            font-size: 0.9rem;
            cursor: pointer;
        }

        #year-filter:focus {
            outline: none;
            border-color: #667eea;
        }

        .match-count {
            color: #666;
            font-size: 0.9rem;
            font-style: italic;
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

            .games-container {
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            }

            .shots-sequence {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎾 Tennis Match Analyzer test</h1>
            <p>Analyze point-by-point tennis match data with detailed statistics</p>
        </div>

        <div class="card">
            <div class="matches-section">
                <h2>Available Tennis Matches test</h2>
                <p style="margin: 20px 0; color: #666;">
                    Select a match from the list below to view detailed analysis
                </p>
                <button class="analyze-button" onclick="loadMatches()" id="load-matches-btn">
                    Load Tennis Matches
                </button>
                
                <div id="matches-list" class="matches-list" style="display: none;">
                    <div class="matches-header">
                        <h3>Select a Match to Analyze:</h3>
                        <div class="filter-section">
                            <label for="year-filter">Filter by Year:</label>
                            <select id="year-filter" onchange="filterMatchesByYear()">
                                <option value="all">All Years</option>
                            </select>
                            <span id="match-count" class="match-count"></span>
                        </div>
                    </div>
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

                <div id="games-section" class="games-section" style="display: none;">
                    <h3 style="margin-top: 30px; text-align: center;">Games in This Match</h3>
                    <p style="text-align: center; color: #666; margin-bottom: 20px;">
                        Click on any game to see point-by-point analysis
                    </p>
                    <div id="games-container" class="games-container">
                        <!-- Games will be displayed here -->
                    </div>
                </div>
            </div>

            <div id="game-results" class="results">
                <h2 id="game-title">Game Analysis</h2>
                <div id="game-details" class="game-details">
                    <!-- Game details will be displayed here -->
                </div>
                
                <div id="points-section" class="points-section">
                    <h3>Point-by-Point Breakdown</h3>
                    <div id="points-container" class="points-container">
                        <!-- Points will be displayed here -->
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
        let allYears = [];

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

                matchesData = data.matches || data;
                setupYearFilter(data.matches || data);
                displayMatches(data.matches || data);
                
                // Show dataset information if available
                if (data.datasets_loaded) {
                    const matchCountElement = document.getElementById('match-count');
                    if (matchCountElement) {
                        matchCountElement.innerHTML += ` (from ${data.datasets_loaded.length} sources)`;
                    }
                }
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

        function setupYearFilter(matches) {
            // Extract unique years from matches
            const years = new Set();
            matches.forEach(match => {
                // Extract year from date format "YYYY-MM-DD" or "DD MMM YY"
                let year;
                if (match.date.includes('-')) {
                    // Format: YYYY-MM-DD
                    year = match.date.split('-')[0];
                } else {
                    // Format: DD MMM YY
                    const dateParts = match.date.split(' ');
                    if (dateParts.length >= 3) {
                        year = dateParts[2];
                        // Convert 2-digit year to 4-digit (assuming 2000s)
                        if (year.length === 2) {
                            year = '20' + year;
                        }
                    }
                }
                if (year) {
                    years.add(year);
                }
            });

            allYears = Array.from(years).sort().reverse(); // Most recent years first
            
            const yearFilter = document.getElementById('year-filter');
            // Clear existing options except "All Years"
            yearFilter.innerHTML = '<option value="all">All Years</option>';
            
            // Add year options
            allYears.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearFilter.appendChild(option);
            });

            updateMatchCount(matches.length);
        }

async function filterMatchesByYear() {
    const selectedYear = document.getElementById('year-filter').value;
    const url = selectedYear === 'all'
        ? '/matches'
        : `/matches?year=${encodeURIComponent(selectedYear)}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        matchesData = data.matches || [];
        displayMatches(matchesData);
        updateMatchCount(matchesData.length);
    } catch (err) {
        console.error(err);  // 🔍 pour voir l'erreur exacte dans la console
        const container = document.getElementById('matches-container');
        container.innerHTML = `<p>Error loading filtered matches: ${err.message}</p>`;
    }
}
        

        function updateMatchCount(count) {
            const matchCount = document.getElementById('match-count');
            matchCount.textContent = `(${count} matches)`;
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

        let currentMatchData = null;

        async function analyzeMatch(matchId) {
            const results = document.getElementById('results');
            const gameResults = document.getElementById('game-results');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');

            // Reset UI
            results.style.display = 'none';
            gameResults.style.display = 'none';
            error.style.display = 'none';
            loading.style.display = 'block';

            try {
                const response = await fetch(`/analyze/${matchId}`);
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                currentMatchData = data;
                currentMatchData.matchId = matchId;

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

                // Display games
                displayGames(data.games);
                document.getElementById('games-section').style.display = 'block';

                results.style.display = 'block';

            } catch (err) {
                error.textContent = 'Error analyzing match: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        }

        function displayGames(games) {
            const container = document.getElementById('games-container');
            container.innerHTML = '';

            games.forEach((game, index) => {
                const gameDiv = document.createElement('div');
                gameDiv.className = 'game-item';
                gameDiv.onclick = () => analyzeGame(currentMatchData.matchId, index);

                const serverName = game.server === 1 ? currentMatchData.match_info.player1 : currentMatchData.match_info.player2;

                gameDiv.innerHTML = `
                    <div class="game-number">Game ${game.game_number}</div>
                    <div class="game-server">Server: ${serverName}</div>
                    <div class="game-server">${game.game_info.length} points</div>
                `;

                container.appendChild(gameDiv);
            });
        }

        async function analyzeGame(matchId, gameId) {
            const gameResults = document.getElementById('game-results');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');

            // Reset UI
            gameResults.style.display = 'none';
            error.style.display = 'none';
            loading.style.display = 'block';

            try {
                const response = await fetch(`/analyze/${matchId}/${gameId}`);
                const data = await response.json();
                console.log(data);
                if (data.error) {
                    throw new Error(data.error);
                }

                // Update game details
                const matchInfo = data.match_info;
                const serverName = data.server === 1 ? matchInfo.player1 : matchInfo.player2;
                const winnerName = data.game_info.winner === 1 ? matchInfo.player1 : matchInfo.player2;

                document.getElementById('game-title').textContent = 
                    `Game ${data.game_number} - ${matchInfo.player1} vs ${matchInfo.player2}`;
                
                const gameDetails = document.getElementById('game-details');
                gameDetails.innerHTML = `
                    <h4>Game ${data.game_number} Details</h4>
                    <p><strong>Server:</strong> ${serverName}</p>
                    <p><strong>Winner:</strong> ${winnerName}</p>
                    <p><strong>Points in this Game:</strong> ${data.game_info.length}</p>
                    <p><strong>Aces in this Game:</strong> ${data.aces.player1 + data.aces.player2}</p>
                    <p><strong>Double Faults in this Game:</strong> ${data.double_faults.player1 + data.double_faults.player2}</p>
                    <p><strong>Average Rally Length:</strong> ${data.rally_lengths.length > 0 ? (data.rally_lengths.reduce((a, b) => a + b, 0) / data.rally_lengths.length).toFixed(1) : 0}</p>
                `;
                gameDetails.style.display = 'block';

                // Display points with score evolution
                displayPointsWithScores(data.game_info, data.score_progression, matchInfo);

                gameResults.style.display = 'block';

            } catch (err) {
                error.textContent = 'Error analyzing game: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        }

        function displayPointsWithScores(game_info, scoreProgression, matchInfo) {
            const container = document.getElementById('points-container');
            container.innerHTML = '';

            // Add score evolution header
            const evolutionDiv = document.createElement('div');
            evolutionDiv.className = 'score-evolution';
            evolutionDiv.innerHTML = `
                <h4>Game Score Evolution (Traditional Tennis Scoring)</h4>
                <p><strong>${matchInfo.player1}</strong> vs <strong>${matchInfo.player2}</strong></p>
            `;
            container.appendChild(evolutionDiv);

            game_info.forEach((point, index) => {
                const pointDiv = document.createElement('div');
                pointDiv.className = 'point-item';

                // Determine winner description
                const winnerName = point.winner === 1 ? matchInfo.player1 : matchInfo.player2;
                const serverName = point.server === 1 ? matchInfo.player1 : matchInfo.player2;
                
                let winnerDescription = '';
                switch(point.winner_code) {
                    case 'A':
                        winnerDescription = `A: Ace from ${serverName}`;
                        break;
                    case 'D':
                        winnerDescription = `D: Double fault from ${serverName}, point to ${winnerName}`;
                        break;
                    case 'S':
                        winnerDescription = `Result: Game ${serverName} wins`;
                        break;
                    case 'R':
                        winnerDescription = `Result: Game  for returner ${winnerName}`;
                        break;
                    default:
                        winnerDescription = `Winner: ${winnerName}`;
                }

                // Get tennis score after this point
                const score = point.score_after || {player1: "0", player2: "0", status: "playing"};
                let scoreClass = 'tennis-score';
                if (score.status === 'deuce') scoreClass += ' deuce';
                else if (score.status && score.status.includes('advantage')) scoreClass += ' advantage';
                else if (score.status && score.status.includes('game')) scoreClass += ' game-won';

                pointDiv.innerHTML = `
                    <div class="point-header">
                        <span class="point-number">Game ${point.game_number}</span>
                        <span class="rally-length">Rally Length: ${point.rally_length} shots</span>
                    </div>
                    <div class="point-winner" style="margin-bottom: 10px; font-weight: bold; color: #667eea;">
                        ${winnerDescription}
                    </div>
                    <div class="${scoreClass}">
                        <span>${matchInfo.player1}: ${score.player1}</span>
                        <span>${matchInfo.player2}: ${score.player2}</span>
                    </div>
                    <div class="shots-sequence">
                        ${point.shots.map(shot => {
                            const playerName = shot.player === 1 ? matchInfo.player1 : matchInfo.player2;
                            const classes = ['shot-item', `player${shot.player}`];
                            if (shot.point_end) classes.push('point-end');
                            
                            return `<span class="${classes.join(' ')}" title="${playerName}">
                                ${shot.description}
                            </span>`;
                        }).join('')}
                    </div>
                `;

                container.appendChild(pointDiv);
            });
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
        import re

        def extract_year(date_str):
            if not date_str:
                return None
            # Format: YYYY-MM-DD
            if re.match(r'^\d{4}-', date_str):
                return date_str[:4]
            # Format: DD MMM YY
            elif re.match(r'^\d{2} \w{3} \d{2}$', date_str):
                yy = date_str[-2:]
                return '20' + yy if int(yy) < 50 else '19' + yy
            return None

        try:
            # Extraire les paramètres de l'URL
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            year_filter = params.get('year', [None])[0]

            # Récupération des données
            combined_data, successful_datasets = self.analyzer.fetch_all_tennis_data(
            )

            # Générer la liste des matchs pour le frontend
            matches = self.analyzer.get_match_list(combined_data=combined_data)

            if year_filter:
                matches = [
                    m for m in matches
                    if extract_year(m.get('date')) == year_filter
                ]
                # Réaffecte des ID continus mais garde original_index pour analyse
                for new_id, match in enumerate(matches):
                    match['id'] = new_id

            # Répondre en JSON
            response_data = {
                'matches': matches,
                'datasets_loaded': successful_datasets,
                'total_matches': len(matches)
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            self.send_error_json(f"Error getting matches: {str(e)}")

    def serve_game_analysis(self, match_id, game_id):
        try:
            # Fetch from all available datasets
            combined_data, successful_datasets = self.analyzer.fetch_all_tennis_data(
            )

            if combined_data:
                stats = self.analyzer.analyze_single_match(
                    combined_data=combined_data, match_id=match_id)
                if stats and len(stats['games']) > game_id:
                    game_data = stats['games'][game_id]
                    game_data['match_info'] = stats['match_info']
                    game_data['datasets_loaded'] = successful_datasets
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(game_data).encode())
                else:
                    self.send_error_json("Game not found")
            else:
                self.send_error_json(
                    "Failed to fetch match data from any source")
        except Exception as e:
            self.send_error_json(f"Game analysis error: {str(e)}")

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
