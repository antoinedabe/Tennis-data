# Replit Agent Guide

## Overview

This is a comprehensive Tennis Match Analyzer web application that combines Python backend data analysis with a modern HTML/CSS frontend. The application provides three levels of analysis: (1) browseable list of tennis matches, (2) detailed match statistics with game breakdown, and (3) point-by-point analysis of individual games showing every shot and outcome. Users can drill down from match selection to specific game analysis with complete shot-by-shot breakdowns. It demonstrates advanced full-stack development using Python's HTTP server, complex data processing, and interactive web design.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Python HTTP Server**: Custom web server using BaseHTTPRequestHandler for routing and data serving
- **Data Analysis Engine**: TennisAnalyzer class that fetches and processes CSV tennis match data
- **API Endpoints**: RESTful endpoints for match list (`/matches`), match analysis (`/analyze/{id}`), and game analysis (`/analyze/{match_id}/{game_id}`)
- **Multi-level Analysis System**: Users can browse matches, analyze match statistics, then drill down to specific games with point-by-point shot analysis
- **Game Selection System**: Interactive grid showing all games in a match with server information and point counts
- **Real-time Processing**: Fetches live data from GitHub tennis datasets on demand

### Frontend Architecture
- **Single-page application**: Modern HTML5/CSS3/JavaScript interface with embedded styling
- **Responsive design**: Mobile-first approach with CSS Grid and Flexbox layouts
- **Match Browser**: Scrollable list of available matches with player names, dates, scores, and winners
- **Year Filter**: Dropdown filter to browse matches by specific years (2017, etc.) with match count display
- **Game Grid Interface**: Visual grid of games within each match showing server and point count information
- **Point-by-Point Analysis**: Detailed breakdown of every shot in a game with color-coded player actions and outcomes
- **Interactive dashboard**: Multi-level statistics display from match overview to individual point analysis
- **Asynchronous requests**: JavaScript fetch API for seamless data retrieval without page refresh

### Data Processing Pipeline
- **External Data Source**: Tennis point-by-point data from JeffSackmann's GitHub repository
- **CSV Processing**: Real-time parsing and analysis of match statistics including aces, winners, errors
- **Statistical Analysis**: Calculation of player comparisons, rally lengths, and match summaries
- **JSON API**: Structured data delivery for frontend consumption

### File Structure
- **app.py**: Main Python application with HTTP server, data analysis, and routing logic
- **index.html**: Replaced by embedded HTML template in Python server for dynamic content
- **Integrated approach**: Single Python file contains both backend logic and frontend template

## External Dependencies

### Python Libraries
- **requests**: HTTP client for fetching external tennis data from GitHub
- **csv**: Built-in library for parsing tennis match data
- **http.server**: Built-in HTTP server infrastructure
- **json**: Built-in JSON serialization for API responses

### Data Sources
- **GitHub Tennis Dataset**: Real tennis match data from github.com/JeffSackmann/tennis_pointbypoint
- **Live Data Fetching**: No local data storage, fetches fresh data on each analysis request

### Browser Requirements
- **Modern browser support**: ES6+ JavaScript features, CSS Grid, and Flexbox support
- **API compatibility**: Fetch API support for asynchronous data requests
- **Responsive design**: Mobile and desktop compatibility