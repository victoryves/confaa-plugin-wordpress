"""Testa imports um por um para identificar qual está falhando."""
import sys
import os
import json
import traceback
from http.server import BaseHTTPRequestHandler

# Garante que o root do projeto está no path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

results = {}

try:
    from supabase import create_client
    results["supabase"] = "ok"
except Exception as e:
    results["supabase"] = str(e)

try:
    from scrapling import Fetcher
    results["scrapling"] = "ok"
except Exception as e:
    results["scrapling"] = str(e)

try:
    import requests
    results["requests"] = "ok"
except Exception as e:
    results["requests"] = str(e)

try:
    from lib.classifier import classify_article
    results["lib.classifier"] = "ok"
except Exception as e:
    results["lib.classifier"] = str(e)

try:
    from lib.filter import is_violent_content
    results["lib.filter"] = "ok"
except Exception as e:
    results["lib.filter"] = str(e)

try:
    from lib.supabase_client import get_client
    results["lib.supabase_client"] = "ok"
except Exception as e:
    results["lib.supabase_client"] = str(e)

try:
    from lib.scraper_base import BaseScraper
    results["lib.scraper_base"] = "ok"
except Exception as e:
    results["lib.scraper_base"] = str(e)

results["sys_path_root"] = ROOT
results["cwd"] = os.getcwd()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(results, indent=2).encode())
