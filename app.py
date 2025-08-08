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
                        f"â Loaded {len(dataset_matches)} matches from {dataset_name}"
                    )

                except Exception as e:
                    print(f"Error parsing {dataset_name}: {str(e)}")
            else:
                print(f"â Failed to load {dataset_name}")

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
            current_score = {'player1': "0", 'player2': "0", 'status': 'playing'}
            player1_points = 0
            player2_points = 0
            rally_length = 0
            server_position = game_stats['server']
            point_server = server_position

            for shot in game:
                if shot in 'SR':  # S=serve, R=return
                    current_point.append({
                        'shot': shot,
                        'player': point_server if shot == 'S' else (2 if point_server == 1 else 1),
                        'description': 'Serve' if shot == 'S' else 'Return'
                    })
                    rally_length += 1
                elif shot == 'A':  # Ace - server wins point
                    current_point.append({
                        'shot': shot,
                        'player': point_server,
                        'description': 'Ace',
                        'point_end': True,
                        'winner': point_server,
                        'winner_code': 'A'
                    })
                    rally_length += 1
                    if point_server == 1:
                        player1_points += 1
                        game_stats['aces']['player1'] += 1
                        stats['aces']['player1'] += 1
                    else:
                        player2_points += 1
                        game_stats['aces']['player2'] += 1
                        stats['aces']['player2'] += 1

                    current_score = self._calculate_tennis_score(
                        rally_length, point_server, current_score, player1_points, player2_points)
                elif shot == 'D':  # Double fault - returner wins point
                    current_point.append({
                        'shot': shot,
                        'player': point_server,
                        'description': 'Double Fault',
                        'point_end': True,
                        'winner': 2 if point_server == 1 else 1,
                        'winner_code': 'D'
                    })
                    if point_server == 1:
                        player2_points += 1  # Returner gets the point
                        game_stats['double_faults']['player1'] += 1
                        game_stats['errors']['player1'] += 1
                        stats['double_faults']['player1'] += 1
                        stats['errors']['player1'] += 1
                    else:
                        player1_points += 1  # Returner gets the point
                        game_stats['double_faults']['player2'] += 1
                        game_stats['errors']['player2'] += 1
                        stats['double_faults']['player2'] += 1
                        stats['errors']['player2'] += 1

                    rally_length += 1
                    current_score = self._calculate_tennis_score(
                        rally_length, 2 if point_server == 1 else 1, current_score, player1_points, player2_points)
                elif shot in '.':  # End of point - determine winner based on last shot
                    if current_point:
                        # Determine point winner and code
                        point_winner = None
                        winner_code = 'S'

                        # Check if there was already a definitive end (ace or double fault)
                        point_end_shots = [s for s in current_point if s.get('point_end')]
                        if point_end_shots:
                            # Point already has winner from ace/double fault
                            point_end_shot = point_end_shots[0]
                            point_winner = point_end_shot['winner']
                            winner_code = point_end_shot['winner_code']
                        else:
                            # No ace or double fault, determine winner based on rally
                            last_shot_player = current_point[-1]['player'] if current_point else point_server
                            point_winner = last_shot_player
                            winner_code = 'S' if point_winner == point_server else 'R'

                            # Update points for regular rally end
                            if point_winner == 1:
                                player1_points += 1
                            else:
                                player2_points += 1

                            # Calculate tennis score after this point
                            current_score = self._calculate_tennis_score(
                                rally_length, point_winner, current_score, player1_points, player2_points)

                        # Add winner info to the point
                        point_data = {
                            'point_number': len(game_stats['game_info']) + 1,
                            'rally_length': rally_length,
                            'shots': current_point.copy(),
                            'winner': point_winner,
                            'winner_code': winner_code,
                            'server': point_server,
                            'score_after': current_score.copy()
                        }

                        game_stats['game_info'].append(point_data)
                        game_stats['score_progression'].append(current_score.copy())
                        if rally_length > 0:
                            game_stats['rally_lengths'].append(rally_length)
                            stats['rally_lengths'].append(rally_length)

                    current_point = []
                    rally_length = 0
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
                last_shot_player = current_point[-1]['player'] if current_point else point_server
                point_winner = last_shot_player
                winner_code = 'S' if point_winner == point_server else 'R'

                # Update points for unfinished point
                if point_winner == 1:
                    player1_points += 1
                else:
                    player2_points += 1

                current_score = self._calculate_tennis_score(
                    rally_length, point_winner, current_score, player1_points, player2_points)

                point_data = {
                    'point_number': len(game_stats['game_info']) + 1,
                    'rally_length': rally_length,
                    'shots': current_point.copy(),
                    'winner': point_winner,
                    'winner_code': winner_code,
                    'server': point_server,
                    'score_after': current_score.copy()
                }

                game_stats['game_info'].append(point_data)
                game_stats['score_progression'].append(current_score.copy())
                game_stats['rally_lengths'].append(rally_length)
                stats['rally_lengths'].append(rally_length)

            # Determine game winner
            if current_score.get('status', '').startswith('game_'):
                game_stats['winner'] = 1 if current_score['status'] == 'game_p1' else 2
            else:
                # If no clear winner, determine based on points
                game_stats['winner'] = 1 if player1_points > player2_points else 2

            game_stats['final_score'] = current_score.copy()
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
            len(stats['rally_lengths']),
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
                                current_score, player1_points, player2_points):
        """Calculate tennis score (15, 30, 40, Advantage, Game) after each point"""

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




