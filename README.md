# Power-Grid Optimization and Visualization Tool

## Overview  
This project models an electrical grid, computes optimal routing and network backbones under varying conditions (distance, load demand, failure probability), and provides both static and interactive visualizations to analyze grid behavior, failure impact, edge criticality, and flow-cuts.

## File Structure  
- **`main.py`**
  - Loads `nodes.csv` & `edges.csv`  
  - Computes weighted edges (`compute_weights`)  
  - Builds adjacency list (`build_graph`)  
  - Runs Dijkstra’s shortest paths, Kruskal’s MST, Edmonds–Karp max-flow/min-cut  
  - Generates `baseline_overlay.png` & `after_overlay.png`  

- **`visualization.py`**
  - Dash application:  
    - **Main View**: remove edges, select sources/sink, adjust α/β sliders

- **`nodes.csv`**
  - `Node_ID`, `Type`, `Power Supply`, `Power Demand`, `Latitude`, `Longitude`  

- **`edges.csv`** 
  - `From`, `To`, `Capacity`, `Distance`, `Failure Probability`

## Installation & Requirements  
```bash
git clone https://github.com/labishbardiya/Power-Grid-Optimization-and-Visualization-Tool/
cd Power-Grid-Optimization-and-Visualization-Tool
pip install pandas networkx plotly dash dash-bootstrap-components
```
## Usage
```bash
python main.py
```
### Produces:

- ![baseline_overlay](https://github.com/user-attachments/assets/bfb14f6b-eeb7-4b14-bd39-428c3c98c788)
- ![after_overlay](https://github.com/user-attachments/assets/533057a9-4401-4f11-b79f-bb1f8a5729ef)

## Interactive Dashboard
(It uses a subset of data for ease of understanding.)
```bash
python visualization.py
```
### Then open http://127.0.0.1:8050/ in your browser.

![Visualization](https://github.com/user-attachments/assets/afb267ca-c390-4a9a-a561-2995a45aa424)

## Core Algorithms & Their Roles

- Dijkstra’s Algorithm
Finds shortest (minimum-weight) paths from a source to all nodes; used to route power via chosen nodes.

- Kruskal’s Minimum Spanning Tree
Builds the network “backbone”: a tree connecting all nodes at minimal total cost, highlighting essential links.

- Edmonds–Karp Max-Flow / Min-Cut
Computes maximum flow from plant to city and identifies critical edges whose removal disconnects the network under stress.

## Data Flow Workflow
1. Load CSVs (`nodes.csv`, `edges.csv`)

2. Compute Weights for each edge:
- `α·distance + β·load_demand + γ·failure_probability`

3. Build Graph as adjacency list

4. Run Algorithms:

- MST (Kruskal)
- Shortest paths (Dijkstra)
- Max-flow/min-cut (Edmonds–Karp)

5. Visualize:

- Static PNGs with overlays
- Interactive Dash app with sliders, dropdowns, and analysis

## References & Inspiration

- Dijkstra, E. W. (1959). “A note on two problems in connexion with graphs.” Numerische Mathematik.
- Kruskal, J. B. (1956). “On the shortest spanning subtree of a graph and the traveling salesman problem.” Proceedings of the American Mathematical Society.
- Edmonds, J. & Karp, R. M. (1972). “Theoretical improvements in algorithmic efficiency for network flow problems.” Journal of the ACM.
