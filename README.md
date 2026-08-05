# Intelligent Agents, Search and Markov Decision Processes

Individual project on classical artificial intelligence developed by **Rodrigo Alejandro Sicilia Maroto**. The repository contains three interactive, terminal-based environments that combine knowledge-based reasoning, uninformed and informed search, Bayesian belief updates, risk-aware planning and Markov decision processes.

The project was completed for the Fundamentals of Artificial Intelligence course in the second year of the Mathematical Engineering and Artificial Intelligence degree at ICAI – Universidad Pontificia Comillas (2025/2026).

## Project overview

The repository is divided into three independent programs:

1. **Searching for Colonel Kurtz** (`kurtz.py`)
   - Partially observable grid world with three pits, one soldier, Colonel Kurtz and an exit.
   - Local percepts: breeze, snoring, glow, walls and the scream produced after a successful grenade throw.
   - Knowledge base containing observations, candidate locations and logically consistent pit configurations.
   - Safety inference and fixed-point propagation between pit, soldier and exit deductions.
   - Manual and automatic modes.
   - BFS, DFS, Greedy Best-First Search and A* with deterministic tie-breaking and detailed frontier/exploration traces.
   - Manhattan distance as the heuristic for informed search.

2. **Bayesian Palace** (`palacio.py`)
   - Probabilistic grid world containing three trap types, a soldier, an exit and Colonel Kurtz.
   - Belief matrices for each entity and deterministic Bayesian updates through evidence masks.
   - Probability and mortality-risk maps.
   - Manual and automatic modes with configurable risk threshold.
   - BFS, DFS, Greedy Best-First Search and A* for risk-aware planning.
   - Reactive grenade use and temporary risk-threshold relaxation when no route is available under the current threshold.

3. **River Crossing MDP** (`river.py`)
   - Grid-based river environment with stochastic current, islands, a start state and an exit.
   - Explicit state, action, transition and reward models.
   - Value Iteration using the Bellman optimality update.
   - Greedy policy extraction from the computed value function.
   - Episode simulation with accumulated return, success rate and average number of steps.
   - Configurable map size, random seed, number of islands, discount factor and optional deadly-island variant.

The supporting module `kurtz_colors.py` contains the ANSI terminal-colour helpers shared by the first two programs.

## AI concepts demonstrated

- Knowledge-based agents and logical inference
- Model enumeration under global constraints
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Greedy Best-First Search (GBFS)
- A* search
- Admissible and consistent Manhattan heuristic
- Deterministic tie-breaking and reproducible search traces
- Bayesian belief updating
- Probability and risk maps
- Risk-aware and adaptive planning
- Markov Decision Processes
- Bellman optimality equation
- Value Iteration
- Policy extraction and stochastic simulation

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── python-checks.yml   # Compilation and import checks
├── .gitignore
├── README.md
├── requirements.txt
├── kurtz.py                    # Knowledge-based agent and search algorithms
├── kurtz_colors.py             # ANSI terminal-colour utilities
├── palacio.py                  # Bayesian agent and risk-aware planning
├── river.py                    # River-crossing MDP and Value Iteration
└── FIA_Project_Report.pdf      # Detailed technical report
```

## Requirements

- Python 3.11 or newer
- NumPy 2.3.5
- A terminal with UTF-8 and ANSI-colour support is recommended

The project was validated with:

```text
Python 3.13.5
NumPy 2.3.5
```

No external datasets, APIs or database servers are required. Every environment is generated at runtime.

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/Rodrisici/intelligent-agents-search-mdp.git
cd intelligent-agents-search-mdp
```

Create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the programs

All commands must be executed from the repository root.

### 1. Searching for Colonel Kurtz

```bash
python kurtz.py
```

The program asks for:

- Manual or automatic mode
- Search algorithm in automatic mode: `bfs`, `dfs`, `gbfs` or `astar`
- Optional silent mode
- Optional integer random seed
- Grid size, with a default of 6

Manual controls:

```text
w / a / s / d   Move
 g               Throw the grenade, followed by a direction
 x               Exit when standing on the exit with Kurtz
 q               End the game
```

In automatic mode, the planner may ask the user whether to expand an uncertain cell when no demonstrably safe route remains. This is expected behaviour: the environment is partially observable and some generated worlds require an explicit risk decision.

### 2. Bayesian Palace

```bash
python palacio.py
```

The program asks for:

- Manual or automatic mode
- Search algorithm in automatic mode
- Optional integer random seed
- Grid size, with a default of 6
- Initial mortality-risk threshold, with a default of 0.20
- Whether to print all numerical belief and risk maps in automatic mode

Manual controls:

```text
w / a / s / d   Move
 g               Throw the grenade, followed by a direction
 x               Exit when standing on the exit with Kurtz
 m               Display numerical maps
 q               End the game
```

When an automatic route cannot be found under the current threshold, the program may offer to increase that threshold temporarily. The decision is intentionally interactive because it changes the accepted probability of death.

### 3. River Crossing MDP

```bash
python river.py
```

The program guides the user through:

- Optional integer random seed
- Default or custom map size
- Number of islands
- Discount factor in `(0, 1]`
- Optional deadly-island mode
- Value Iteration convergence output
- Number of episodes to simulate
- Detailed or summarised simulation output

The program then displays the generated world, converged value function, derived policy, transition analysis and simulation summary.

## Reproducibility

Each program accepts an optional integer seed. Reusing the same seed and configuration reproduces the generated environment. Search tie-breaking is deterministic, so search traces are stable for the same world and configuration.

The environments remain stochastic where intended. In particular, episode outcomes in the river MDP are sampled from the transition probabilities and may therefore vary between simulations unless the same random state is reproduced.

## Validation

The repository includes a GitHub Actions workflow that:

1. Installs the declared dependency.
2. Compiles all four Python modules.
3. Imports every module to verify that the dependency graph is valid.

The original source files were also checked locally with `py_compile`. Interactive smoke tests were performed for all three entry points, and the river MDP was executed through Value Iteration and episode simulation.

## Design notes

- `kurtz.py` uses 1-indexed grid coordinates, while `palacio.py` and `river.py` use 0-indexed internal coordinates. Their terminal output is designed independently for each environment.
- ANSI colours improve readability but do not affect the algorithms.
- The report refers to the river component as `river_mdp.py`; the submitted source file in this repository is named `river.py`. Both names refer to the same component.
- With a discount factor of `1.0`, Value Iteration may converge slowly or reach the configured iteration limit. The program reports this condition and returns the best value estimate obtained.

## Limitations

- The programs are educational, interactive simulations rather than production applications.
- The interfaces are terminal-based.
- Automatically generated worlds can require user-authorised risk taking when the available evidence is insufficient to prove a route safe.
- The project does not include a formal unit-test suite; the automated workflow performs compilation and import validation.

## Documentation

A detailed explanation of the world models, percepts, inference rules, search procedures, Bayesian updates, risk calculations and MDP formulation is available in [`FIA_Project_Report.pdf`](FIA_Project_Report.pdf).

## Author

**Rodrigo Alejandro Sicilia Maroto**  
Mathematical Engineering and Artificial Intelligence  
ICAI – Universidad Pontificia Comillas
