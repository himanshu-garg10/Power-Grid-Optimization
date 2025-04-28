import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import heapq

from dash import Dash, dcc, html, Output, Input
import dash_bootstrap_components as dbc

# --- 1. Data setup ---
node_data = {
    'Node_ID': list(range(7)),
    'Type': ['City','Substation','City','Power Plant','City','Substation','City'],
    'Power Supply': [0,0,0,600,0,0,0],
    'Power Demand': [200,0,150,0,180,0,220],
    'Latitude': [14.0,13.5,15.0,12.5,16.0,14.5,15.5],
    'Longitude':[77.0,76.5,75.5,76.0,77.5,75.0,76.8]
}
nodes = pd.DataFrame(node_data)

edge_data = {
    'From': [3,3,1,1,5,5,0,2,4,6],
    'To':   [1,5,0,2,4,6,2,4,6,0],
    'Capacity':[300,300,150,150,180,180,120,120,200,200],
    'Distance':[70,80,50,60,75,85,55,65,90,95],
    'Failure Probability':[0.02,0.03,0.04,0.05,0.025,0.035,0.03,0.04,0.02,0.03]
}
edges = pd.DataFrame(edge_data)

edge_options = [{'label': f"{u}→{v}", 'value': f"{u}-{v}"} 
                for u,v in zip(edges['From'], edges['To'])]
edge_options.insert(0, {'label':'-- none --','value':''})

# --- 2. Algorithms ---
def compute_weights(df, nodes_df, alpha, beta, gamma):
    m = df.merge(
        nodes_df[['Node_ID','Power Demand']],
        left_on='To', right_on='Node_ID', how='left'
    ).rename(columns={'Power Demand':'LoadDemand'}).drop(columns=['Node_ID'])
    m['Weight'] = alpha*m['Distance'] + beta*m['LoadDemand'] + gamma*m['Failure Probability']
    return m

def build_graph(nodes_df, edf):
    g = {int(u):{} for u in nodes_df['Node_ID']}
    for _,r in edf.iterrows():
        g[int(r['From'])][int(r['To'])] = r['Weight']
    return g

def dijkstra(g, src):
    dist={u:float('inf') for u in g}
    prev={u:None for u in g}
    dist[src]=0
    heap=[(0,src)]
    while heap:
        d,u=heapq.heappop(heap)
        if d>dist[u]: continue
        for v,w in g[u].items():
            alt=d+w
            if alt<dist[v]:
                dist[v],prev[v]=alt,u
                heapq.heappush(heap,(alt,v))
    return dist, prev

def kruskal(nodes_list, edgelist):
    parent={u:u for u in nodes_list}
    rank={u:0 for u in nodes_list}
    def find(u):
        while parent[u]!=u:
            parent[u]=parent[parent[u]]
            u=parent[u]
        return u
    def union(u,v):
        ru,rv=find(u),find(v)
        if ru==rv: return False
        if rank[ru]<rank[rv]: ru,rv=rv,ru
        parent[rv]=ru
        if rank[ru]==rank[rv]: rank[ru]+=1
        return True

    mst=[]
    for u,v,w in sorted(edgelist, key=lambda x:x[2]):
        if union(u,v):
            mst.append((u,v,w))
    return mst

NX = nx.DiGraph()
for _,r in nodes.iterrows():
    NX.add_node(int(r['Node_ID']), pos=(r['Longitude'], r['Latitude']))
pos = nx.get_node_attributes(NX, 'pos')

# --- 3. Plotly trace builders ---
def edge_trace(g, color, dash, name):
    """
    Builds an edge trace with given color, dash style and legend name.
    """
    x,y,text = [],[],[]
    for u,nbrs in g.items():
        for v,w in nbrs.items():
            x0,y0 = pos[u]; x1,y1 = pos[v]
            x += [x0, x1, None]
            y += [y0, y1, None]
            text.append(f"{u}→{v}: {w:.1f}")
    return go.Scatter(
        x=x, y=y, mode='lines',
        line=dict(color=color, dash=dash),
        hoverinfo='text', text=text, name=name
    )

