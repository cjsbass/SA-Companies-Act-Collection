#!/usr/bin/env python3
"""
serve_checklist.py - A minimal HTTP server that serves the SA Legal LLM Checklist file.

This server runs on port 8742, which is unlikely to conflict with other services.
Access the checklist at: http://localhost:8742/checklist
"""

import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

# Settings
PORT = 8742
CHECKLIST_FILE = "SA_LEGAL_LLM_CHECKLIST.md"

# Ensure we're in the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)

# Check if checklist file exists
if not os.path.exists(CHECKLIST_FILE):
    print(f"Error: Checklist file '{CHECKLIST_FILE}' not found in {os.getcwd()}")
    sys.exit(1)

# Custom request handler
class ChecklistHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/checklist'
        
        if self.path == '/checklist':
            # Serve the checklist file with proper markdown formatting
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SA Legal LLM Checklist</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <!-- GitHub markdown styling -->
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css">
                <!-- Markdown parser -->
                <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
                <style>
                    .markdown-body {{
                        box-sizing: border-box;
                        min-width: 200px;
                        max-width: 980px;
                        margin: 0 auto;
                        padding: 45px;
                    }}
                    @media (max-width: 767px) {{
                        .markdown-body {{
                            padding: 15px;
                        }}
                    }}
                    .checkbox-item {{
                        list-style-type: none;
                        margin-left: -20px;
                    }}
                    .checkbox-item input {{
                        margin-right: 10px;
                    }}
                </style>
            </head>
            <body class="markdown-body">
                <div id="content"></div>
                <script>
                    // Fetch the markdown content
                    fetch('/{CHECKLIST_FILE}')
                        .then(response => response.text())
                        .then(text => {{
                            // Replace markdown checkboxes with HTML checkboxes
                            text = text.replace(/- \\[([ xX])\\] (.*)/g, (match, checked, label) => {{
                                const isChecked = checked.toLowerCase() === 'x';
                                return `<div class="checkbox-item"><input type="checkbox" ${{isChecked ? 'checked' : ''}} disabled> ${{label}}</div>`;
                            }});
                            document.getElementById('content').innerHTML = marked.parse(text);
                        }});
                </script>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode())
            return
        
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def main():
    """Start the HTTP server and open the checklist in a browser."""
    print(f"Starting checklist server on port {PORT}...")
    
    try:
        with socketserver.TCPServer(("", PORT), ChecklistHandler) as httpd:
            print(f"Serving at: http://localhost:{PORT}/checklist")
            print(f"Press Ctrl+C to stop the server")
            
            # Open the checklist in the default browser
            webbrowser.open(f"http://localhost:{PORT}/checklist")
            
            # Start the server
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 