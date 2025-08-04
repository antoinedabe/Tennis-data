# Replit Agent Guide

## Overview

This is a Tennis Match Analyzer web application that combines Python backend data analysis with a modern HTML/CSS frontend. The application analyzes point-by-point tennis match data from GitHub datasets and displays comprehensive statistics through an interactive web interface. It demonstrates full-stack development using Python's HTTP server, data processing with CSV/requests libraries, and responsive web design.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Python HTTP Server**: Custom web server using BaseHTTPRequestHandler for routing and data serving
- **Data Analysis Engine**: TennisAnalyzer class that fetches and processes CSV tennis match data
- **API Endpoints**: RESTful endpoints for serving HTML interface and JSON analysis results
- **Real-time Processing**: Fetches live data from GitHub tennis datasets on demand

### Frontend Architecture
- **Single-page application**: Modern HTML5/CSS3/JavaScript interface with embedded styling
- **Responsive design**: Mobile-first approach with CSS Grid and Flexbox layouts
- **Interactive dashboard**: Real-time statistics display with player comparisons and match summaries
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