def nodes_trace(name):
    """
    Builds the node trace, showing node IDs.
    """
    xs,ys,labels = [],[],[]
    for u,(x,y) in pos.items():
        xs.append(x); ys.append(y); labels.append(str(u))
    return go.Scatter(
        x=xs, y=ys, mode='markers+text',
        marker=dict(size=14, color='skyblue', line=dict(width=1)),
        text=labels, textposition='top center',
        hoverinfo='text', name=name
    )

# --- 4. Build Dash App ---
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2("Interactive Power‐Grid Optimizer"),
    dbc.Row([
        dbc.Col([
            html.Label("Remove Edge:"),
            dcc.Dropdown(id="remove-edge", options=edge_options, value="")
        ], width=3),
        dbc.Col([
            html.Label("Source₁ (Power Plant):"),
            dcc.Dropdown(id="src1",
                         options=[{'label':str(u),'value':u}
                                  for u,t in zip(nodes['Node_ID'],nodes['Type']) if t=="Power Plant"],
                         value=3)
        ], width=2),
        dbc.Col([
            html.Label("Via Substation (Source₂):"),
            dcc.Dropdown(id="src2",
                         options=[{'label':str(u),'value':u}
                                  for u,t in zip(nodes['Node_ID'],nodes['Type']) if t=="Substation"],
                         value=1)
        ], width=2),
        dbc.Col([
            html.Label("Sink (City):"),
            dcc.Dropdown(id="sink",
                         options=[{'label':str(u),'value':u}
                                  for u,t in zip(nodes['Node_ID'],nodes['Type']) if t=="City"],
                         value=0)
        ], width=2)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            html.Label("α (Distance)"),
            dcc.Slider(id="alpha", min=0, max=1, step=0.01, value=0.4)
        ], width=4),
        dbc.Col([
            html.Label("β (Load Demand)"),
            dcc.Slider(id="beta",  min=0, max=1, step=0.01, value=0.3)
        ], width=4),
        dbc.Col([
            html.Label("γ (Failure Prob) = 1–α–β"),
            html.Div(id="gamma-display", style={"padding":"10px 0"})
        ], width=4)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="network-graph", style={"height":"600px"}))
    ])
], fluid=True)

# --- 5. Callback to update graph ---
@app.callback(
    Output("gamma-display","children"),
    Output("network-graph","figure"),
    Input("remove-edge","value"),
    Input("src1","value"),
    Input("src2","value"),
    Input("sink","value"),
    Input("alpha","value"),
    Input("beta","value")
)
def update(remove_edge, s1, s2, sink, a, b):
    gamma = round(1 - a - b, 2)
    if gamma < 0:
        return html.Span("ERROR: α+β > 1", style={"color":"red"}), go.Figure()

    # 1) compute weighted edges (and remove one if selected)
    ew = compute_weights(edges, nodes, a, b, gamma)
    if remove_edge:
        u,v = map(int, remove_edge.split("-"))
        ew = ew[~((ew['From']==u)&(ew['To']==v))]

    # 2) build graph and MST
    G = build_graph(nodes, ew)
    und = [(u, v, ew.loc[(ew['From']==u)&(ew['To']==v),'Weight'].values[0])
           for u in G for v in G[u]]
    mst = kruskal(list(G), und)

    # 3) shortest paths via s1→s2→sink
    dist1, prev1 = dijkstra(G, s1)
    dist2, prev2 = dijkstra(G, s2)

    path=[]
    u=s2
    while u is not None and u!=s1:
        path.append((prev1[u],u)); u=prev1[u]
    path=path[::-1]
    
    u=sink; tmp=[]
    while u is not None and u!=s2:
        tmp.append((prev2[u],u)); u=prev2[u]
    path+=tmp[::-1]
    path_set=set(path)

    # 4) build traces with legend names
    traces = [
        edge_trace(G, 'lightgray','solid',    name='All Edges'),
        edge_trace({u:{v:w for (uu,v,w) in mst if uu==u} for u in G}, 'blue','solid', name='MST'),
        edge_trace({u:{v:G[u][v] for (u,v) in path_set}},        'red','dash',  name='Chosen Path'),
        nodes_trace(name='Nodes')
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=f"α={a:.2f}, β={b:.2f}, γ={gamma:.2f} | Remove: {remove_edge or 'None'}",
        legend=dict(title='Legend')
    )

    return f"γ = {gamma:.2f}", fig

if __name__ == "__main__":
    app.run(debug=True)