# ===============================
# Clean statistics engine (integrated)
# ===============================
class CleanStatsEngine:
    def analyze(self, combined_data, match_id: int = 0):
        if not combined_data or match_id >= len(combined_data):
            return None
        target = combined_data[match_id]
        pbp = (target.get('pbp') or "").strip()

        stats = {
            'aces': {'player1':0,'player2':0},
            'double_faults': {'player1':0,'player2':0},
            'errors': {'player1':0,'player2':0},
            'rally_lengths': [],
            'games': [],
            'points_won': {'player1':0,'player2':0},
            'service_points_won': {'player1':0,'player2':0},
            'return_points_won': {'player1':0,'player2':0},
            'breaks': {
                'player1_made':0,'player2_made':0,
                'player1_bp_faced':0,'player2_bp_faced':0,
                'player1_bp_saved':0,'player2_bp_saved':0,
                'player1_bp_converted':0,'player2_bp_converted':0
            },
            'match_info': {
                'date': target.get('date','Unknown'),
                'tournament': target.get('tny_name','Unknown Tournament'),
                'player1': target.get('server1','Player 1'),
                'player2': target.get('server2','Player 2'),
                'winner': target.get('winner',''),
                'score': target.get('score','N/A'),
                'duration': target.get('wh_minutes','N/A'),
            }
        }

        if not pbp:
            stats['summary'] = {
                'total_aces':0,'total_errors':0,'total_double_faults':0,'total_games':0,
                'avg_rally_length':0,'total_rallies':0,
                'p1_points_won':0,'p2_points_won':0,
                'p1_breaks_made':0,'p2_breaks_made':0,
                'p1_bp_faced':0,'p2_bp_faced':0,'p1_bp_saved':0,'p2_bp_saved':0,
                'p1_bp_converted':0,'p2_bp_converted':0,
                'key_moment_game':None,'key_moment_point':None,'key_moment_desc':""
            }
            return stats

        def tscore(p1,p2):
            if p1>=3 and p2>=3:
                if p1==p2: return "Deuce"
                if p1==p2+1: return "Adv P1"
                if p2==p1+1: return "Adv P2"
            mp={0:"0",1:"15",2:"30",3:"40"}
            return f"{mp.get(p1,'40')}-{mp.get(p2,'40')}"

        def game_win(p1,p2):
            if (p1>=4 or p2>=4) and abs(p1-p2)>=2:
                return 1 if p1>p2 else 2
            return None

        games = [g for g in pbp.split(';') if g]
        total_points_seen=0
        total_points_overall = sum(len(g) for g in games) or 1

        key_moment={'leverage':-1.0}

        for gi,g in enumerate(games):
            server = 1 if gi%2==0 else 2
            p1=p2=0
            game_obj={
                'game_number':gi+1,'server':server,'game_info':[],'rally_lengths':[],
                'aces':{'player1':0,'player2':0},
                'double_faults':{'player1':0,'player2':0},
                'errors':{'player1':0,'player2':0},
                'score_progression':[]
            }
            current_point=[]; rally_len=0

            def hitter(idx):
                if server==1:
                    return 1 if idx%2==0 else 2
                else:
                    return 2 if idx%2==0 else 1

            for ch in g:
                if ch in "SRFBLVNE":
                    current_point.append(ch); rally_len+=1; continue
                if ch in "ADWE":
                    before = tscore(p1,p2)

                    if ch=='A':
                        win=server
                        if server==1:
                            stats['aces']['player1']+=1; game_obj['aces']['player1']+=1
                        else:
                            stats['aces']['player2']+=1; game_obj['aces']['player2']+=1
                    elif ch=='D':
                        win=2 if server==1 else 1
                        if server==1:
                            stats['double_faults']['player1']+=1; stats['errors']['player1']+=1
                            game_obj['double_faults']['player1']+=1; game_obj['errors']['player1']+=1
                        else:
                            stats['double_faults']['player2']+=1; stats['errors']['player2']+=1
                            game_obj['double_faults']['player2']+=1; game_obj['errors']['player2']+=1
                    elif ch=='W':
                        hit_idx=max(0,len(current_point)-1); w=hitter(hit_idx); win=w
                    elif ch=='E':
                        hit_idx=max(0,len(current_point)-1); h=hitter(hit_idx); win=2 if h==1 else 1
                        if h==1:
                            stats['errors']['player1']+=1; game_obj['errors']['player1']+=1
                        else:
                            stats['errors']['player2']+=1; game_obj['errors']['player2']+=1

                    sp = p1 if server==1 else p2
                    rp = p2 if server==1 else p1
                    is_bp = (rp>=3 and (rp-sp)>=1)
                    if is_bp:
                        if server==1: stats['breaks']['player1_bp_faced']+=1
                        else: stats['breaks']['player2_bp_faced']+=1

                    if win==1: stats['points_won']['player1']+=1
                    else: stats['points_won']['player2']+=1

                    if win==server:
                        if server==1: stats['service_points_won']['player1']+=1
                        else: stats['service_points_won']['player2']+=1
                    else:
                        if server==1: stats['return_points_won']['player2']+=1
                        else: stats['return_points_won']['player1']+=1

                    if win==1: p1+=1
                    else: p2+=1

                    after = tscore(p1,p2)
                    if rally_len>0:
                        stats['rally_lengths'].append(rally_len); game_obj['rally_lengths'].append(rally_len)

                    if is_bp:
                        if win==server:
                            if server==1: stats['breaks']['player1_bp_saved']+=1
                            else: stats['breaks']['player2_bp_saved']+=1
                        else:
                            if win==1: stats['breaks']['player1_bp_converted']+=1
                            else: stats['breaks']['player2_bp_converted']+=1

                    total_points_seen+=1
                    deuce = (p1>=3 and p2>=3 and abs(p1-p2)<=1)
                    game_point = (p1>=3 and (p1-p2)>=1) or (p2>=3 and (p2-p1)>=1)
                    time_w = total_points_seen/float(max(total_points_overall,1))
                    lev = (1.0 if game_point else 0.0) + (0.8 if is_bp else 0.0) + (0.3 if deuce else 0.0)
                    lev *= (0.6 + 0.4*time_w)
                    if lev > key_moment.get('leverage',-1):
                        key_moment={
                            'game_index':gi,'point_number':len(game_obj['game_info'])+1,'server':server,'winner':win,
                            'is_break_point':bool(is_bp),'was_game_point':bool(game_point),'deuce_phase':bool(deuce),'leverage':lev
                        }

                    game_obj['game_info'].append({
                        'point_number':len(game_obj['game_info'])+1,'rally_length':rally_len,'winner':win,'server':server,
                        'score_before':before,'score_after':after,'event':ch
                    })
                    game_obj['score_progression'].append({
                        'player1': after.split('-')[0] if '-' in after else after,
                        'player2': after.split('-')[1] if '-' in after else ''
                    })
                    current_point=[]; rally_len=0
                else:
                    continue

            gw = game_win(p1,p2)
            if gw is None: gw = 1 if p1>p2 else 2
            game_obj['winner']=gw
            stats['games'].append(game_obj)
            if gw!=server:
                if gw==1: stats['breaks']['player1_made']+=1
                else: stats['breaks']['player2_made']+=1

        tot_aces = stats['aces']['player1']+stats['aces']['player2']
        tot_err = stats['errors']['player1']+stats['errors']['player2']
        tot_df = stats['double_faults']['player1']+stats['double_faults']['player2']

        if 'game_index' in key_moment:
            nserv = stats['match_info']['player1'] if key_moment['server']==1 else stats['match_info']['player2']
            nwin = stats['match_info']['player1'] if key_moment['winner']==1 else stats['match_info']['player2']
            tags=[]
            if key_moment.get('is_break_point'): tags.append('break point')
            if key_moment.get('was_game_point'): tags.append('game point')
            if key_moment.get('deuce_phase'): tags.append('deuce')
            desc=f"Point {key_moment['point_number']} du jeu {key_moment['game_index']+1}: {nwin} gagne ({', '.join(tags) if tags else 'point important'}), serveur: {nserv}."
        else:
            desc=""
        stats['key_moment']={**key_moment,'description':desc}

        stats['summary']={
            'total_aces': tot_aces,
            'total_errors': tot_err,
            'total_double_faults': tot_df,
            'total_games': len(stats['games']),
            'avg_rally_length': (sum(stats['rally_lengths'])/len(stats['rally_lengths'])) if stats['rally_lengths'] else 0,
            'total_rallies': len(stats['rally_lengths']),
            'p1_points_won': stats['points_won']['player1'],
            'p2_points_won': stats['points_won']['player2'],
            'p1_breaks_made': stats['breaks']['player1_made'],
            'p2_breaks_made': stats['breaks']['player2_made'],
            'p1_bp_faced': stats['breaks']['player1_bp_faced'],
            'p2_bp_faced': stats['breaks']['player2_bp_faced'],
            'p1_bp_saved': stats['breaks']['player1_bp_saved'],
            'p2_bp_saved': stats['breaks']['player2_bp_saved'],
            'p1_bp_converted': stats['breaks']['player1_bp_converted'],
            'p2_bp_converted': stats['breaks']['player2_bp_converted'],
            'key_moment_game': (stats['key_moment']['game_index']+1) if 'game_index' in stats['key_moment'] else None,
            'key_moment_point': stats['key_moment'].get('point_number'),
            'key_moment_desc': desc
        }
        return stats
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

        elif path.startswith('/download_stats'):
            self.serve_download_stats(urllib.parse.urlparse(self.path))

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
            combined_data, successful_datasets = self.analyzer.fetch_all_tennis_data()
            data = CleanStatsEngine().analyze(combined_data, match_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_error_json(f"Error analyzing match: {str(e)}")


def serve_download_stats(self, parsed_path):
    try:
        qs = urllib.parse.parse_qs(parsed_path.query or '')
        match_id = int(qs.get('match_id', ['0'])[0])
        combined_data, _ = self.analyzer.fetch_all_tennis_data()
        data = CleanStatsEngine().analyze(combined_data, match_id)
        if not data:
            self.send_error_json("Match not found")
            return

        mi = data.get('match_info', {})
        summ = data.get('summary', {})

        header = [
            'tournament','date','player1','player2','winner','score','duration',
            'total_aces','total_errors','total_double_faults','total_games','avg_rally_length',
            'p1_points_won','p2_points_won',
            'p1_breaks_made','p2_breaks_made','p1_bp_faced','p2_bp_faced','p1_bp_saved','p2_bp_saved','p1_bp_converted','p2_bp_converted',
            'key_moment_game','key_moment_point','key_moment_desc'
        ]

        def g(d,k,default=''): return d.get(k, default) if isinstance(d, dict) else default

        row = [
            g(mi,'tournament'), g(mi,'date'), g(mi,'player1'), g(mi,'player2'), g(mi,'winner'), g(mi,'score'), g(mi,'duration','N/A'),
            g(summ,'total_aces',0), g(summ,'total_errors',0), g(summ,'total_double_faults',0), g(summ,'total_games',0), g(summ,'avg_rally_length',0),
            g(summ,'p1_points_won',0), g(summ,'p2_points_won',0),
            g(summ,'p1_breaks_made',0), g(summ,'p2_breaks_made',0), g(summ,'p1_bp_faced',0), g(summ,'p2_bp_faced',0), g(summ,'p1_bp_saved',0), g(summ,'p2_bp_saved',0), g(summ,'p1_bp_converted',0), g(summ,'p2_bp_converted',0),
            g(summ,'key_moment_game',''), g(summ,'key_moment_point',''), g(summ,'key_moment_desc','')
        ]

        import io, csv as _csv
        buf = io.StringIO(); w = _csv.writer(buf)
        w.writerow(header); w.writerow(row)
        data_bytes = buf.getvalue().encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type','text/csv; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename=match_{match_id}_stats.csv')
        self.send_header('Content-Length', str(len(data_bytes)))
        self.end_headers()
        self.wfile.write(data_bytes)
    except Exception as e:
        self.send_error_json(f"Error exporting stats: {str(e)}")

    def serve_download_stats(self, parsed_path):
        try:
            qs = urllib.parse.parse_qs(parsed_path.query or '')
            match_id = int(qs.get('match_id', ['0'])[0])
            combined_data, _ = self.analyzer.fetch_all_tennis_data()
            data = CleanStatsEngine().analyze(combined_data, match_id)
            if not data:
                self.send_error_json("Match not found")
                return
            mi = data.get('match_info', {})
            summ = data.get('summary', {})
            header = [
                'tournament','date','player1','player2','winner','score','duration',
                'total_aces','total_errors','total_double_faults','total_games','avg_rally_length',
                'p1_points_won','p2_points_won',
                'p1_breaks_made','p2_breaks_made','p1_bp_faced','p2_bp_faced','p1_bp_saved','p2_bp_saved','p1_bp_converted','p2_bp_converted',
                'key_moment_game','key_moment_point','key_moment_desc'
            ]
            def g(d,k,default=''): return d.get(k, default) if isinstance(d, dict) else default
            row = [
                g(mi,'tournament'), g(mi,'date'), g(mi,'player1'), g(mi,'player2'), g(mi,'winner'), g(mi,'score'), g(mi,'duration','N/A'),
                g(summ,'total_aces',0), g(summ,'total_errors',0), g(summ,'total_double_faults',0), g(summ,'total_games',0), g(summ,'avg_rally_length',0),
                g(summ,'p1_points_won',0), g(summ,'p2_points_won',0),
                g(summ,'p1_breaks_made',0), g(summ,'p2_breaks_made',0), g(summ,'p1_bp_faced',0), g(summ,'p2_bp_faced',0), g(summ,'p1_bp_saved',0), g(summ,'p2_bp_saved',0), g(summ,'p1_bp_converted',0), g(summ,'p2_bp_converted',0),
                g(summ,'key_moment_game',''), g(summ,'key_moment_point',''), g(summ,'key_moment_desc','')
            ]
            import io, csv as _csv
            buf = io.StringIO(); w = _csv.writer(buf)
            w.writerow(header); w.writerow(row)
            data_bytes = buf.getvalue().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','text/csv; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename=match_{match_id}_stats.csv')
            self.send_header('Content-Length', str(len(data_bytes)))
            self.end_headers()
            self.wfile.write(data_bytes)
        except Exception as e:
            self.send_error_json(f"Error exporting stats: {str(e)}")

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
            <h1>ð¾ Tennis Match Analyzer test</h1>
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
                        <h3>Points Won</h3>
                        <p><span id="p1-name-inline"></span>: <strong id="p1-points-won">0</strong></p>
                        <p><span id="p2-name-inline"></span>: <strong id="p2-points-won">0</strong></p>
                    </div>
                    <div class="stat-card">
                        <h3>Breaks</h3>
                        <p><span id="p1-name-inline-2"></span>: <strong id="p1-breaks-made">0</strong></p>
                        <p><span id="p2-name-inline-2"></span>: <strong id="p2-breaks-made">0</strong></p>
                    </div>
                    <div class="stat-card">
                        <h3>Break Points</h3>
                        <p><span id="p1-name-inline-3"></span>: <strong id="p1-bp-saved">0</strong> saved / <span id="p1-bp-faced">0</span> faced</p>
                        <p><span id="p2-name-inline-3"></span>: <strong id="p2-bp-saved">0</strong> saved / <span id="p2-bp-faced">0</span> faced</p>
                    </div>
                    <div class="stat-card">
                        <h3>Key Moment</h3>
                        <p id="key-moment-desc">â</p>
                        <button id="download-stats" class="analyze-button" style="margin-top:10px;">Download match stats (CSV)</button>
                    </div>

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
        console.error(err);  // ð pour voir l'erreur exacte dans la console
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
                // Inline names for new stat cards
                document.getElementById('p1-name-inline').textContent = matchInfo.player1;
                document.getElementById('p2-name-inline').textContent = matchInfo.player2;
                document.getElementById('p1-name-inline-2').textContent = matchInfo.player1;
                document.getElementById('p2-name-inline-2').textContent = matchInfo.player2;
                document.getElementById('p1-name-inline-3').textContent = matchInfo.player1;
                document.getElementById('p2-name-inline-3').textContent = matchInfo.player2;

                // New stats from summary
                const S = data.summary || {};
                document.getElementById('p1-points-won').textContent = S.p1_points_won ?? data.points_won?.player1 ?? 0;
                document.getElementById('p2-points-won').textContent = S.p2_points_won ?? data.points_won?.player2 ?? 0;
                document.getElementById('p1-breaks-made').textContent = S.p1_breaks_made ?? data.breaks?.player1_made ?? 0;
                document.getElementById('p2-breaks-made').textContent = S.p2_breaks_made ?? data.breaks?.player2_made ?? 0;
                document.getElementById('p1-bp-faced').textContent = S.p1_bp_faced ?? data.breaks?.player1_bp_faced ?? 0;
                document.getElementById('p2-bp-faced').textContent = S.p2_bp_faced ?? data.breaks?.player2_bp_faced ?? 0;
                document.getElementById('p1-bp-saved').textContent = S.p1_bp_saved ?? data.breaks?.player1_bp_saved ?? 0;
                document.getElementById('p2-bp-saved').textContent = S.p2_bp_saved ?? data.breaks?.player2_bp_saved ?? 0;
                document.getElementById('key-moment-desc').textContent = S.key_moment_desc || (data.key_moment?.description ?? 'â');

                // Wire download button
                const dlBtn = document.getElementById('download-stats');
                if (dlBtn) dlBtn.onclick = () => { window.location.href = `/download_stats?match_id=${matchId}`; };


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
                const finalScore = data.final_score || {player1: "0", player2: "0"};
                const gameWinner = data.winner === 1 ? matchInfo.player1 : matchInfo.player2;

                gameDetails.innerHTML = `
                    <h4>Game ${data.game_number} Details</h4>
                    <p><strong>Server:</strong> ${serverName}</p>
                    <p><strong>Game Winner:</strong> ${gameWinner}</p>
                    <p><strong>Final Score:</strong> ${matchInfo.player1} ${finalScore.player1} - ${finalScore.player2} ${matchInfo.player2}</p>
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
            # Extraire les paramÃ¨tres de l'URL
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            year_filter = params.get('year', [None])[0]

            # RÃ©cupÃ©ration des donnÃ©es
            combined_data, successful_datasets = self.analyzer.fetch_all_tennis_data(
            )

            # GÃ©nÃ©rer la liste des matchs pour le frontend
            matches = self.analyzer.get_match_list(combined_data=combined_data)

            if year_filter:
                matches = [
                    m for m in matches
                    if extract_year(m.get('date')) == year_filter
                ]
                # RÃ©affecte des ID continus mais garde original_index pour analyse
                for new_id, match in enumerate(matches):
                    match['id'] = new_id

            # RÃ©pondre en JSON
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
                stats = CleanStatsEngine().analyze(combined_data=combined_data, match_id=match_id)
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