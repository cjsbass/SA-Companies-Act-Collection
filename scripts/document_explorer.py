#!/usr/bin/env python3
"""
Document Explorer Server
-----------------------
A simple web server to browse and search through legal documents
without requiring Cursor to index them.
"""

import os
import sys
import json
from pathlib import Path
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import urllib.parse
import mimetypes
import datetime
import re

# Make sure to install these with pip if they're not present
try:
    import jinja2
    from jinja2 import Environment, BaseLoader
except ImportError:
    print("Please install jinja2 with: pip install jinja2")
    sys.exit(1)

# Court name mappings
COURT_NAMES = {
    "ZAGPPHC": "Pretoria High Court",
    "ZASCA": "Supreme Court of Appeal",
    "ZACC": "Constitutional Court",
    "ZAKZDHC": "KwaZulu-Natal High Court",
    "ZAWCHC": "Western Cape High Court",
    "ZAGPJHC": "Johannesburg High Court",
    "ZAECGHC": "Eastern Cape High Court (Grahamstown)",
    "ZAECPEHC": "Eastern Cape High Court (Port Elizabeth)",
    "ZAFSHC": "Free State High Court",
    "ZANWHC": "North West High Court",
    "ZALMPPHC": "Limpopo High Court",
    "ZANCHC": "Northern Cape High Court",
    "ZAMPHC": "Mpumalanga High Court",
    "ZALCC": "Land Claims Court",
    "ZALAC": "Labour Appeal Court",
    "ZALCJHB": "Labour Court (Johannesburg)",
    "ZALCCT": "Labour Court (Cape Town)",
    "ZALCPE": "Labour Court (Port Elizabeth)",
    "ZALCDBN": "Labour Court (Durban)",
    "CC": "Competition Commission",
    "CT": "Competition Tribunal",
    "CAC": "Competition Appeal Court"
}

# Document categories
DOCUMENT_CATEGORIES = {
    "judgments": "Court Judgments",
    "legislation": "Legislation",
    "regulations": "Regulations",
    "notices": "Government Notices",
    "circulars": "Circulars",
    "practice_notes": "Practice Notes",
    "rules": "Court Rules"
}

# Directory name mappings
DIRECTORY_NAMES = {
    # Main categories
    "judgments": "Court Judgments",
    "legislation": "Legislation",
    "regulations": "Regulations",
    "commercial": "Commercial Law",
    "competition": "Competition Law",
    "constitutional": "Constitutional Law",
    "criminal": "Criminal Law",
    "environmental": "Environmental Law",
    "financial": "Financial Law",
    "labour": "Labour Law",
    "property": "Property Law",
    "tax": "Tax Law",
    "core_legislation": "Core Legislation",
    "comptri": "Competition Tribunal",
    
    # Court codes
    "zacac": "Competition Appeal Court",
    "zaccma": "Companies and Intellectual Property Commission",
    "zaccp": "Competition Commission Proceedings",
    "zacgso": "State Law Advisor",
    "zacommc": "Commercial Court",
    "zaconaf": "Constitutional Affairs",
    "zact": "Competition Tribunal",
    "zaec": "Eastern Cape High Court",
    "zaecbhc": "Eastern Cape High Court (Bhisho)",
    "zaecellc": "Eastern Cape Local Division",
    "zaecghc": "Eastern Cape High Court (Grahamstown)",
    "zaechc": "Eastern Cape High Court",
    "zaecmhc": "Eastern Cape High Court (Mthatha)",
    "zagpphc": "Gauteng High Court (Pretoria)",
    "zagpjhc": "Gauteng High Court (Johannesburg)",
    "zakzdhc": "KwaZulu-Natal High Court (Durban)",
    "zakznphc": "KwaZulu-Natal High Court (Pietermaritzburg)",
    "zalmpphc": "Limpopo High Court (Polokwane)",
    "zampumalanga": "Mpumalanga High Court",
    "zanwhc": "North West High Court",
    "zanchc": "Northern Cape High Court",
    "zawchc": "Western Cape High Court",
    "zasca": "Supreme Court of Appeal",
    "zacc": "Constitutional Court",
    
    # Special jurisdictions
    "zalcc": "Land Claims Court",
    "zalac": "Labour Appeal Court",
    "zalcjhb": "Labour Court (Johannesburg)",
    "zalcct": "Labour Court (Cape Town)",
    "zalcpe": "Labour Court (Port Elizabeth)",
    "zalcdbn": "Labour Court (Durban)",
    
    # Special categories
    "zz": "Miscellaneous Documents",
    "zzmisc": "Additional Miscellaneous",
    "zzold": "Historical Documents",
    "zzpending": "Pending Documents",
    "zzarchive": "Archived Documents",
    
    # Default for unknown codes
    "unknown": "Uncategorized Documents"
}

