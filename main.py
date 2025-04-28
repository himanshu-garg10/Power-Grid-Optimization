import pandas as pd
import matplotlib.pyplot as plt
import random
import heapq
import traceback
from collections import deque
from matplotlib.lines import Line2D
import networkx as nx

# Compute edge weights based on rules: Distance, Load Demand, and Failure Probability
def compute_weights(edges_df, nodes_df, alpha, beta, gamma):
    """
    Computes the weight of each edge in the graph based on three factors:
    1. Distance between nodes
    2. Load demand at the destination node
    3. Failure probability of the edge
    
    Parameters:
    - edges_df: DataFrame containing edge data with columns like 'From', 'To', 'Distance'
    - nodes_df: DataFrame containing node data with 'Node_ID' and 'Power Demand'
    - alpha, beta, gamma: Weights for each factor in the computation

    Returns:
    - A DataFrame with the computed edge weights.
    """
    merged = edges_df.merge(
        nodes_df[['Node_ID', 'Power Demand']], 
        left_on='To', right_on='Node_ID', how='left'
    ).rename(columns={'Power Demand': 'Load Demand'}).drop(columns=['Node_ID'])
    
    # Calculate edge weight as a weighted sum of Distance, Load Demand, and Failure Probability
    merged['Weight'] = (
        alpha * merged['Distance'] + 
        beta * merged['Load Demand'] + 
        gamma * merged['Failure Probability']
    )
    return merged

# Build a directed graph from the nodes and edges data
def build_graph(nodes_df, edges_df):
    """
    Builds a directed graph from the node and edge data.

    Parameters:
    - nodes_df: DataFrame with node details.
    - edges_df: DataFrame with edges and their respective weights.

    Returns:
    - A dictionary representing the directed graph.
    """
    graph = {int(n): {} for n in nodes_df['Node_ID']}  # Initialize nodes in the graph
    for _, row in edges_df.iterrows():
        u, v = int(row['From']), int(row['To'])
        graph[u][v] = {'weight': row['Weight'], 'capacity': row['Capacity']}
    return graph

# Dijkstra's Algorithm to find the shortest path from the source node
def dijkstra(graph, source):
    """
    Implements Dijkstra's shortest path algorithm to find the minimum cost path 
    from the source node to all other nodes in the graph.
    
    Parameters:
    - graph: The graph represented as an adjacency list.
    - source: The node from which shortest paths are calculated.
    
    Returns:
    - dist: Dictionary of shortest distances from source to each node.
    - prev: Dictionary storing the previous node in the shortest path to each node.
    """
    dist = {u: float('inf') for u in graph}  # Initialize distances to infinity
    prev = {u: None for u in graph}  # Initialize previous node to None
    dist[source] = 0  # Distance to source is 0
    heap = [(0, source)]  # Min-heap for selecting the node with the smallest distance

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue  # Skip if we've already found a shorter path to u
        for v, data in graph[u].items():
            alt = d + data['weight']  # Calculate alternative path distance
            if alt < dist[v]:
                dist[v] = alt  # Update shortest distance
                prev[v] = u  # Update previous node
                heapq.heappush(heap, (alt, v))  # Push updated node to heap

    return dist, prev

# Kruskal's Algorithm to find the Minimum Spanning Tree (MST) of an undirected graph
def kruskal_mst(nodes, edges):
    """
    Implements Kruskal's algorithm to find the Minimum Spanning Tree (MST) for the graph.
    
    Parameters:
    - nodes: List of node IDs.
    - edges: List of edges as (u, v, weight) tuples.
    
    Returns:
    - mst: A list of edges in the Minimum Spanning Tree.
    """
    parent = {u: u for u in nodes}  # Initialize parent for each node
    rank = {u: 0 for u in nodes}  # Initialize rank (used for union-find)
    
    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]  # Path compression
            u = parent[u]
        return u
    
    def union(u, v):
        ru, rv = find(u), find(v)
        if ru == rv: return False  # Skip if nodes are already connected
        if rank[ru] < rank[rv]:
            ru, rv = rv, ru  # Union by rank
        parent[rv] = ru
        if rank[ru] == rank[rv]:
            rank[ru] += 1
        return True
    
    mst = []
    for u, v, w in sorted(edges, key=lambda x: x[2]):
        if union(u, v):
            mst.append((u, v, w))

    return mst

