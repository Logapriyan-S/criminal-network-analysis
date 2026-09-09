"""
One-command prototype runner.

    python run.py

Generates fresh data, runs all analytics, exports the dashboard JSON,
and starts a local web server so the dashboard opens in a browser.
"""

import http.server
import json
import socketserver
import webbrowser

import generate_data
from analytics import (
    load_graph, rank_key_players, detect_gangs,
    predict_hidden_links, graph_for_frontend,
)

PORT = 8000


def build():
    print("[1/3] Generating synthetic criminal-network data...")
    generate_data.main()

    print("[2/3] Running analytics (centrality, communities, link prediction)...")
    G, data = load_graph()
    gangs, partition = detect_gangs(G)
    output = {
        "graph": graph_for_frontend(G, partition),
        "key_players": rank_key_players(G, top=5),
        "gangs": gangs,
        "hidden_links": predict_hidden_links(G, top=5),
        "stats": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "gangs": len(gangs),
        },
    }
    with open("dashboard_data.json", "w") as f:
        json.dump(output, f, indent=2)

    print("[3/3] Dashboard data ready.")
    print(f"\n    Top key player: {output['key_players'][0]['name']} "
          f"(betweenness {output['key_players'][0]['betweenness']})")
    print(f"    Groups detected: {len(gangs)}")
    print(f"    Hidden links predicted: {len(output['hidden_links'])}\n")


def serve():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print(f"Dashboard running at:  {url}")
        print("Press Ctrl+C to stop.")
        webbrowser.open(url)
        httpd.serve_forever()


if __name__ == "__main__":
    build()
    serve()