# Court Categories
COURT_CATEGORIES = {
    "supreme": {
        "name": "Supreme Courts",
        "courts": ["ZASCA", "ZACC"],
        "description": "Supreme Court of Appeal and Constitutional Court"
    },
    "high": {
        "name": "High Courts",
        "courts": ["ZAGPPHC", "ZAGPJHC", "ZAKZDHC", "ZAWCHC", "ZAECGHC", "ZAECPEHC", "ZAFSHC", "ZANWHC", "ZALMPPHC", "ZANCHC", "ZAMPHC"],
        "description": "Provincial High Courts"
    },
    "labour": {
        "name": "Labour Courts",
        "courts": ["ZALCC", "ZALAC", "ZALCJHB", "ZALCCT", "ZALCPE", "ZALCDBN"],
        "description": "Labour Courts and Labour Appeal Court"
    },
    "competition": {
        "name": "Competition Courts",
        "courts": ["CC", "CT", "CAC", "ZACAC", "ZACCMA", "ZACCP"],
        "description": "Competition Commission, Tribunal and Appeal Court"
    },
    "specialized": {
        "name": "Specialized Courts",
        "courts": ["ZACOMMC", "ZACONAF"],
        "description": "Commercial and Constitutional Affairs Courts"
    }
}

# Add a regex_replace filter for Jinja2
def regex_replace(s, find, replace):
    """A custom filter for regex replacement"""
    return re.sub(find, replace, s)

# Initialize Jinja2 environment 
env = Environment(loader=BaseLoader)
env.filters['regex_replace'] = regex_replace