# Edmonds-Karp algorithm to compute Max-Flow/Min-Cut
def edmonds_karp(graph, source, sink):
    """
    Implements the Edmonds-Karp algorithm for calculating the maximum flow 
    and minimum cut in a flow network using the Ford-Fulkerson method.
    
    Parameters:
    - graph: Directed graph represented by adjacency list with edge capacities.
    - source: Source node of the flow.
    - sink: Sink node of the flow.
    
    Returns:
    - max_flow: The total maximum flow from source to sink.
    - cut: The minimum cut that separates the source and sink.
    """
    residual = {u: {} for u in graph}
    for u in graph:
        for v, d in graph[u].items():
            residual[u][v] = d['capacity']
            residual[v].setdefault(u, 0)
    
    max_flow, parent = 0, {}
    
    def bfs():
        visited = {source}; queue = deque([source]); parent.clear()
        while queue:
            u = queue.popleft()
            for v, cap in residual[u].items():
                if v not in visited and cap > 0:
                    visited.add(v)
                    parent[v] = u
                    if v == sink:
                        return True
                    queue.append(v)
        return False

    while bfs():
        path_flow = float('inf')
        s = sink
        while s != source:
            path_flow = min(path_flow, residual[parent[s]][s])
            s = parent[s]
        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= path_flow
            residual[v][u] += path_flow
            v = u
        max_flow += path_flow

    visited = {source}; stack = [source]
    while stack:
        u = stack.pop()
        for v, cap in residual[u].items():
            if v not in visited and cap > 0:
                visited.add(v)
                stack.append(v)
    cut = [(u, v) for u in visited for v in graph[u] if v not in visited]
    return max_flow, cut

# Plotting the graph with enhanced edge styles and displaying weights
def plot_with_overlays_networkx(graph, nodes_df, title, fname, mst_edges=None, prev=None):
    """
    Visualizes the directed graph using NetworkX, highlighting Minimum Spanning Tree (MST) and shortest paths.
    
    Parameters:
    - graph: Directed graph to visualize.
    - nodes_df: DataFrame containing node details (e.g., ID, type, position).
    - title: Title of the graph.
    - fname: Filename to save the plot.
    - mst_edges: Optional edges to highlight as MST.
    - prev: Previous node for shortest path highlights.
    """
    G = nx.DiGraph()

    for _, r in nodes_df.iterrows():
        G.add_node(int(r['Node_ID']), pos=(r['Longitude'], r['Latitude']), type=r['Type'])

    for _, row in graph.items():
        for v, data in row.items():
            G.add_edge(_, v, weight=data['weight'], capacity=data['capacity'])

    pos = nx.get_node_attributes(G, 'pos')
    nx.draw(G, pos, with_labels=True, node_size=300, node_color='lightblue', font_size=8, font_weight='bold', arrows=True)
    
    # Plot edges with weight labels
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    # Highlight MST edges in blue
    if mst_edges:
        mst_edges = [(u, v) for u, v, _ in mst_edges]
        nx.draw_networkx_edges(G, pos, edgelist=mst_edges, edge_color='blue', width=2)

    # Highlight shortest paths in yellow (dashed)
    if prev:
        for v in prev:
            u = prev[v]
            if u is not None:
                nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color='yellow', style='dashed', width=2)

    plt.title(title)
    plt.axis('off')
    plt.savefig(fname, bbox_inches='tight')
    plt.close()

# Demonstration
if __name__ == '__main__':
    # Load the node and edge data
    nodes = pd.read_csv('nodes.csv')
    edges = pd.read_csv('edges.csv')
    
    # Set weights for edge computation
    alpha, beta, gamma = 0.4, 0.3, 0.2
    edges_w = compute_weights(edges, nodes, alpha, beta, gamma)
    
    # Build the graph
    graph = build_graph(nodes, edges_w)
    
    # Find the source node with maximum power supply
    source = int(nodes.loc[nodes['Power Supply'].idxmax(), 'Node_ID'])
    
    # Run Dijkstra’s algorithm
    dist, prev = dijkstra(graph, source)
    
    # Kruskal's MST
    undirected_edges = [(u, v, d['weight']) for u in graph for v, d in graph[u].items()]
    mst = kruskal_mst(list(graph), undirected_edges)
    
    # Plot with overlays
    plot_with_overlays_networkx(graph, nodes, 'Baseline with MST (blue) & Shortest Paths (yellow)', 'baseline_overlay.png', mst_edges=mst, prev=prev)
    
    # Simulate edge failure
    u, v = random.choice([(u, v) for u in graph for v in graph[u]])
    mod_edges_df = edges[~((edges['From'] == u) & (edges['To'] == v))]  # Remove the failed edge
    edges_w2 = compute_weights(mod_edges_df, nodes, alpha, beta, gamma)
    graph2 = build_graph(nodes, edges_w2)
    
    # Re-run Dijkstra and MST after failure
    dist2, prev2 = dijkstra(graph2, source)
    mst2 = kruskal_mst(list(graph2), [(u, v, d['weight']) for u in graph2 for v, d in graph2[u].items()])
    
    # Plot after failure
    plot_with_overlays_networkx(graph2, nodes, f'After Failure {u}->{v}', 'after_overlay.png', mst_edges=mst2, prev=prev2)
    
    print('Done: baseline_overlay.png, after_overlay.png')
