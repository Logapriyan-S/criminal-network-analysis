"""
Criminal-network analytics engine.

Given the people + edges, this builds the graph and runs the four
capabilities that make the project stand out:

  1. Key-player ranking      -> graph centrality (esp. betweenness)
  2. Gang / module detection -> Louvain community detection
  3. Hidden-link prediction  -> Adamic-Adar on non-connected pairs
  4. Plain-language reasons   -> so every result explains itself

Everything returns simple dicts/lists so a web API or the demo script
can consume it directly.
"""

import json

import networkx as nx
import community as community_louvain  # python-louvain


def load_graph(path="crime_data.json"):
    with open(path) as f:
        data = json.load(f)

    G = nx.Graph()
    for p in data["people"]:
        G.add_node(p["id"], **p)
    for e in data["edges"]:
        # if a pair has multiple edge types, keep the strongest weight
        if G.has_edge(e["source"], e["target"]):
            G[e["source"]][e["target"]]["weight"] += e["weight"]
        else:
            G.add_edge(e["source"], e["target"], weight=e["weight"], type=e["type"])
    return G, data


def rank_key_players(G, top=5):
    """Rank suspects by importance. Betweenness catches 'brokers' who
    connect otherwise-separate groups - often the real coordinator."""
    deg = nx.degree_centrality(G)
    btw = nx.betweenness_centrality(G, weight=None)
    eig = nx.eigenvector_centrality(G, max_iter=1000)

    scored = []
    for n in G.nodes():
        # combined score, weighted toward betweenness (the interesting signal)
        score = 0.3 * deg[n] + 0.5 * btw[n] + 0.2 * eig[n]
        scored.append({
            "id": n,
            "name": G.nodes[n]["name"],
            "score": round(score, 4),
            "degree": round(deg[n], 3),
            "betweenness": round(btw[n], 3),
            "eigenvector": round(eig[n], 3),
            "reason": _key_player_reason(G, n, deg[n], btw[n], eig[n]),
        })
    scored.sort(key=lambda x: -x["score"])
    return scored[:top]


def _key_player_reason(G, n, deg, btw, eig):
    reasons = []
    if btw > 0.15:
        reasons.append("acts as a broker connecting otherwise-separate groups")
    if deg > 0.4:
        reasons.append("is directly connected to many suspects")
    if eig > 0.3:
        reasons.append("is connected to other highly-connected suspects")
    if not reasons:
        reasons.append("has moderate connectivity in the network")
    return "This suspect " + "; ".join(reasons) + "."


def detect_gangs(G):
    """Find clusters (gangs/modules) without being told how many exist."""
    partition = community_louvain.best_partition(G, random_state=7)
    communities = {}
    for node, comm in partition.items():
        communities.setdefault(comm, []).append(node)
    result = []
    for comm_id, members in sorted(communities.items()):
        result.append({
            "gang_id": comm_id,
            "size": len(members),
            "members": members,
            "member_names": [G.nodes[m]["name"] for m in members],
        })
    return result, partition


def predict_hidden_links(G, top=5):
    """Suggest connections not in the data but statistically likely.
    Adamic-Adar scores non-connected pairs by their shared neighbours."""
    candidates = []
    nodes = list(G.nodes())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if not G.has_edge(a, b):
                common = list(nx.common_neighbors(G, a, b))
                if len(common) >= 2:  # only meaningful candidates
                    aa = sum(1 / (nx.degree(G, c) ** 0.5) for c in common)
                    candidates.append({
                        "a": a, "a_name": G.nodes[a]["name"],
                        "b": b, "b_name": G.nodes[b]["name"],
                        "shared_contacts": len(common),
                        "score": round(aa, 3),
                        "reason": f"No recorded direct contact, but they share "
                                  f"{len(common)} common associates \u2014 a probable hidden link.",
                    })
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:top]


def graph_for_frontend(G, partition):
    """Export nodes+edges with community colour for visualization."""
    nodes = [{
        "id": n,
        "name": G.nodes[n]["name"],
        "gang": partition.get(n, 0),
        "degree": G.degree(n),
    } for n in G.nodes()]
    edges = [{
        "source": u, "target": v,
        "type": G[u][v].get("type", "call"),
        "weight": G[u][v].get("weight", 1),
    } for u, v in G.edges()]
    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    G, data = load_graph()
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    print("=== TOP KEY PLAYERS ===")
    for i, p in enumerate(rank_key_players(G), 1):
        print(f"{i}. {p['name']} ({p['id']})  score={p['score']}  "
              f"[deg={p['degree']} btw={p['betweenness']} eig={p['eigenvector']}]")
        print(f"   {p['reason']}")

    print(f"\nGround-truth broker was: {data['ground_truth']['broker']}")

    print("\n=== DETECTED GANGS ===")
    gangs, partition = detect_gangs(G)
    for g in gangs:
        print(f"Gang {g['gang_id']}: {g['size']} members -> {', '.join(g['member_names'][:5])}"
              + (" ..." if g['size'] > 5 else ""))

    print("\n=== PREDICTED HIDDEN LINKS ===")
    for link in predict_hidden_links(G):
        print(f"{link['a_name']} <-> {link['b_name']}  "
              f"(shared={link['shared_contacts']}, score={link['score']})")
        print(f"   {link['reason']}")
