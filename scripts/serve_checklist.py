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
                        padding: 6px 8px;
                        border-radius: 6px;
                        margin-bottom: 5px;
                        transition: background-color 0.3s;
                    }}
                    .checkbox-item:hover {{
                        background-color: #f0f0f0;
                    }}
                    .checkbox-checked {{
                        background-color: rgba(46, 160, 67, 0.15);
                        border-left: 4px solid #2ea043;
                    }}
                    .checkbox-unchecked {{
                        background-color: rgba(248, 81, 73, 0.15);
                        border-left: 4px solid #f85149;
                    }}
                    .checkbox-item input {{
                        margin-right: 10px;
                    }}
                    .checkbox-label {{
                        font-weight: 500;
                    }}
                    .progress-bar {{
                        height: 10px;
                        background-color: #eee;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                    .progress-fill {{
                        height: 100%;
                        background-color: #2ea043;
                        border-radius: 5px;
                        transition: width 0.5s;
                    }}
                    .category-header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .category-progress {{
                        font-size: 14px;
                        color: #666;
                    }}
                    details {{
                        margin-bottom: 15px;
                    }}
                    details summary {{
                        cursor: pointer;
                        font-weight: bold;
                        padding: 8px;
                        background-color: #f6f8fa;
                        border-radius: 6px;
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
                                const checkboxClass = isChecked ? 'checkbox-checked' : 'checkbox-unchecked';
                                const checkIcon = isChecked ? '✅' : '❌';
                                return `<div class="checkbox-item ${{checkboxClass}}">
                                           <span class="checkbox-icon">${{checkIcon}}</span>
                                           <span class="checkbox-label">${{label}}</span>
                                        </div>`;
                            }});
                            
                            // Replace section headers with collapsible sections that show progress
                            text = text.replace(/(## ([^\\n]+))/g, (match, header, title) => {{
                                if (title === 'Progress Summary') return match;
                                return `<div class="category-header">
                                          ${{header}}
                                          <span class="category-progress" data-category="${{title.trim()}}">0%</span>
                                        </div>
                                        <div class="progress-bar">
                                          <div class="progress-fill" data-category-bar="${{title.trim()}}" style="width: 0%"></div>
                                        </div>`;
                            }});
                            
                            document.getElementById('content').innerHTML = marked.parse(text);
                            
                            // Calculate and display progress per category
                            document.querySelectorAll('h2').forEach(header => {{
                                if (header.textContent.includes('Progress Summary')) return;
                                
                                const categoryName = header.textContent.trim();
                                const categoryItems = header.nextElementSibling.nextElementSibling.querySelectorAll('.checkbox-item');
                                
                                if (categoryItems.length === 0) return;
                                
                                const totalItems = categoryItems.length;
                                const completedItems = Array.from(categoryItems).filter(item => 
                                    item.classList.contains('checkbox-checked')).length;
                                
                                const percentage = Math.round((completedItems / totalItems) * 100);
                                
                                // Update the progress displays
                                document.querySelector(`[data-category="${{categoryName}}"]`).textContent = 
                                    `${{completedItems}}/${{totalItems}} (${{percentage}}%)`;
                                document.querySelector(`[data-category-bar="${{categoryName}}"]`).style.width = 
                                    `${{percentage}}%`;
                            }});
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
    global PORT
    print(f"Starting checklist server on port {PORT}...")
    
    # Try up to 10 different ports if the default is in use
    for attempt in range(10):
        try:
            with socketserver.TCPServer(("", PORT), ChecklistHandler) as httpd:
                print(f"Serving at: http://localhost:{PORT}/checklist")
                print(f"Press Ctrl+C to stop the server")
                
                # Open the checklist in the default browser
                webbrowser.open(f"http://localhost:{PORT}/checklist")
                
                # Start the server
                httpd.serve_forever()
        except OSError as e:
            if e.errno == 48:  # Address already in use
                PORT += 1
                print(f"Port {PORT-1} is in use, trying port {PORT}...")
            else:
                print(f"Error: {e}")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    print(f"Could not find an available port after {attempt+1} attempts.")
    sys.exit(1)

if __name__ == "__main__":
    main() 