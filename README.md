# Intelligent Agents, Search and Markov Decision Processes

[![Python checks](https://github.com/rodrigosicilia/intelligent-agents-search-mdp/actions/workflows/python-checks.yml/badge.svg)](https://github.com/rodrigosicilia/intelligent-agents-search-mdp/actions/workflows/python-checks.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Three interactive, terminal-based artificial intelligence environments implemented from
scratch in Python, without AI or search libraries. Together they cover knowledge-based
reasoning, uninformed and informed search, Bayesian belief updating, risk-aware planning
and Markov decision processes.

Individual project by **Rodrigo Alejandro Sicilia Maroto**, written for the Fundamentals of
Artificial Intelligence course in the second year of the Mathematical Engineering and
Artificial Intelligence degree at ICAI – Universidad Pontificia Comillas (2025/2026).

> **Note on language.** This documentation is in English, but the source-code comments and
> the interactive console interface are in **Spanish**, as originally submitted. The
> algorithms are of course language-independent, and every prompt you will encounter is
> translated below, so the programs can be followed without reading Spanish.

## Table of contents

- [Project overview](#project-overview)
- [AI concepts demonstrated](#ai-concepts-demonstrated)
- [Sample output](#sample-output)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the programs](#running-the-programs)
- [Reproducibility](#reproducibility)
- [Validation](#validation)
- [Design notes](#design-notes)
- [Limitations](#limitations)
- [Documentation](#documentation)
- [License](#license)
- [Author](#author)

## Project overview

The repository contains three independent programs.

### 1. Searching for Colonel Kurtz (`kurtz.py`)

A **knowledge-based agent** in a partially observable grid world, in the spirit of the
classic Wumpus World.

- Grid containing three pits, one soldier, Colonel Kurtz and an exit.
- Local percepts only: breeze, snoring, glow, walls, and the scream produced by a
  successful grenade throw.
- A knowledge base holding observations, candidate locations and the set of logically
  consistent pit configurations.
- Model enumeration under global constraints, plus fixed-point propagation between the
  pit, soldier and exit deductions until no new fact can be derived.
- BFS, DFS, Greedy Best-First Search and A\*, restricted to cells that have been *proved*
  safe, with deterministic tie-breaking and full frontier/explored traces.
- Manhattan distance as the heuristic for informed search.
- Manual and automatic modes.

### 2. Bayesian Palace (`palacio.py`)

A **probabilistic agent** that reasons about uncertainty instead of proving safety.

- Grid world containing three trap types, a soldier, an exit and Colonel Kurtz.
- One belief matrix per entity, updated by deterministic Bayesian conditioning through
  evidence masks.
- Derived probability maps and an aggregate mortality-risk map.
- Risk-aware planning: BFS, DFS, GBFS and A\* over the cells whose estimated risk of death
  falls below a configurable threshold.
- Reactive grenade use, and temporary relaxation of the risk threshold when no route
  exists under the current one.
- Manual and automatic modes.

### 3. River Crossing MDP (`river.py`)

A **Markov decision process** solved exactly by dynamic programming.

- Grid-based river with a per-column stochastic current, islands, a start state and an exit.
- Explicit state, action, transition and reward models.
- Value Iteration using the Bellman optimality update.
- Greedy policy extraction from the converged value function.
- Episode simulation reporting accumulated return, success rate and average step count.
- Configurable map size, random seed, number of islands, discount factor, and an optional
  deadly-island variant in which entering an island is a terminal, heavily penalised event.

The supporting module `kurtz_colors.py` contains the ANSI terminal-colour helpers shared by
the first two programs.

## AI concepts demonstrated

| Area | Techniques |
| --- | --- |
| Knowledge-based agents | Logical inference, model enumeration under global constraints, fixed-point propagation, provable safety |
| Uninformed search | Breadth-First Search, Depth-First Search |
| Informed search | Greedy Best-First Search, A\*, admissible and consistent Manhattan heuristic |
| Search engineering | Deterministic tie-breaking, reproducible frontier/explored traces, closed sets, g-value relaxation |
| Probabilistic reasoning | Bayesian belief updating, evidence masks, probability and mortality-risk maps |
| Decision making under risk | Risk thresholds, risk-aware path planning, adaptive threshold relaxation |
| Markov decision processes | Transition and reward models, Bellman optimality equation, Value Iteration, greedy policy extraction, stochastic simulation |

Everything is implemented directly from the underlying mathematics. The only third-party
dependency is NumPy, used purely for array storage and arithmetic in the belief and value
tables.

## Sample output

### River Crossing MDP

Generated world, converged value function and extracted policy (seed `42`, default 7×6 map,
two islands, discount `1.0`):

```text
Mapa generado
Seed=42 | start=(0, 0) | exit=(5, 5)
Islas=2/20 | islas_peligrosas=False | descuento(extra)=1.0
river_strength por columna: [0.0, 0.7, 0.3, 0.2, 0.2, 0.0]
|| CWCK  R     R     R     R     |     ||
|| |     I     R     R     I     |     ||
|| |     R     R     R     R     |     ||
|| |     R     R     R     R     |     ||
|| |     R     R     R     R     |     ||
|| |     R     R     R     R     E     ||
|| |     R     R     R     R     |     ||

Convergencia: iteraciones=58 | delta_final=8.014e-07 | convergido=True

Tabla de valores V(s):
  S    88.6  92.0  93.0  93.8  95.0
 89.4   I    93.0  94.0   I    96.0
 90.4  91.4  93.9  95.0  96.0  97.0
 90.8  91.8  94.8  95.9  97.0  98.0
 90.9  91.9  95.4  96.8  97.9  99.0
 90.9  91.9  95.5  97.1  98.6   E
 90.7  91.7  95.1  96.5  97.8  99.0

Politica optima:
||   Sv    >     >     v     >     v   ||
||   v     I     >     v     I     v   ||
||   >     >     >     >     >     v   ||
||   >     >     >     >     >     v   ||
||   >     >     >     >     >     v   ||
||   >     >     >     >     >     E   ||
||   >     >     >     >     >     ^   ||

Resumen final de simulacion:
Exitos: 3/3
Media de puntos: 90.000
Pasos medios: 10.00
```

Legend: `R` is open river, `I` an island, `|` a bank, `E` the exit. Note that column 1 has
`river_strength=0.7`: the optimal policy avoids lingering there, because any action other
than `down` has a 70 % chance of being pushed downstream instead.

### Searching for Colonel Kurtz

Search trace and the internal map of the agent (A\*, seed `3`):

```text
=== PLANIFICACION A KURTZ ===
[Plan] Step 0 | Frontier={(1, 1)(4)} | Removed=(1, 1)(4) | Explored={(1, 1)(4)}
[Plan] Step 1 | Frontier={(1, 2)(4),(2, 1)(4)} | Removed=(1, 2)(4) | Explored={(1, 1)(4),(1, 2)(4)}
[Plan] Step 2 | Frontier={(2, 1)(4),(1, 3)(6),(2, 2)(4)} | Removed=(2, 1)(4) | Explored={...}

[Auto] Plan 1 (posiciones): (1, 1) -> (1, 2) -> (2, 2) -> (3, 2) -> (4, 2)
[Auto] Plan 1 (teclas):     d s s s

=== PALACIO (conocimiento del agente) ===
         1       2       3       4       5       6
      ------------------------------------------------
  1 |    CW      v       .       .       .       .
  2 |    v       .       .       .       .       .
  3 |    .       .       .       .       .       .
  4 |    .       .       .       .       .       .
  5 |    .       .       .       .       .       .
  6 |    .       .       .       .       .       .

Percepto:[Brisa=0, Ronquido=0, Resplandor=0, Pared_arriba=1, ...]
```

Each frontier entry is printed as `(row, col)(f-value)`, so the whole A\* expansion order
can be checked by hand. In the board, `CW` is the agent, `v` a visited cell, `.` an unknown
cell, `P?`/`S?` a possible hazard, `P!`/`S!` a certain hazard, and `E?`/`E!` a candidate or
confirmed exit.

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── python-checks.yml   # CI: compilation, imports and an end-to-end MDP run
├── .gitattributes              # Deterministic line endings across platforms
├── .gitignore
├── LICENSE                     # MIT
├── README.md
├── requirements.txt
├── kurtz.py                    # Knowledge-based agent and search algorithms
├── kurtz_colors.py             # ANSI terminal-colour utilities
├── palacio.py                  # Bayesian agent and risk-aware planning
├── river.py                    # River-crossing MDP and Value Iteration
└── FIA_Project_Report.pdf      # Detailed technical report (Spanish)
```

## Requirements

- Python 3.11 or newer
- NumPy 2.x
- A terminal with UTF-8 and ANSI-colour support is recommended

The project was developed and validated with:

```text
Python 3.13.5
NumPy 2.3.5
```

Continuous integration additionally exercises Python 3.11, 3.12 and 3.13.

No external datasets, APIs or database servers are required: every environment is generated
at runtime.

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/rodrigosicilia/intelligent-agents-search-mdp.git
```

```bash
cd intelligent-agents-search-mdp
```

Create and activate a virtual environment, then install the dependency.

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

All commands must be executed from the repository root. Each program is fully interactive
and prompts in Spanish; the tables below translate every question you will be asked.
Pressing <kbd>Enter</kbd> always accepts the default shown in the prompt.

### 1. Searching for Colonel Kurtz

```bash
python kurtz.py
```

| Prompt (Spanish) | Meaning | Accepted values |
| --- | --- | --- |
| `Elige modo [manual/auto]` | Manual or automatic mode | `manual`, `auto` |
| `Elige búsqueda [bfs/dfs/gbfs/astar]` | Search algorithm (automatic mode only) | `bfs`, `dfs`, `gbfs`, `astar` |
| `¿Modo silencioso?` | Suppress the detailed traces | `s` = yes, `n` = no |
| `Semilla` | Random seed | any integer, or Enter for random |
| `Tamaño del tablero n` | Grid size | integer ≥ 3, default 6 |

Manual controls:

```text
w / a / s / d   Move up / left / down / right
g               Throw the grenade, followed by a direction key
x               Exit, when standing on the exit together with Kurtz
q               End the game
```

In automatic mode the planner may ask whether to expand an uncertain cell when no
demonstrably safe route remains. This is expected: the environment is partially observable,
and some generated worlds cannot be solved without an explicit risk decision.

### 2. Bayesian Palace

```bash
python palacio.py
```

| Prompt (Spanish) | Meaning | Accepted values |
| --- | --- | --- |
| `Modo [manual/auto]` | Manual or automatic mode | `manual`, `auto` |
| `Búsqueda [bfs/dfs/gbfs/astar]` | Search algorithm | `bfs`, `dfs`, `gbfs`, `astar` |
| `¿Modo silencioso?` | Suppress the detailed traces | `s` = yes, `n` = no |
| `Semilla` | Random seed | any integer, or Enter for random |
| `Tamaño n` | Grid size | integer ≥ 3, default 6 |
| `Umbral de riesgo p` | Maximum accepted probability of death per cell | float in `[0, 1]`, default `0.20` |
| `¿Imprimir TODOS los mapas numéricos?` | Print every belief and risk matrix | `s`, `n` |

Manual controls:

```text
w / a / s / d   Move up / left / down / right
g               Throw the grenade, followed by a direction key
x               Exit, when standing on the exit together with Kurtz
m               Display the numerical belief and risk maps
q               End the game
```

When no route exists under the current threshold, the program offers to raise it
temporarily. That decision is deliberately left to the user, because it changes the accepted
probability of death.

### 3. River Crossing MDP

```bash
python river.py
```

| Prompt (Spanish) | Meaning | Accepted values |
| --- | --- | --- |
| `Semilla` | Random seed | any integer, or Enter for random |
| `¿Usar tamaño 7x6?` | Keep the default map size | `s`, `n` |
| `Filas` / `Columnas` | Custom map size | integers ≥ 2 |
| `Número de islas` | Islands placed in the interior | integer ≥ 0, default 2 |
| `Factor de descuento` | Discount factor γ | float in `(0, 1]`, default `1.0` |
| `¿Activar islas peligrosas?` | Islands become terminal and penalised | `s`, `n` |
| `¿Mostrar deltas de convergencia?` | Print the Value Iteration deltas | `s`, `n` |
| `Número de episodios a simular` | Episodes to simulate | integer ≥ 1, default 3 |
| `¿Imprimir cada paso?` | Step-by-step simulation output | `s`, `n` |

The program then displays the generated world, the converged value function, the derived
policy, a transition analysis and a simulation summary.

## Reproducibility

Every program accepts an optional integer seed. Reusing the same seed and configuration
regenerates exactly the same environment. Search tie-breaking is deterministic, so search
traces are stable for a given world and configuration.

The environments remain stochastic where that is the point. In particular, episode outcomes
in the river MDP are sampled from the transition probabilities and will vary between
simulations unless the same random state is reproduced.

## Validation

A GitHub Actions workflow runs on every push and pull request. Across Python 3.11, 3.12 and
3.13 it:

1. Installs the declared dependency.
2. Byte-compiles all four modules.
3. Imports every module, verifying that the dependency graph is valid.
4. Solves a seeded river MDP end to end, covering world generation, Value Iteration and
   episode simulation, and fails the build on any non-zero exit code.

Beyond CI, the search and inference components were exercised interactively across multiple
seeds and all four search algorithms, in both manual and automatic modes.

## Design notes

- `kurtz.py` uses 1-indexed grid coordinates; `palacio.py` and `river.py` use 0-indexed
  internal coordinates. Terminal output is designed independently for each environment.
- ANSI colours improve readability but never affect the algorithms. They can be switched off
  by setting `USE_COLOR = False` in `kurtz_colors.py`.
- Each entry point reconfigures standard output to UTF-8 on start-up, so the board symbols
  survive being redirected to a file or piped into another program on Windows.
- With a discount factor of exactly `1.0`, Value Iteration may converge slowly or reach the
  configured iteration limit. The program reports this explicitly and returns the best value
  estimate obtained; `0.99` converges quickly and is numerically very close.
- The technical report refers to the river component as `river_mdp.py`. The submitted source
  file in this repository is named `river.py`; both names denote the same component.

## Limitations

- These are educational, interactive simulations rather than production applications.
- The interfaces are terminal-based and the prompts are in Spanish.
- Automatically generated worlds can require a user-authorised risk decision when the
  available evidence is insufficient to prove any route safe.
- There is no formal unit-test suite. Automated validation covers compilation, imports and
  an end-to-end MDP run; the interactive components were validated manually.

## Documentation

A detailed explanation of the world models, percepts, inference rules, search procedures,
Bayesian updates, risk calculations and MDP formulation is available in
[`FIA_Project_Report.pdf`](FIA_Project_Report.pdf) (Spanish).

## License

Released under the [MIT License](LICENSE).

This repository is coursework published as a portfolio piece. If you are currently taking
the same course, please use it as a reference rather than as a submission.

## Author

**Rodrigo Alejandro Sicilia Maroto**  
Mathematical Engineering and Artificial Intelligence  
ICAI – Universidad Pontificia Comillas