# Define HTML templates
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>South Africa Legal Documents Explorer</title>
    <style>
      :root {
        --primary-color: #1e40af;
        --secondary-color: #0ea5e9;
        --text-color: #1e293b;
        --bg-color: #f8fafc;
        --sidebar-bg: #f1f5f9;
        --border-color: #e2e8f0;
      }
      
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: var(--text-color);
        background-color: var(--bg-color);
        max-width: 1400px;
        margin: 0 auto;
        padding: 0;
      }
      
      .container {
        display: flex;
        min-height: 100vh;
      }
      
      .sidebar {
        width: 320px;
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
        padding: 2rem;
        height: 100vh;
        overflow-y: auto;
        position: sticky;
        top: 0;
      }
      
      .main-content {
        flex: 1;
        padding: 2.5rem 3rem;
        overflow-y: auto;
      }
      
      header {
        margin-bottom: 2.5rem;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 1.5rem;
      }
      
      h1 {
        color: var(--primary-color);
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
      
      h2 {
        font-size: 1.5rem;
        margin: 2rem 0 1.5rem;
        color: var(--primary-color);
        font-weight: 600;
      }
      
      h3 {
        font-size: 1.2rem;
        margin: 1.5rem 0 1rem;
        color: var(--text-color);
      }
      
      a {
        color: var(--primary-color);
        text-decoration: none;
      }
      
      a:hover {
        text-decoration: underline;
      }
      
      .breadcrumb {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        color: #64748b;
        font-size: 0.95rem;
      }
      
      .breadcrumb a {
        color: #64748b;
        text-decoration: none;
        transition: color 0.2s;
      }
      
      .breadcrumb a:hover {
        color: var(--primary-color);
      }
      
      .breadcrumb span {
        margin: 0 0.5rem;
      }
      
      .filters-section {
        background-color: white;
        border-radius: 8px;
        padding: 1.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
      }
      
      .filter-group {
        margin-bottom: 1.5rem;
      }
      
      .filter-group:last-child {
        margin-bottom: 0;
      }
      
      .filter-label {
        display: block;
        margin-bottom: 0.75rem;
        font-weight: 600;
        color: var(--text-color);
      }
      
      select {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        background-color: white;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%231e293b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 0.75rem center;
        background-size: 1rem;
      }
      
      select:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
      }
      
      input[type="text"] {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        font-size: 0.95rem;
      }
      
      input[type="text"]:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
      }
      
      button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
        width: 100%;
      }
      
      button:hover {
        background-color: #1e3a8a;
      }
      
      .quick-access {
        background-color: white;
        border-radius: 8px;
        padding: 1.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      }
      
      .quick-access-link {
        display: block;
        margin-bottom: 0.75rem;
        padding: 0.6rem 0;
        color: var(--primary-color);
        font-weight: 500;
        transition: transform 0.2s;
      }
      
      .quick-access-link:hover {
        transform: translateX(5px);
        text-decoration: none;
      }
      
      .file-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      
      .file-list li {
        margin-bottom: 0.75rem;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        transition: background-color 0.2s, transform 0.2s;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #fff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      }
      
      .file-list li:hover {
        background-color: #f1f5f9;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
      }
      
      .file-info {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
      }
      
      .file-title {
        flex: 1;
        font-size: 1rem;
        color: var(--text-color);
        text-decoration: none;
        font-weight: 500;
      }
      
      .file-title:hover {
        color: var(--primary-color);
        text-decoration: none;
      }
      
      .file-meta {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        color: #64748b;
        font-size: 0.9rem;
        white-space: nowrap;
      }
      
      .court-info {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #64748b;
        font-size: 0.9rem;
      }
      
      .court-category {
        color: #1e40af;
        font-weight: 500;
        padding: 0.4rem 0.75rem;
        background-color: #e0e7ff;
        border-radius: 4px;
        text-transform: capitalize;
      }
      
      .court-name {
        color: #4b5563;
        font-weight: 500;
      }
      
      .file-size {
        color: #64748b;
        font-size: 0.9rem;
        padding: 0.25rem 0.5rem;
        background-color: #f1f5f9;
        border-radius: 4px;
      }
      
      .stats {
        margin-top: 3rem;
        padding: 1.5rem;
        background-color: white;
        border-radius: 8px;
        font-size: 0.95rem;
        color: #4b5563;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      }
      
      .search-highlight {
        background-color: #fef9c3;
        padding: 0 0.25rem;
        border-radius: 2px;
      }
      
      .empty-state {
        padding: 3rem;
        text-align: center;
        color: #64748b;
      }
      
      .directory-link {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 6px;
        background-color: white;
        color: var(--text-color);
        text-decoration: none;
        transition: background-color 0.2s;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
      }
      
      .directory-link:hover {
        background-color: #f1f5f9;
        text-decoration: none;
      }
      
      .directory-link svg {
        margin-right: 0.75rem;
        color: #64748b;
      }
      
      @media (max-width: 992px) {
        .container {
          flex-direction: column;
        }
        
        .sidebar {
          width: 100%;
          height: auto;
          position: static;
          padding: 1.5rem;
        }
        
        .main-content {
          padding: 1.5rem;
        }
      }
      
      .results-table-container {
        overflow-x: auto;
        margin-bottom: 2rem;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      }
      
      .results-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
      }
      
      .results-table th {
        background-color: #f8fafc;
        text-align: left;
        padding: 1rem;
        font-weight: 600;
        color: #475569;
        border-bottom: 1px solid #e2e8f0;
      }
      
      .results-table td {
        padding: 1rem;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: middle;
      }
      
      .results-table tr:last-child td {
        border-bottom: none;
      }
      
      .results-table tr:hover {
        background-color: #f8fafc;
      }
      
      .column-case {
        width: 10%;
        white-space: nowrap;
      }
      
      .column-title {
        width: 40%;
      }
      
      .column-year {
        width: 8%;
        text-align: center;
      }
      
      .column-court {
        width: 27%;
      }
      
      .column-size {
        width: 10%;
        text-align: right;
      }
    </style>
    <script>
      function updateFilters() {
        const courtCategory = document.getElementById('court-category').value;
        const court = document.getElementById('court').value;
        const year = document.getElementById('year').value;
        const search = document.getElementById('search').value;
        
        window.location.href = `/?court_category=${courtCategory}&court=${court}&year=${year}&search=${encodeURIComponent(search)}`;
      }
    </script>
  </head>
  <body>
    <div class="container">
      <div class="sidebar">
        <h2>Document Filters</h2>
        <div class="filters-section">
          <div class="filter-group">
            <label class="filter-label" for="court-category">Court System</label>
            <select id="court-category" onchange="updateFilters()">
              <option value="">All Court Systems</option>
              <option value="supreme" {% if selected_court_category == 'supreme' %}selected{% endif %}>Supreme Courts</option>
              <option value="high" {% if selected_court_category == 'high' %}selected{% endif %}>High Courts</option>
              <option value="labour" {% if selected_court_category == 'labour' %}selected{% endif %}>Labour Courts</option>
              <option value="land" {% if selected_court_category == 'land' %}selected{% endif %}>Land Claims Courts</option>
              <option value="special" {% if selected_court_category == 'special' %}selected{% endif %}>Specialized Courts</option>
              <option value="tribunal" {% if selected_court_category == 'tribunal' %}selected{% endif %}>Tribunals</option>
              <option value="other" {% if selected_court_category == 'other' %}selected{% endif %}>Other Legal Documents</option>
            </select>
          </div>
          
          <div class="filter-group">
            <label class="filter-label" for="court">Specific Court</label>
            <select id="court" onchange="updateFilters()">
              <option value="">All Courts</option>
              {% for court_code in available_courts %}
              <option value="{{ court_code }}" {% if selected_court == court_code %}selected{% endif %}>{{ available_courts[court_code] }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="filter-group">
            <label class="filter-label" for="year">Publication Year</label>
            <select id="year" onchange="updateFilters()">
              <option value="">All Years</option>
              {% for year in available_years %}
              <option value="{{ year }}" {% if selected_year == year %}selected{% endif %}>{{ year }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="filter-group">
            <label class="filter-label" for="search">Document Search</label>
            <input type="text" id="search" placeholder="Search by title or content..." value="{{ search_term }}">
          </div>
          
          <button onclick="updateFilters()">Apply Filters</button>
        </div>
        
        <h2>Quick Access</h2>
        <div class="quick-access">
          {% for link in quick_links %}
          <a href="{{ link.url }}" class="quick-access-link">{{ link.name }}</a>
          {% endfor %}
        </div>
      </div>
      
      <div class="main-content">
        <header>
          <h1>South Africa Legal Documents Explorer</h1>
          <div class="breadcrumb">
            <a href="/">Home</a>
            {% for part in breadcrumbs %}
            <span>/</span>
            <a href="{{ part.url }}">{{ part.name }}</a>
            {% endfor %}
          </div>
        </header>
        
        {% if search_results %}
        <h2>Search Results for "{{ search_term }}"</h2>
        <div class="results-table-container">
          <table class="results-table">
            <thead>
              <tr>
                <th class="column-case">Case Number</th>
                <th class="column-title">Title/Description</th>
                <th class="column-year">Year</th>
                <th class="column-court">Court</th>
                <th class="column-size">Size</th>
              </tr>
            </thead>
            <tbody>
              {% for file in search_results %}
              <tr>
                <td class="column-case">
                  {% if file.year %}{{ file.name | regex_replace('.*?([0-9]+).*', '\\1') }}{% else %}-{% endif %}
                </td>
                <td class="column-title">
                  <a href="/view?file={{ file.path }}" class="file-title" title="{{ file.name }}">{{ file.friendly_title }}</a>
                </td>
                <td class="column-year">{{ file.year if file.year else "-" }}</td>
                <td class="column-court">
                  <div class="court-info">
                    {% if file.court_category %}
                    <span class="court-category">{{ file.court_category }}</span>
                    {% endif %}
                    {% if file.court_name %}
                    <span class="court-name">{{ file.court_name }}</span>
                    {% endif %}
                  </div>
                </td>
                <td class="column-size">{{ file.size }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        {% elif files %}
        <h2>Documents in {{ current_dir }}</h2>
        <div class="results-table-container">
          <table class="results-table">
            <thead>
              <tr>
                <th class="column-case">Case Number</th>
                <th class="column-title">Title/Description</th>
                <th class="column-year">Year</th>
                <th class="column-court">Court</th>
                <th class="column-size">Size</th>
              </tr>
            </thead>
            <tbody>
              {% for file in files %}
              <tr>
                <td class="column-case">
                  {% if file.year %}{{ file.name | regex_replace('.*?([0-9]+).*', '\\1') }}{% else %}-{% endif %}
                </td>
                <td class="column-title">
                  <a href="/view?file={{ file.path }}" class="file-title" title="{{ file.name }}">{{ file.friendly_title }}</a>
                </td>
                <td class="column-year">{{ file.year if file.year else "-" }}</td>
                <td class="column-court">
                  <div class="court-info">
                    {% if file.court_category %}
                    <span class="court-category">{{ file.court_category }}</span>
                    {% endif %}
                    {% if file.court_name %}
                    <span class="court-name">{{ file.court_name }}</span>
                    {% endif %}
                  </div>
                </td>
                <td class="column-size">{{ file.size }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        {% else %}
        <div class="empty-state">
          <h2>No documents found</h2>
          <p>Try adjusting your filters or search term</p>
        </div>
        {% endif %}
        
        {% if directories %}
        <h2>Directories</h2>
        <div class="directories-list">
          {% for directory in directories %}
          <a href="{{ directory.url }}" class="directory-link">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            {{ directory.name }}
          </a>
          {% endfor %}
        </div>
        {% endif %}
        
        {% if stats %}
        <div class="stats">
          <h3>Collection Statistics</h3>
          <p>Total Documents: {{ stats.total_files }}</p>
          <p>Document Types: {{ stats.file_types }}</p>
          <p>Date Range: {{ stats.date_range }}</p>
        </div>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""

VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ filename }} - Viewer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --background-color: #f8fafc;
            --text-color: #1e293b;
            --border-color: #e2e8f0;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
        }
        
        .header {
            background-color: white;
            padding: 1rem 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        h1 {
            color: var(--text-color);
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .breadcrumb {
            margin-bottom: 1.5rem;
            color: #64748b;
            font-size: 0.95rem;
        }
        
        .breadcrumb a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        
        .content {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .file-info {
            background-color: var(--background-color);
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1.5rem;
            font-size: 0.95rem;
            color: #64748b;
        }
        
        .file-info strong {
            color: var(--text-color);
            font-weight: 500;
        }
        
        .pdf-viewer {
            width: 100%;
            height: 800px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
        }
        
        .text-content {
            white-space: pre-wrap;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            background-color: var(--background-color);
            padding: 1.5rem;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        .download-link {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.75rem 1.5rem;
            background-color: var(--primary-color);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .download-link:hover {
            background-color: var(--secondary-color);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ filename }}</h1>
    </div>
    
    <div class="container">
        <div class="breadcrumb">
            <a href="/">Home</a> &gt; 
            {% for crumb in breadcrumbs %}
            <a href="/?path={{ crumb.path }}">{{ crumb.name }}</a> &gt; 
            {% endfor %}
            {{ filename }}
        </div>
        
        <div class="content">
            <div class="file-info">
                <strong>Path:</strong> {{ filepath }}<br>
                <strong>Size:</strong> {{ filesize }}<br>
                <strong>Last Modified:</strong> {{ last_modified }}
            </div>
            
            {% if is_pdf %}
            <iframe class="pdf-viewer" src="/raw?file={{ filepath }}"></iframe>
            {% elif is_text %}
            <div class="text-content">{{ file_content }}</div>
            {% else %}
            <p>This file type cannot be previewed.</p>
            <a href="/raw?file={{ filepath }}" class="download-link">Download File</a>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

class DocumentExplorerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, base_dir="scrapers_output", **kwargs):
        self.base_dir = base_dir
        super().__init__(*args, **kwargs)
    
    def get_court_category(self, court_code):
        """Get the category of a court code"""
        for category_id, category in COURT_CATEGORIES.items():
            if court_code in category["courts"]:
                return category_id, category["name"]
        return None, None
    
    def get_court_from_filename(self, filename):
        """Extract court code from filename and return full name"""
        for code in COURT_NAMES:
            if code in filename:
                return code, COURT_NAMES[code]
        return None, None
    
    def get_year_from_filename(self, filename):
        """Extract year from filename"""
        year_match = re.search(r'20[0-2][0-9]', filename)
        if year_match:
            return year_match.group(0)
        return None
    
    def get_available_years(self):
        """Get list of available years from files"""
        years = set()
        base_path = Path(self.base_dir)
        
        for file_path in base_path.glob("**/*"):
            if file_path.is_file():
                year = self.get_year_from_filename(file_path.name)
                if year:
                    years.add(year)
        
        return sorted(list(years), reverse=True)
    
    def get_friendly_directory_name(self, dir_name):
        """Convert directory code to friendly name"""
        return DIRECTORY_NAMES.get(dir_name.lower(), dir_name)
    
    def get_friendly_title(self, filename):
        """Generate a user-friendly title from the filename"""
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Extract court and year
        court_code, court_name = self.get_court_from_filename(filename)
        year = self.get_year_from_filename(filename)
        
        # Extract case number or reference
        case_match = re.search(r'[_-](\d+)[_-]', filename)
        case_number = case_match.group(1) if case_match else ""
        
        # Remove common prefixes and codes
        name = re.sub(r'^(ZA|ZASCA|ZACC|ZAGPPHC|ZAKZDHC|ZAWCHC|ZAGPJHC|ZAECGHC|ZAECPEHC|ZAFSHC|ZANWHC|ZALMPPHC|ZANCHC|ZAMPHC|ZALCC|ZALAC|ZALCJHB|ZALCCT|ZALCPE|ZALCDBN|CC|CT|CAC)_\d{4}_', '', name)
        
        # Clean up remaining text
        name = name.replace('_', ' ').replace('-', ' ')
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Capitalize words properly
        name = ' '.join(word.capitalize() for word in name.split())
        
        # Build the friendly title
        parts = []
        
        # Add descriptive prefix based on file location or type
        if "judgment" in filename.lower():
            parts.append("Judgment:")
        elif "legislation" in filename.lower():
            parts.append("Act:")
        elif "regulation" in filename.lower():
            parts.append("Regulation:")
        
        # Add the main name
        if name:
            parts.append(name)
        
        # Add case number if available
        if case_number:
            parts.append(f"(Case {case_number})")
        
        # Add year if available
        if year:
            parts.append(f"- {year}")
        
        # If we couldn't generate a meaningful title, use a cleaned-up version of the original filename
        if not parts:
            return filename.replace('_', ' ').replace('-', ' ').strip()
        
        return ' '.join(parts)
    
    def get_file_metadata(self, file_path, filename):
        """Extract and return file metadata."""
        court_code, court_name = self.get_court_from_filename(filename)
        court_category, category_name = self.get_court_category(court_code)
        year = self.get_year_from_filename(filename)
        friendly_title = self.get_friendly_title(filename)
        
        # Get file size
        try:
            full_path = Path(self.base_dir) / file_path
            size_bytes = full_path.stat().st_size
            
            if size_bytes < 1024:
                size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size = f"{size_bytes / 1024:.1f} KB"
            else:
                size = f"{size_bytes / (1024 * 1024):.1f} MB"
        except (FileNotFoundError, PermissionError):
            size = "Unknown size"
        
        return {
            "name": filename,
            "friendly_title": friendly_title,
            "path": file_path,
            "size": size,
            "court_code": court_code,
            "court_name": court_name,
            "court_category": category_name,
            "year": year
        }
    
    def get_template_vars(self, path="", filters=None):
        if filters is None:
            filters = {}
        
        base_dir = Path(self.base_dir)
        current_dir = base_dir / path if path else base_dir
        
        search_term = filters.get("search", "")
        court_filter = filters.get("court", "")
        year_filter = filters.get("year", "")
        court_category_filter = filters.get("court_category", "")
        
        # Get court categories
        available_courts = {}
        court_data = COURT_NAMES
        
        # Add courts based on filters
        for court_code, court_name in court_data.items():
            if court_category_filter:
                category = self.get_court_category(court_code)[0]
                if category == court_category_filter:
                    available_courts[court_code] = court_name
            else:
                available_courts[court_code] = court_name
        
        # Get available years from files
        available_years = self.get_available_years()
        available_years.sort(reverse=True)
        
        # Prepare quick links
        quick_links = [
            {"name": "Supreme Court of Appeal", "url": "/?court_category=supreme&court=ZASCA"},
            {"name": "Constitutional Court", "url": "/?court_category=supreme&court=ZACC"},
            {"name": "Competition Appeal Court", "url": "/?court_category=special&court=ZACAC"},
            {"name": "Companies Act", "url": "/?search=Companies+Act+71+of+2008"},
            {"name": "Competition Act", "url": "/?search=Competition+Act+89+of+1998"},
            {"name": "Consumer Protection Act", "url": "/?search=Consumer+Protection+Act"},
        ]
        
        # Handle search if specified
        if search_term:
            search_results = self.search_files(search_term, filters)
            return {
                "search_term": search_term,
                "search_results": search_results,
                "current_dir": self.get_friendly_directory_name(path) if path else "Root",
                "available_courts": available_courts,
                "available_years": available_years,
                "selected_court": court_filter,
                "selected_year": year_filter,
                "selected_court_category": court_category_filter,
                "quick_links": quick_links,
                "breadcrumbs": self.get_breadcrumbs(path),
                "stats": {
                    "total_files": len(search_results),
                    "file_types": self.get_file_type_summary(search_results),
                    "date_range": self.get_date_range(search_results)
                }
            }
        
        # List files and directories
        files = []
        directories = []
        
        try:
            for item in sorted(current_dir.iterdir()):
                if item.is_file():
                    # Apply filtering
                    if court_filter or year_filter or court_category_filter:
                        court = self.get_court_from_filename(item.name)[0]
                        year = self.get_year_from_filename(item.name)
                        category = self.get_court_category(court)[0]
                        
                        if court_filter and court != court_filter:
                            continue
                        if year_filter and year != year_filter:
                            continue
                        if court_category_filter and category != court_category_filter:
                            continue
                    
                    # Get file info
                    rel_path = str(item.relative_to(base_dir))
                    files.append(self.get_file_metadata(item, item.name))
                elif item.is_dir():
                    rel_path = str(item.relative_to(base_dir))
                    dir_name = self.get_friendly_directory_name(item.name)
                    directories.append({
                        "name": dir_name,
                        "path": rel_path,
                        "url": f"/?path={urllib.parse.quote(rel_path)}"
                    })
        except PermissionError:
            print(f"Permission error accessing {current_dir}")
        
        return {
            "search_term": search_term,
            "files": files,
            "directories": directories,
            "current_dir": self.get_friendly_directory_name(path) if path else "Root Directory",
            "breadcrumbs": self.get_breadcrumbs(path),
            "available_courts": available_courts,
            "available_years": available_years,
            "selected_court": court_filter,
            "selected_year": year_filter,
            "selected_court_category": court_category_filter,
            "quick_links": quick_links,
            "stats": {
                "total_files": len(files),
                "file_types": self.get_file_type_summary(files),
                "date_range": self.get_date_range(files)
            }
        }

    def get_breadcrumbs(self, path):
        if not path:
            return []
        
        parts = path.split('/')
        breadcrumbs = []
        current_path = ""
        
        for part in parts:
            if current_path:
                current_path = f"{current_path}/{part}"
            else:
                current_path = part
            
            breadcrumbs.append({
                "name": self.get_friendly_directory_name(part),
                "url": f"/?path={urllib.parse.quote(current_path)}"
            })
        
        return breadcrumbs
    
    def get_file_type_summary(self, files):
        """Get a summary of file types"""
        types = {}
        for file in files:
            ext = Path(file["name"]).suffix.lower()
            types[ext] = types.get(ext, 0) + 1
        
        result = []
        for ext, count in types.items():
            if ext == ".pdf":
                result.append(f"PDF ({count})")
            elif ext == ".html":
                result.append(f"HTML ({count})")
            elif ext == ".doc" or ext == ".docx":
                result.append(f"Word ({count})")
            elif ext == ".rtf":
                result.append(f"RTF ({count})")
            elif ext:
                result.append(f"{ext[1:].upper()} ({count})")
        
        return ", ".join(result)
    
    def get_date_range(self, files):
        """Get the date range of files"""
        years = set()
        for file in files:
            year = self.get_year_from_filename(file["name"])
            if year and year.isdigit():
                years.add(int(year))
        
        if not years:
            return "Unknown"
        
        years = sorted(years)
        if len(years) == 1:
            return str(years[0])
        else:
            return f"{min(years)} - {max(years)}"
    
    def search_files(self, search_term, filters=None):
        """Search for files containing the search term in their name"""
        if filters is None:
            filters = {}
            
        results = []
        base_path = Path(self.base_dir)
        
        if not search_term and not filters:
            return results
        
        search_term = search_term.lower()
        
        for file_path in base_path.glob("**/*"):
            if file_path.is_file():
                # Get friendly title for searching
                friendly_title = self.get_friendly_title(file_path.name)
                
                # Check search term against both filename and friendly title
                if search_term and search_term not in file_path.name.lower() and search_term not in friendly_title.lower():
                    continue
                
                # Apply filters
                if filters:
                    court_code, court_name = self.get_court_from_filename(file_path.name)
                    year = self.get_year_from_filename(file_path.name)
                    
                    # Apply court category filter
                    if filters.get('court_category'):
                        category = filters['court_category']
                        if not court_code or self.get_court_category(court_code)[0] != category:
                            continue
                    
                    # Apply specific court filter
                    if filters.get('court') and (not court_code or court_code != filters['court']):
                        continue
                    
                    if filters.get('year') and (not year or year != filters['year']):
                        continue
                
                results.append(self.get_file_metadata(file_path, file_path.name))
                
                if len(results) >= 100:
                    break
        
        return results
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # Handle the homepage or directory listing
        if parsed_path.path == "/":
            path = query_params.get("path", [""])[0]
            search_term = query_params.get("search", [""])[0]
            
            # Get filter values
            filters = {
                "court_category": query_params.get("court_category", [""])[0],
                "court": query_params.get("court", [""])[0],
                "year": query_params.get("year", [""])[0],
                "category": query_params.get("category", [""])[0],
                "search_term": search_term
            }
            
            template_vars = self.get_template_vars(path, filters)
            
            if search_term:
                search_results = self.search_files(search_term, filters)
                template_vars["search_results"] = search_results
            
            template = env.from_string(INDEX_TEMPLATE)
            html_content = template.render(**template_vars)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
            return
        
        # Handle file viewing
        elif parsed_path.path == "/view":
            file_path = query_params.get("file", [""])[0]
            full_path = Path(self.base_dir) / file_path
            
            if not full_path.exists() or not full_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # Get file info
            file_size = full_path.stat().st_size
            if file_size < 1024:
                file_size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                file_size_str = f"{file_size / 1024:.1f} KB"
            else:
                file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            last_modified = datetime.datetime.fromtimestamp(full_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate breadcrumbs
            breadcrumbs = []
            parent_path = full_path.parent.relative_to(Path(self.base_dir))
            parts = parent_path.parts
            current = ""
            for part in parts:
                current = str(Path(current) / part)
                breadcrumbs.append({"name": part, "path": current})
            
            # Determine file type
            is_pdf = full_path.suffix.lower() == ".pdf"
            is_text = full_path.suffix.lower() in [".txt", ".html", ".md", ".csv"]
            
            file_content = ""
            if is_text and file_size < 1024 * 1024:  # Only load text content if file is under 1MB
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    is_text = False  # If we can't decode it, don't treat as text
            
            template_vars = {
                "filename": full_path.name,
                "filepath": file_path,
                "filesize": file_size_str,
                "last_modified": last_modified,
                "breadcrumbs": breadcrumbs,
                "is_pdf": is_pdf,
                "is_text": is_text,
                "file_content": file_content
            }
            
            template = env.from_string(VIEWER_TEMPLATE)
            html_content = template.render(**template_vars)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
            return
        
        # Handle raw file access
        elif parsed_path.path == "/raw":
            file_path = query_params.get("file", [""])[0]
            full_path = Path(self.base_dir) / file_path
            
            if not full_path.exists() or not full_path.is_file():
                self.send_error(404, "File not found")
                return
            
            content_type, _ = mimetypes.guess_type(str(full_path))
            if not content_type:
                content_type = "application/octet-stream"
            
            with open(full_path, "rb") as f:
                file_content = f.read()
            
            if file_path.endswith((".html", ".htm")) and not self.is_binary_content(file_content):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(file_content)
            elif file_path.endswith(".pdf"):
                template_vars = {
                    "file_path": file_path,
                    "file_name": Path(file_path).name,
                    "file_size": file_size_str,
                }
                
                template = env.from_string(VIEWER_TEMPLATE)
                html_content = template.render(**template_vars)
                
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.send_header("Content-length", str(len(file_content)))
                self.end_headers()
                self.wfile.write(file_content)
            return
        
        # Any other path returns a 404
        self.send_error(404, "Not found")

def run_server(base_dir="scrapers_output", port=8000):
    """Run the document explorer server"""
    handler = lambda *args, **kwargs: DocumentExplorerHandler(*args, base_dir=base_dir, **kwargs)
    server = HTTPServer(("localhost", port), handler)
    print(f"Starting server at http://localhost:{port}/")
    print(f"Serving documents from: {base_dir}")
    print("Press Ctrl+C to stop the server")
    
    # Open the browser automatically
    webbrowser.open(f"http://localhost:{port}/")
    
    server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a web-based document explorer")
    parser.add_argument("--dir", default="scrapers_output", help="Directory to serve documents from")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    
    args = parser.parse_args()
    
    # Make sure the required libraries are installed
    try:
        import jinja2
    except ImportError:
        print("Please install required libraries:")
        print("pip install jinja2")
        sys.exit(1)
    
    run_server(args.dir, args.port) 