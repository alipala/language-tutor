#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse

# Default speaking prompts
DEFAULT_PROMPTS = {
    "general": [
        "Tell me about yourself and your language learning experience.",
        "Describe your hometown and what you like about it.",
        "What are your hobbies and interests?",
        "Talk about your favorite book, movie, or TV show.",
        "Describe your typical day."
    ],
    "travel": [
        "Describe a memorable trip you've taken.",
        "What's your favorite place to visit and why?",
        "Talk about a place you would like to visit in the future.",
        "Describe your ideal vacation.",
        "What do you usually do when you travel?"
    ],
    "education": [
        "Talk about your educational background.",
        "Describe a teacher who influenced you.",
        "What subjects did you enjoy studying?",
        "How do you think education has changed in recent years?",
        "Describe your learning style."
    ]
}

class PromptsServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS header
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_OPTIONS(self):
        self._set_headers()
        
    def do_GET(self):
        # Parse the URL and query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Check if this is a health check endpoint
        if parsed_path.path == '/api/health':
            self._set_headers()
            response = {'status': 'healthy'}
            self.wfile.write(json.dumps(response).encode())
            return
            
        # Check if this is the speaking prompts endpoint
        if parsed_path.path == '/api/speaking-prompts' or parsed_path.path == '/api/assessment/speaking/prompts':
            self._set_headers()
            
            # Get the language parameter (default to English)
            query_components = urllib.parse.parse_qs(parsed_path.query)
            language = query_components.get('language', ['english'])[0].lower()
            
            print(f"Received request for speaking prompts in language: {language}")
            
            # Return the default prompts (we're not actually translating here)
            response = {'prompts': DEFAULT_PROMPTS}
            self.wfile.write(json.dumps(response).encode())
            return
            
        # If the path is not recognized, return a 404
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'detail': 'Not Found'}).encode())

def run(server_class=HTTPServer, handler_class=PromptsServer, port=8001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting mock prompts server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
