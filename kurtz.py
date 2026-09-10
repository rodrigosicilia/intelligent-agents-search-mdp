import random
import sys

import kurtz_colors as kc
#Buscando al Coronel Kurtz (Parte 1) - FIA

DIRS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}

KEY_TO_DIR = {"w": "U", "s": "D", "a": "L", "d": "R"}
DIR_TO_KEY = {"U": "w", "D": "s", "L": "a", "R": "d"}
DIR_ARROW = {"U": "↑", "D": "↓", "L": "←", "R": "→"}

#Politica:orden de insercion en frontera global (solo cuando son seguras)
#Primero derecha,luego abajo,luego izquierda y finalmente arriba
FRONTIER_DIR_ORDER = ("R","D","L","U")


def _fmt_cells_list(cells):
    """Formatea una colección de celdas como { (r,c), (r,c), ... } en el orden dado.

    Ojo:
        - Si pasas una lista, se respeta el orden (útil para ver el desempate por inserción).
        - Si pasas un set, el orden no está garantizado.

    Args:
        cells (iterable[tuple[int,int]]): Celdas.

    Returns:
        str: Representación tipo conjunto, pero con el orden que llega.
    """
    cells_list = list(cells)
    return "{" + ",".join(str(p) for p in cells_list) + "}"

def _fmt_cells_with_vals(cells, val_of):
    """
    Formatea una lista de celdas mostrando un valor asociado.

    El formato es: {(r,c)(v),(r,c)(v),...} respetando el orden de `cells`.

    Args:
        cells (list[tuple[int, int]]): Lista de celdas a mostrar.
        val_of (callable): Función val_of(celda) -> valor a imprimir.

    Returns:
        str: Cadena formateada.
    """
    return "{" + ",".join(f"{p}({val_of(p)})" for p in cells) + "}"


def _fmt_frontier_tuples(frontier, val_index=0, cell_index=-1):
    """
    Formatea una frontera representada como lista de tuplas.

    Útil para GBFS/A*, donde la frontera suele ser una lista con tuplas del estilo:
    (valor, stamp, celda). Los índices se pueden ajustar con `val_index` y `cell_index`.

    Args:
        frontier (list[tuple]): Lista de tuplas en frontera.
        val_index (int): Índice de la tupla que contiene el valor a mostrar.
        cell_index (int): Índice de la tupla que contiene la celda.

    Returns:
        str: Cadena formateada.
    """
    return "{" + ",".join(f"{item[cell_index]}({item[val_index]})" for item in frontier) + "}"


def get_single_element(container):
    """Devuelve el único elemento de un contenedor iterable (p.ej. set) SIN usar next/iter.

    Se usa solo cuando sabemos que el contenedor tiene exactamente 1 elemento.

    Args:
        container (iterable):Contenedor iterable (normalmente set) con exactamente 1 elemento.

    Returns:
        object|None:El único elemento, o None si el contenedor está vacío.
    """
    elem = None
    for x in container:
        elem = x
        break
    return elem


def in_bounds(n, pos):
    """Comprueba si una celda está dentro del tablero n×n (1-indexado).

    Args:
        n (int):Tamaño del tablero (n>=1).
        pos (tuple[int,int]):Celda (fila,col) con índices 1..n.

    Returns:
        bool:True si 1<=fila<=n y 1<=col<=n; False en caso contrario.
    """
    r, c = pos
    return 1 <= r <= n and 1 <= c <= n


def move_pos(pos, d):
    """Devuelve la celda resultante de aplicar un movimiento ortogonal.

    Nota:Esta función NO comprueba límites; para eso usa in_bounds().

    Args:
        pos (tuple[int,int]):Celda actual (fila,col), 1-indexada.
        d (str):Dirección en {"U","D","L","R"}.

    Returns:
        tuple[int,int]:Nueva celda tras aplicar DIRS[d].
    """
    dr, dc = DIRS[d]
    return (pos[0] + dr, pos[1] + dc)


def neighbors4(n, pos):
    """Lista los vecinos 4-conexos válidos dentro del tablero.

    Vecinos 4-conexos:arriba, abajo, izquierda, derecha (distancia Manhattan 1).

    Args:
        n (int):Tamaño del tablero.
        pos (tuple[int,int]):Celda (fila,col).

    Returns:
        list[tuple[int,int]]:Lista de celdas vecinas dentro del tablero.
    """
    r, c = pos
    cand = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    res = []
    for q in cand:
        if in_bounds(n, q):
            res.append(q)
    return res


def neighbors4_dir_order(n, pos, dir_order):
    """Vecinos 4-conexos en un orden de direcciones específico.

    Esto se usa para que los empates sean deterministas.

    Args:
        n (int):Tamaño del tablero.
        pos (tuple[int,int]):Celda (fila,col).
        dir_order (tuple[str,...]):Orden de direcciones, p.ej.("R","D","L","U").

    Returns:
        list[tuple[int,int]]:Vecinos válidos en el orden indicado.
    """
    out = []
    for d in dir_order:
        q = move_pos(pos, d)
        if in_bounds(n, q):
            out.append(q)
    return out


def all_cells(n):
    """Genera la lista de todas las celdas del tablero n×n.

    Args:
        n (int):Tamaño del tablero.

    Returns:
        list[tuple[int,int]]:Lista [(1,1),(1,2),...,(n,n)].
    """
    cells = []
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            cells.append((r, c))
    return cells


def manhattan(a, b):
    """Distancia Manhattan entre dos celdas.

    Esta distancia se usa como heurística en GBFS y A*:
    -En rejilla 4-conexa con coste 1 por paso, h(n)=|dr|+|dc|.
    -Es admisible (no sobreestima) y consistente.

    Args:
        a (tuple[int,int]):Celda (fila,col).
        b (tuple[int,int]):Celda (fila,col).

    Returns:
        int:|a.fila-b.fila|+|a.col-b.col|.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


#Mundo real

def make_world(n: int = 6) -> dict:
    """
    Crea y devuelve el estado real del mundo (palacio).

    Se crea un tablero n×n con coordenadas 1-indexadas, y se inicializa el estado dinámico:
    posición del agente, estado de vida, si Kurtz ha sido rescatado, etc.

    Args:
        n (int): Tamaño del tablero (n x n). Debe cumplir n >= 3.

    Returns:
        dict: Diccionario con el estado del mundo (incluye mapa oculto y estado del agente).

    Raises:
        ValueError: Si n < 3 (no hay celdas suficientes para colocar todos los elementos).
    """
    if n < 3:
        raise ValueError(
            f"n={n} inválido: se requiere n>=3 (n*n>=7) para colocar start + 3 pits + soldado + salida + Kurtz."
        )

    start = (1, 1)

    return {
        "n": n,
        "start": start,

        "pits": set(),
        "soldier": None,
        "exit": None,
        "kurtz": None,

        "agent": start,
        "alive": True,
        "kurtz_found": False,

        "grenade": True,
        "soldier_alive": True,
        "last_scream": False,

        "exit_seen": False,
    }

def reset_world(world: dict, seed: int | None = None) -> None:
    """
    Genera un mapa aleatorio cumpliendo las restricciones del enunciado.

    Coloca exactamente:
      - 3 precipicios
      - 1 soldado
      - 1 salida
      - 1 Kurtz
    en celdas todas distintas y distintas de world["start"].

    Modifica el diccionario `world` in-place, sobrescribiendo las claves: "pits", "soldier",
    "exit" y "kurtz".

    Args:
        world (dict): Mundo real (debe contener "n" y "start").
        seed (int | None): Semilla opcional para fijar la aleatoriedad.

    Returns:
        None
    """
    if seed is not None:
        random.seed(seed)

    n = world["n"]
    start = world["start"]

    available = [
        (r, c)
        for r in range(1, n + 1)
        for c in range(1, n + 1)
        if (r, c) != start
    ]
    picks = random.sample(available, 6)  #3 pits + soldado + salida + kurtz

    world["pits"] = set(picks[:3])
    world["soldier"] = picks[3]
    world["exit"] = picks[4]
    world["kurtz"] = picks[5]


def percept(world):
    """Devuelve el percepto del agente en su celda actual.

    Percepto (lista de booleanos):
    [Brisa, Ronquido, Resplandor, Pared↑, Pared↓, Pared←, Pared→, Grito]

    Brisa:True si hay algún precipicio en una celda adyacente.
    Ronquido:True si el soldado está vivo y está en una celda adyacente.
    Resplandor:True si la salida está en la celda actual o en una celda adyacente.
    Pared*:True si en esa dirección hay borde del tablero.
    Grito:True solo en el turno posterior a matar al soldado con granada (se consume).

    Args:
        world (dict):Estado real del mundo.

    Returns:
        list[bool]:Lista de 8 booleanos.
    """
    n = world["n"]
    pos = world["agent"]
    adj = neighbors4(n, pos)

    breeze = False
    for q in adj:
        if q in world["pits"]:
            breeze = True
            break

    snore = False
    if world["soldier_alive"]:
        for q in adj:
            if q == world["soldier"]:
                snore = True
                break

    glow = False
    if pos == world["exit"]:
        glow = True
    else:
        for q in adj:
            if q == world["exit"]:
                glow = True
                break

    r, c = pos
    wall_up = (r == 1)
    wall_down = (r == n)
    wall_left = (c == 1)
    wall_right = (c == n)

    scream = world["last_scream"]
    world["last_scream"] = False

    return [breeze, snore, glow, wall_up, wall_down, wall_left, wall_right, scream]

def percept_at(world: dict, pos: tuple[int, int]) -> list[bool]:
    """
    Calcula el percepto (vector de 8 booleanos) en una celda.

    Orden exacto del percepto:
        0) Brisa         -> hay un precipicio en una celda adyacente (Manhattan 1)
        1) Ronquido      -> soldado vivo está en una celda adyacente
        2) Resplandor    -> la salida está en una celda adyacente y sigue vivo
        3) Pared arriba  -> borde superior del tablero
        4) Pared abajo   -> borde inferior del tablero
        5) Pared izq.    -> borde izquierdo del tablero
        6) Pared dcha.   -> borde derecho del tablero
        7) Grito         -> True solo en el percepto inmediatamente posterior a lanzar granada

    Args:
        world (dict): Mundo real (incluye posiciones de pits/soldado/salida/Kurtz y estado).
        pos (tuple[int, int]): Celda (fila, columna) 1-indexada.

    Returns:
        list[bool]: Lista de 8 booleanos en el orden descrito.
    """
    n = world["n"]
    adj = neighbors4(n, pos)

    breeze = False
    for q in adj:
        if q in world["pits"]:
            breeze = True
            break

    snore = False
    if world["soldier_alive"]:
        for q in adj:
            if q == world["soldier"]:
                snore = True
                break

    glow = False
    if pos == world["exit"]:
        glow = True
    else:
        for q in adj:
            if q == world["exit"]:
                glow = True
                break

    r, c = pos
    wall_up = (r == 1)
    wall_down = (r == n)
    wall_left = (c == 1)
    wall_right = (c == n)

    scream = False  #en planificación no hay lanzamiento real de granada
    return [breeze, snore, glow, wall_up, wall_down, wall_left, wall_right, scream]


def plan_path_virtual_kb(
    world: dict,
    kb: dict,
    start: tuple[int, int],
    method: str,
    goal_test,
    heuristic=None,
    trace: bool = False,
    trace_prefix: str = "[Plan]",
):
    """
    Planifica un camino haciendo "visita virtual" y actualizando la KB.

    Este planificador NO mueve al agente real. En su lugar:
    - Extrae nodos de una frontera (según el algoritmo elegido).
    - Al extraer un nodo `u`, consulta el percepto real en `u` y actualiza `kb`.
    - Solo expande vecinos que la KB pueda demostrar como seguros (is_safe()).

    Args:
        world (dict): Mundo real (se usa para obtener perceptos durante la planificación).
        kb (dict): Base de conocimiento. Se actualiza durante la planificación.
        start (tuple[int, int]): Celda inicial.
        method (str): Algoritmo de búsqueda: "bfs", "dfs", "gbfs" o "astar".
        goal_test (callable): Función goal_test(pos) -> bool para comprobar objetivo.
        heuristic (callable | None): Función h(pos) -> número (solo para gbfs/astar).
        trace (bool): Si True, imprime una traza de la planificación.
        trace_prefix (str): Prefijo para las líneas de traza.

    Returns:
        list[tuple[int, int]] | None: Camino start->goal si se encuentra, o None si no hay solución.

    Raises:
        ValueError: Si `method` no está soportado.
    """
    method = method.lower()
    n = kb["n"]

    def safe_neighbors(pos):
        out = []
        for q in neighbors4_dir_order(n, pos, FRONTIER_DIR_ORDER):
            if is_safe(kb, q):
                out.append(q)
        return out

    #---------------- BFS ----------------
    if method == "bfs":
        q = [start]
        qi = 0
        seen = {start}
        parent = {}
        g = {start: 0}
        explored_order = []
        step_k = 0

        while qi < len(q):
            frontier_before = q[qi:]
            u = q[qi]
            qi += 1
            explored_order.append(u)

            if trace:
                frontier_str = _fmt_cells_list(frontier_before)
                removed_str = f"{u}"
                explored_str = _fmt_cells_list(explored_order)
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1


            #"Visita virtual": consultamos percepto y actualizamos KB
            per_u = percept_at(world, u)
            update_kb(kb, u, per_u, soldier_alive=world["soldier_alive"])

            if goal_test(u):
                return reconstruct_path(parent, start, u)

            for v in safe_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    g[v] = g[u] + 1
                    q.append(v)

        return None

    #---------------- DFS ----------------
    if method == "dfs":
        stack = [start]
        seen = {start}
        parent = {}
        g = {start: 0}
        explored_order = []
        step_k = 0

        while stack:
            frontier_before = list(stack)
            u = stack.pop()
            explored_order.append(u)

            if trace:
                frontier_str = _fmt_cells_list(frontier_before)
                removed_str = f"{u}"
                explored_str = _fmt_cells_list(explored_order)
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            per_u = percept_at(world, u)
            update_kb(kb, u, per_u, soldier_alive=world["soldier_alive"])

            if goal_test(u):
                return reconstruct_path(parent, start, u)

            for v in safe_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    g[v] = g[u] + 1
                    stack.append(v)

        return None

    #---------------- GBFS ----------------
    if method == "gbfs":
        if heuristic is None:
            heuristic = (lambda _p: 0)

        frontier = []
        counter = 0
        seen = {start}
        parent = {}
        explored_order = []
        step_k = 0

        frontier.append((heuristic(start), counter, start))

        while frontier:
            frontier_before = list(frontier)

            best_i = 0
            for i in range(1, len(frontier)):
                if frontier[i] < frontier[best_i]:
                    best_i = i

            h_u, _, u = frontier.pop(best_i)
            explored_order.append(u)

            if trace:
                frontier_str = _fmt_frontier_tuples(frontier_before, val_index=0, cell_index=-1)
                removed_str = f"{u}({h_u})"
                explored_str = _fmt_cells_with_vals(explored_order, lambda p: heuristic(p))
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            per_u = percept_at(world, u)
            update_kb(kb, u, per_u, soldier_alive=world["soldier_alive"])

            if goal_test(u):
                return reconstruct_path(parent, start, u)

            for v in safe_neighbors(u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    counter += 1
                    frontier.append((heuristic(v), counter, v))

        return None

    #---------------- A* ----------------
    if method == "astar":
        if heuristic is None:
            heuristic = (lambda _p: 0)

        frontier = []
        counter = 0
        parent = {}
        best_g = {start: 0}
        closed = set()
        explored_order = []
        step_k = 0

        frontier.append((best_g[start] + heuristic(start), counter, start))

        while frontier:
            frontier_before = list(frontier)

            best_i = 0
            for i in range(1, len(frontier)):
                if frontier[i] < frontier[best_i]:
                    best_i = i

            f_u, _, u = frontier.pop(best_i)
            if u in closed:
                continue

            closed.add(u)
            explored_order.append(u)

            if trace:
                frontier_str = _fmt_frontier_tuples(frontier_before, val_index=0, cell_index=-1)
                removed_str = f"{u}({f_u})"
                explored_str = _fmt_cells_with_vals(
                    explored_order,
                    lambda p: (best_g.get(p, 0) + heuristic(p)),
                )
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            per_u = percept_at(world, u)
            update_kb(kb, u, per_u, soldier_alive=world["soldier_alive"])

            if goal_test(u):
                return reconstruct_path(parent, start, u)

            gu = best_g[u]
            for v in safe_neighbors(u):
                if v in closed:
                    continue
                gv = gu + 1
                if gv < best_g.get(v, 10**9):
                    best_g[v] = gv
                    parent[v] = u
                    counter += 1
                    frontier.append((gv + heuristic(v), counter, v))

        return None

    raise ValueError("Método no soportado:" + str(method))


def step_move(world, d):
    """Ejecuta la acción MOVER y actualiza el mundo.

    Args:
        world (dict):Estado real del mundo (se modifica in-place).
        d (str):Dirección en {"U","D","L","R"}.

    Returns:
        None
    """
    if not world["alive"]:
        return

    nxt = move_pos(world["agent"], d)
    if not in_bounds(world["n"], nxt):
        return

    world["agent"] = nxt

    #Encuentra a Kurtz
    if world["agent"] == world["kurtz"]:
        world["kurtz_found"] = True

    #Si Kurtz fue encontrado, viaja con el agente
    if world["kurtz_found"]:
        world["kurtz"] = world["agent"]

    #Marca de interfaz:la salida queda "vista" si el agente pisa la salida real
    if world["agent"] == world["exit"]:
        world["exit_seen"] = True

    #Muerte por precipicio
    if world["agent"] in world["pits"]:
        world["alive"] = False
        return

    #Muerte por soldado (si sigue vivo)
    if world["soldier_alive"] and world["agent"] == world["soldier"]:
        world["alive"] = False
        return


def step_grenade(world, d):
    """
    Ejecuta la acción GRANADA (un solo uso) hacia una celda ortogonal.

    Efectos:
    - Consume la granada (no se puede volver a lanzar).
    - Si el soldado está en la celda objetivo y sigue vivo, lo elimina.
    - Activa world["last_scream"]=True para que en el SIGUIENTE percepto aparezca Grito=True.
    - No marca la celda objetivo como visitada/segura; sigue siendo no explorada.

    Args:
        world (dict): Estado real del mundo (se modifica in-place).
        d (str): Dirección en {"U","D","L","R"}.

    Returns:
        bool: True si mata al soldado; False en caso contrario.
    """
    if not world["alive"]:
        return False
    if not world["grenade"]:
        return False

    tgt = move_pos(world["agent"], d)
    if not in_bounds(world["n"], tgt):
        return False

    world["grenade"] = False

    if world["soldier_alive"] and tgt == world["soldier"]:
        world["soldier_alive"] = False
        world["last_scream"] = True
        return True

    return False


def step_exit(world):
    """Ejecuta la acción SALIR.

    Args:
        world (dict):Estado real del mundo.

    Returns:
        bool:True si se completa la misión (en la salida y con Kurtz); False en caso contrario.
    """
    if not world["alive"]:
        return False
    if world["agent"] != world["exit"]:
        return False
    return world["kurtz_found"]


#KB e inferencia

def make_kb(n, start):
    """Crea la base de conocimiento (KB) del agente.

    La KB guarda solo lo que el agente ha aprendido por perceptos (y acciones, como granada).
    No contiene información "mágica" del mundo real.

    Campos importantes:
    - visited: celdas pisadas físicamente.
    - *_obs: observaciones de perceptos en celdas visitadas.
    - pit_worlds: modelos de 3 precipicios compatibles con brisas observadas.
    - soldier_cand / exit_cand: candidatos compatibles con ronquido / resplandor.
    - soldier_forbidden: celdas donde sabemos que NO está el soldado (por ejemplo, porque
      se lanzó una granada ahí y no se le mató).

    Args:
        n (int): Tamaño del tablero.
        start (tuple[int,int]): Celda inicial del agente.

    Returns:
        dict: Estructura de KB.
    """
    return {
        "n": n,
        "start": start,

        "visited": set(),

        "breeze_obs": {},
        "snore_obs": {},
        "glow_obs": {},

        "soldier_alive": True,

        #Cuando un candidato se reduce a 1, lo guardamos aquí (mejora de claridad y consistencia).
        "soldier_known": None,
        "exit_known": None,

        "pit_worlds": [],

        "soldier_cand": set(),
        "exit_cand": set(),

        #Conocimiento negativo explícito sobre el soldado (útil tras granada fallida).
        "soldier_forbidden": set(),
    }


def update_kb(kb, pos, per, soldier_alive):
    """Actualiza la KB con un percepto observado y recalcula inferencias.

    Args:
        kb (dict):Base de conocimiento (se modifica in-place).
        pos (tuple[int,int]):Celda en la que se observa el percepto.
        per (list[bool]):Percepto completo (lista de 8 booleanos).
        soldier_alive (bool):Estado real del soldado.

    Returns:
        None
    """
    kb["visited"].add(pos)
    kb["breeze_obs"][pos] = bool(per[0])
    kb["snore_obs"][pos] = bool(per[1])
    kb["glow_obs"][pos] = bool(per[2])
    kb["soldier_alive"] = bool(soldier_alive)
    infer_all(kb)


def infer_all(kb):
    """Recalcula todas las inferencias (pits, soldado, salida).

    Importante:
        - Hay dependencias cruzadas: si deducimos la posición del soldado o de la salida con certeza,
          esa celda NO puede ser un precipicio (ni el soldado/salida pueden coincidir con un precipicio).
        - Para que esa coherencia se refleje en el mismo turno, iteramos un par de veces hasta estabilizar.

    Args:
        kb (dict):KB a actualizar.

    Returns:
        None
    """
    #Pequeño punto fijo (máx. 3 iteraciones) para propagar restricciones.
    for _ in range(3):
        prev = (
            kb.get("soldier_known"),
            kb.get("exit_known"),
            frozenset(kb.get("soldier_cand", set())),
            frozenset(kb.get("exit_cand", set())),
            len(kb.get("pit_worlds", [])),
        )

        infer_pits(kb)
        infer_soldier(kb)
        infer_exit(kb)

        cur = (
            kb.get("soldier_known"),
            kb.get("exit_known"),
            frozenset(kb.get("soldier_cand", set())),
            frozenset(kb.get("exit_cand", set())),
            len(kb.get("pit_worlds", [])),
        )
        if cur == prev:
            break


def infer_pits(kb):
    """Deduce modelos consistentes de precipicios (exactamente 3) por enumeración.

    A partir de las observaciones Brisa=True/False, enumeramos todas las combinaciones
    de 3 celdas (no visitadas) que no contradicen lo observado.

    Args:
        kb (dict):KB (lee visited/breeze_obs y escribe pit_worlds).

    Returns:
        None
    """
    n = kb["n"]
    visited = set(kb["visited"])

    ruled_out = set()
    must_cover = []

    for v, b in kb["breeze_obs"].items():
        adj = set(neighbors4(n, v))
        if b:
            must_cover.append(adj)
        else:
            ruled_out |= adj

    #Por reglas del mundo: ni el soldado ni la salida pueden coincidir con un precipicio.
    forbidden_cells = set()
    if kb.get("soldier_known") is not None:
        forbidden_cells.add(kb["soldier_known"])
    if kb.get("exit_known") is not None:
        forbidden_cells.add(kb["exit_known"])

    candidates = []
    for p in all_cells(n):
        if (p not in visited) and (p not in ruled_out) and (p not in forbidden_cells):
            candidates.append(p)

    worlds = []
    L = len(candidates)

    for i in range(L - 2):
        for j in range(i + 1, L - 1):
            for k in range(j + 1, L):
                pits = {candidates[i], candidates[j], candidates[k]}

                ok = True
                for adj in must_cover:
                    if len(pits & adj) == 0:
                        ok = False
                        break
                if not ok:
                    continue

                for v, b in kb["breeze_obs"].items():
                    if not b:
                        if len(pits & set(neighbors4(n, v))) > 0:
                            ok = False
                            break
                if not ok:
                    continue

                worlds.append(pits)

    kb["pit_worlds"] = worlds


def pit_may(kb):
    """Celdas que pueden ser precipicio (aparecen en al menos un mundo consistente).

    Args:
        kb (dict):KB.

    Returns:
        set[tuple[int,int]]:Unión de pits en todos los mundos.
    """
    u = set()
    for w in kb["pit_worlds"]:
        for p in w:
            u.add(p)
    return u


def pit_must(kb):
    """Celdas que son precipicio seguro (aparecen en todos los mundos consistentes).

    Args:
        kb (dict):KB.

    Returns:
        set[tuple[int,int]]:Intersección de pits en todos los mundos; vacío si no hay mundos.
    """
    worlds = kb["pit_worlds"]
    if not worlds:
        return set()

    inter = set()
    first = True
    for w in worlds:
        if first:
            inter = set(w)
            first = False
        else:
            inter &= set(w)
    return inter


def is_pit_safe(kb, p):
    """Comprueba si una celda es segura respecto a precipicios con certeza.

    Args:
        kb (dict):KB.
        p (tuple[int,int]):Celda.

    Returns:
        bool:True si p no aparece en ningún mundo; False si aparece en alguno o si no hay mundos.
    """
    worlds = kb["pit_worlds"]
    if not worlds:
        return False
    for w in worlds:
        if p in w:
            return False
    return True


def infer_soldier(kb):
    """Deduce candidatos del soldado consistentes con ronquidos (si está vivo).

    Además de las restricciones por perceptos, aplicamos conocimiento negativo acumulado:
    - Si el agente lanza una granada a una celda y NO mata al soldado (y el soldado sigue vivo),
      entonces sabemos con certeza que el soldado NO estaba en esa celda.

    Args:
        kb (dict): KB (escribe soldier_cand y soldier_known).

    Returns:
        None
    """
    if not kb["soldier_alive"]:
        kb["soldier_cand"] = set()
        kb["soldier_known"] = None
        return

    n = kb["n"]
    visited = set(kb["visited"])

    candidates = set(all_cells(n))

    #El soldado nunca está en una celda ya visitada (si lo pisas, mueres; y aquí asumimos agente vivo)
    for v in visited:
        candidates.discard(v)

    #No puede coincidir con un precipicio seguro
    pm = pit_must(kb)
    for p in pm:
        candidates.discard(p)

    #La salida no puede coincidir con el soldado
    if kb.get("exit_known") is not None:
        candidates.discard(kb["exit_known"])

    #Restricciones por ronquido (snore_obs)
    forbidden = set()
    must_be_in = []

    for v, s in kb["snore_obs"].items():
        adj = set(neighbors4(n, v))
        if s:
            must_be_in.append(adj)
        else:
            forbidden |= adj

    candidates -= forbidden

    if must_be_in:
        inter = set(must_be_in[0])
        for st in must_be_in[1:]:
            inter &= st
        candidates &= inter

    #Conocimiento negativo adicional (por ejemplo, granada fallida)
    candidates -= set(kb.get("soldier_forbidden", set()))

    kb["soldier_cand"] = candidates

    #Si queda un único candidato, lo marcamos como conocido.
    if len(candidates) == 1:
        kb["soldier_known"] = get_single_element(candidates)
    elif kb.get("soldier_known") not in candidates:
        kb["soldier_known"] = None


def infer_exit(kb):
    """Deduce candidatos de salida consistentes con resplandor.

    Para cada observación Glow:
    -Glow=True en v => salida ∈ {v}∪N(v)
    -Glow=False en v => salida ∉ {v}∪N(v)

    Args:
        kb (dict):KB (escribe exit_cand).

    Returns:
        None
    """
    n = kb["n"]
    candidates = set(all_cells(n))

    pm = pit_must(kb)
    for p in pm:
        if p in candidates:
            candidates.remove(p)

    #El soldado (si se conoce con certeza) no puede coincidir con la salida
    if kb.get("soldier_known") is not None and kb["soldier_known"] in candidates:
        candidates.remove(kb["soldier_known"])

    for v, g in kb["glow_obs"].items():
        zone = set(neighbors4(n, v))
        zone.add(v)
        if g:
            candidates &= zone
        else:
            candidates -= zone

    kb["exit_cand"] = candidates

    #Si queda un único candidato, lo marcamos como conocido.
    if len(candidates) == 1:
        kb["exit_known"] = get_single_element(candidates)
    elif kb.get("exit_known") not in candidates:
        kb["exit_known"] = None


def soldier_may(kb):
    """
    Devuelve celdas donde el soldado PODRÍA estar (según la KB).

    Args:
        kb (dict): Base de conocimiento.

    Returns:
        set[tuple[int, int]]: Conjunto de candidatos posibles para el soldado (vacío si está muerto).
    """
    if not kb["soldier_alive"]:
        return set()
    return set(kb.get("soldier_cand", set()))


def soldier_must(kb):
    """
    Devuelve celdas donde el soldado ESTÁ con certeza (según la KB).

    Si solo queda un candidato, esa celda es 'must'. Si hay 0 o >1 candidatos, no hay certeza.

    Args:
        kb (dict): Base de conocimiento.

    Returns:
        set[tuple[int, int]]: Conjunto con 1 celda si está deducido, o vacío si no.
    """
    if not kb["soldier_alive"]:
        return set()
    cand = kb.get("soldier_cand", set())
    if len(cand) == 1:
        return set(cand)
    return set()


def exit_cand(kb):
    """
    Devuelve celdas donde la salida PODRÍA estar (según la KB).

    Args:
        kb (dict): Base de conocimiento.

    Returns:
        set[tuple[int, int]]: Conjunto de candidatos posibles para la salida.
    """
    return set(kb.get("exit_cand", set()))


def is_soldier_safe(kb, p):
    """Comprueba si una celda es segura respecto al soldado con certeza.

    Regla:
    - Si el soldado está muerto, todo es seguro respecto al soldado.
    - Si el soldado está vivo, una celda es segura solo si está descartada como candidata.

    Nota importante:
    - Si por alguna contradicción temporal la KB se queda sin candidatos (soldier_cand vacío
      pero soldier_alive=True), NO interpretamos eso como "todo es seguro"; al revés: significa
      que la deducción está incompleta/contradictoria, así que devolvemos False.

    Args:
        kb (dict): KB.
        p (tuple[int,int]): Celda.

    Returns:
        bool: True si seguro; False si podría estar el soldado ahí (o no hay certeza).
    """
    if not kb["soldier_alive"]:
        return True

    cand = kb.get("soldier_cand", set())
    if not cand:
        return False

    return p not in cand


def is_safe(kb, p):
    """Comprueba seguridad total de una celda (pits + soldado) con certeza.

    Args:
        kb (dict):KB.
        p (tuple[int,int]):Celda.

    Returns:
        bool:True si demostrablemente segura; False si no hay certeza o hay riesgo.
    """
    if p in kb["visited"]:
        return True
    return is_pit_safe(kb, p) and is_soldier_safe(kb, p)


def safe_cells(kb):
    """Devuelve el conjunto de celdas demostrablemente seguras.

    Args:
        kb (dict):KB.

    Returns:
        set[tuple[int,int]]:Celdas seguras.
    """
    n = kb["n"]
    res = set()
    for p in all_cells(n):
        if is_safe(kb, p):
            res.add(p)
    return res


#Etiquetas de celdas (según el enunciado)

def _has_breeze_evidence(kb, p):
    """Indica si hay evidencia local de pit para p (por alguna brisa observada).

    Args:
        kb (dict):KB.
        p (tuple[int,int]):Celda.

    Returns:
        bool:True si alguna brisa=True está en un vecino de p.
    """
    n = kb["n"]
    for v, b in kb["breeze_obs"].items():
        if b:
            for q in neighbors4(n, v):
                if q == p:
                    return True
    return False


def _has_snore_evidence(kb, p):
    """Indica si hay evidencia local de soldado para p (por algún ronquido observado).

    Args:
        kb (dict):KB.
        p (tuple[int,int]):Celda.

    Returns:
        bool:True si algún ronquido=True está en un vecino de p.
    """
    n = kb["n"]
    for v, s in kb["snore_obs"].items():
        if s:
            for q in neighbors4(n, v):
                if q == p:
                    return True
    return False


def _has_glow_true(kb):
    """Comprueba si alguna vez se observó resplandor=True.

    Args:
        kb (dict):KB.

    Returns:
        bool:True si existe algún glow_obs[v]==True.
    """
    for v in kb["glow_obs"]:
        if kb["glow_obs"][v]:
            return True
    return False


def cell_tag(kb, p):
    """Devuelve la etiqueta visible de una celda según la KB.

    La idea es separar claramente tres conceptos:

    - **Visitada**: ya hemos estado físicamente en esa celda.
    - **Segura deducida**: la KB demuestra que NO hay precipicio y NO hay soldado (si sigue vivo),
      aunque todavía no la hayamos visitado.
    - **Desconocida / peligrosa**: la KB no puede garantizar seguridad.

    Notación (alineada con el enunciado):
    - ``v``  : celda visitada
    - ``✓``  : celda segura deducida (no visitada)
    - ``.``  : celda desconocida
    - ``P?`` / ``P!`` : precipicio posible / seguro
    - ``S?`` / ``S!`` : soldado posible / seguro (solo si el soldado sigue vivo)
    - ``E?`` / ``E!`` : salida posible / segura (deducida)

    Args:
        kb (dict): Base de conocimiento.
        p (tuple[int,int]): Celda (fila, columna) 1-indexadas.

    Returns:
        str: Etiqueta corta para imprimir en el tablero.
    """
    if p in kb["visited"]:
        return "v"

    tags = []

    pmust = pit_must(kb)
    if p in pmust:
        tags.append("P!")
    else:
        pmay = pit_may(kb)
        if (p in pmay) and _has_breeze_evidence(kb, p):
            tags.append("P?")

    if kb["soldier_alive"]:
        smust = soldier_must(kb)
        if p in smust:
            tags.append("S!")
        else:
            smay = soldier_may(kb)
            if (p in smay) and _has_snore_evidence(kb, p):
                tags.append("S?")

    ec = exit_cand(kb)
    if len(ec) == 1 and p in ec:
        tags.append("E!")
    elif _has_glow_true(kb) and (p in ec):
        tags.append("E?")

    if not tags:
        return "✓" if is_safe(kb, p) else "."

    return "".join(tags)

#Visualización

def _stimulus_suffix(per, include_glow: bool = True):
    """Construye el subíndice de estímulos (B,R,E) a partir del percepto.

    Nota:
        - Usamos B,R,E como “marcas” en la celda del capitán para que se vea rápido
          qué se está percibiendo en ese turno.
        - Si include_glow=False, omitimos la E del resplandor (útil si ya pintamos una 'E'
          explícita porque estamos encima de la salida).

    Args:
        per (list[bool] | None): Percepto actual (o None).
        include_glow (bool): Si True añade 'E' cuando hay resplandor.

    Returns:
        str: Sufijo tipo "_BR", "_E", "_BRE" o "" si no hay estímulos.
    """
    if per is None:
        return ""

    marks = []
    if per[0]:
        marks.append("B")
    if per[1]:
        marks.append("R")
    if include_glow and per[2]:
        marks.append("E")

    if not marks:
        return ""
    return "_" + "".join(marks)
def _fmt_cell(s, w):
    """Formatea una celda a ancho fijo.

    Args:
        s (str):Texto de la celda.
        w (int):Ancho.

    Returns:
        str:Texto centrado y recortado a w.
    """
    if s is None:
        s = ""
    if len(s) > w:
        s = s[:w]
    return s.center(w)


def render(world, kb, per=None):
    """Imprime el tablero con la información del agente (KB).

    Notas:
    - La celda actual del capitán se imprime como "CW" con subíndices de estímulos recibidos.
    - Si Kurtz fue encontrado, se muestra "CWK" en la celda actual.
    - Si el capitán está encima de la salida, marcamos explícitamente "E" en la celda ("CWE"/"CWKE")
      para que se entienda rápido que puede intentar salir con la tecla 'x'.
    - Si la salida real fue pisada alguna vez, esa celda se marca como "E" de forma persistente
      (aunque el capitán ya no esté encima).

    Args:
        world (dict): Estado real (solo overlays de posición y marca de salida vista).
        kb (dict): Base de conocimiento.
        per (list[bool] | None): Percepto actual (para mostrar subíndices en la celda del capitán).

    Returns:
        None
    """
    n = world["n"]
    agent = world["agent"]
    on_exit = (agent == world["exit"])

    cell_w = 8

    print("\n=== PALACIO (conocimiento del agente) ===")
    print(
        "Leyenda: v visitada(verde) | ✓ segura no explorada(azul) | . desconocida | "
        "P?/S? posible peligro(naranja) | P!/S! peligro seguro(rojo) | E?/E! salida(amarillo)"
    )
    print("Nota: pueden combinarse en una celda, e.g. P?E? o P?S?E?")
    print("CW=Capitán Willard (subíndices: B=brisa, R=ronquido, E=resplandor)")
    print("Controles: w/a/s/d mover | g + (w/a/s/d) granada | x salir | q terminar")
    if world["exit_seen"]:
        print("        E=salida (pisada alguna vez)")
    print()

    header = " " * 6 + "".join(_fmt_cell(str(c), cell_w) for c in range(1, n + 1))
    print(header)
    print(" " * 6 + "-" * (cell_w * n))

    for r in range(1, n + 1):
        row = []
        for c in range(1, n + 1):
            p = (r, c)
            base = cell_tag(kb, p)

            #Si hemos pisado la salida en algún momento, la dejamos marcada como E
            #(pero si estamos encima, lo gestionamos abajo con el overlay "CW...").
            if world["exit_seen"] and p == world["exit"] and p != agent:
                base = "E!" if kb.get("exit_known") == p else "E"

            #Overlay del capitán
            if p == agent:
                label = "CW"
                if world["kurtz_found"]:
                    label += "K"
                if on_exit:
                    label += "E"  #Marca explícita de "estás en la salida"
                #Si ya marcamos 'E' explícita por estar encima, evitamos duplicarla en el sufijo
                label += _stimulus_suffix(per, include_glow=not on_exit)
                base = label

            padded = _fmt_cell(base, cell_w)
            padded = kc.colorize_cell(padded, base)
            row.append(padded)

        print(f"{r:>3d} | " + "".join(row))

    print(
        f"\nEstado: pos={world['agent']} | vivo={world['alive']} | Kurtz={world['kurtz_found']} | "
        f"granada={'sí' if world['grenade'] else 'no'} | soldado_vivo={world['soldier_alive']}"
    )
    if world["exit_seen"]:
        print("Salida pisada: sí")

    if on_exit:
        if world["kurtz_found"]:
            print(">>> Estás en la salida. Pulsa 'x' para SALIR y completar la misión.")
        else:
            print(">>> Estás en la salida. Podrás salir con 'x' cuando encuentres a Kurtz.")

    print(f"Soldado_candidatos: {sorted(kb['soldier_cand']) if world['soldier_alive'] else '— (muerto)'}")
    print(f"Salida_candidatos : {sorted(kb['exit_cand']) if kb['exit_cand'] else '—'}")

def print_percept(per):
    """
    Imprime el percepto en el orden exacto del enunciado.

    El vector (8 booleanos) se interpreta así:
    1) Brisa
    2) Ronquido
    3) Resplandor
    4) Pared arriba (^)
    5) Pared abajo (v)
    6) Pared izquierda (<)
    7) Pared derecha (>)
    8) Grito

    Args:
        per (list[bool]): Vector de 8 booleanos.

    Returns:
        None
    """
    parts = [
        ("Brisa", per[0]),
        ("Ronquido", per[1]),
        ("Resplandor", per[2]),
        ("Pared_arriba(^)", per[3]),
        ("Pared_abajo(v)", per[4]),
        ("Pared_izq(<)", per[5]),
        ("Pared_dcha(>)", per[6]),
        ("Grito", per[7]),
    ]
    txt = ", ".join(f"{lab}={'1' if v else '0'}" for lab, v in parts)
    print("Percepto:[" + txt + "]")


def recommend(kb):
    """
    En modo manual, muestra celdas no visitadas que la KB demuestra seguras.

    Es una ayuda de interfaz para el jugador: lista celdas que la KB considera seguras y
    todavía no han sido exploradas.

    Args:
        kb (dict): Base de conocimiento.

    Returns:
        None
    """
    n = kb["n"]

    #Recorremos el tablero en orden natural (fila a fila) para que la salida sea siempre igual
    safe_unvisited = []
    for p in all_cells(n):
        if (p not in kb["visited"]) and is_safe(kb, p):
            safe_unvisited.append(p)

    if not safe_unvisited:
        print("Recomendación:ninguna celda no explorada es demostrablemente segura con la info actual.")
        return

    print("Recomendación:celdas seguras no exploradas:" + ", ".join(str(p) for p in safe_unvisited))


#Búsqueda sobre celdas seguras

def neighbors_allowed(n, allowed, pos):
    """Vecinos 4-conexos de pos restringidos al conjunto allowed.

    Nota:
        Usamos un orden fijo R, D, L, U para que BFS/DFS/GBFS/A* sean deterministas en empates.

    Args:
        n (int):Tamaño del tablero.
        allowed (set[tuple[int,int]]):Celdas transitables.
        pos (tuple[int,int]):Celda origen.

    Returns:
        list[tuple[int,int]]:Vecinos dentro de allowed.
    """
    res = []
    for q in neighbors4_dir_order(n, pos, FRONTIER_DIR_ORDER):
        if q in allowed:
            res.append(q)
    return res

def reconstruct_path(parent, start, goal):
    """Reconstruye un camino start->goal usando parent[v]=u.

    Args:
        parent (dict[tuple[int,int],tuple[int,int]]):Mapa de predecesores.
        start (tuple[int,int]):Origen.
        goal (tuple[int,int]):Destino.

    Returns:
        list[tuple[int,int]]|None:Camino o None si no existe.
    """
    if goal == start:
        return [start]
    if goal not in parent:
        return None

    path = [goal]
    cur = goal
    while cur != start:
        cur = parent[cur]
        path.append(cur)
    path.reverse()
    return path


def plan_path_allowed(
    n,
    start,
    goal,
    allowed,
    method,
    heuristic_goal=None,
    trace=False,
    trace_prefix="[Plan]",
):
    """
    Planifica un camino start->goal restringido al conjunto `allowed`.

    Esta función implementa BFS/DFS/GBFS/A* sobre una rejilla 4-conexa y coste unitario,
    pero SOLO permite transitar por celdas que estén en `allowed` (incluyendo start y goal).

    Si `trace=True`, imprime una traza por extracción (expansión) con:
        Step k | Frontier=... | Removed=... | Explored=...

    Notas sobre desempates:
    - BFS/DFS: se resuelven por orden FIFO/LIFO y por el orden de vecinos configurado.
    - GBFS/A*: se desempata por (valor, orden_de_inserción) usando un contador incremental.

    Args:
        n (int): Tamaño del tablero.
        start (tuple[int, int]): Celda inicial.
        goal (tuple[int, int]): Celda objetivo.
        allowed (set[tuple[int, int]]): Conjunto de celdas permitidas.
        method (str): Algoritmo de búsqueda: "bfs", "dfs", "gbfs" o "astar".
        heuristic_goal (tuple[int, int] | None): Heurística h(pos) (solo para gbfs/astar).
        trace (bool): Si True, imprime la traza.
        trace_prefix (str): Prefijo para la traza.

    Returns:
        list[tuple[int, int]] | None: Camino start->goal si se encuentra, o None si no hay solución.

    Raises:
        ValueError: Si `method` no está soportado.
    """
    method = method.lower()

    if start not in allowed or goal not in allowed:
        return None

    hg = heuristic_goal
    parent = {}
    explored_order = []
    step_k = 0

    #---------------- BFS ----------------
    if method == "bfs":
        q = [start]
        qi = 0
        seen = {start}

        while qi < len(q):
            #Frontier ANTES de extraer
            frontier_before = q[qi:]
            u = q[qi]
            qi += 1

            explored_order.append(u)

            if trace:
                frontier_str = _fmt_cells_list(frontier_before)
                removed_str = str(u)
                explored_str = _fmt_cells_list(explored_order)
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if u == goal:
                break

            for v in neighbors_allowed(n, allowed, u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    q.append(v)

        return reconstruct_path(parent, start, goal)

    #---------------- DFS ----------------
    if method == "dfs":
        stack = [start]
        seen = {start}

        while stack:
            #Frontier ANTES de extraer (pila tal cual)
            frontier_before = list(stack)
            u = stack.pop()

            explored_order.append(u)

            if trace:
                frontier_str = _fmt_cells_list(frontier_before)
                removed_str = str(u)
                explored_str = _fmt_cells_list(explored_order)
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if u == goal:
                break

            for v in neighbors_allowed(n, allowed, u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    stack.append(v)

        return reconstruct_path(parent, start, goal)

    #---------------- GBFS ----------------
    if method == "gbfs":
        frontier = []
        counter = 0
        seen = {start}

        h0 = manhattan(start, hg) if hg is not None else 0
        frontier.append((h0, counter, start))

        while frontier:
            #Frontier ANTES de extraer
            frontier_before = list(frontier)

            best_i = 0
            for i in range(1, len(frontier)):
                if frontier[i] < frontier[best_i]:
                    best_i = i

            h_u, _, u = frontier.pop(best_i)
            explored_order.append(u)

            if trace:
                frontier_str = _fmt_frontier_tuples(frontier_before, val_index=0, cell_index=-1)
                removed_str = f"{u}({h_u})"
                explored_str = _fmt_cells_with_vals(explored_order, lambda p: (manhattan(p, hg) if hg is not None else 0))
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if u == goal:
                break

            for v in neighbors_allowed(n, allowed, u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    counter += 1
                    hv = manhattan(v, hg) if hg is not None else 0
                    frontier.append((hv, counter, v))

        return reconstruct_path(parent, start, goal)

    #---------------- A* ----------------
    if method == "astar":
        frontier = []
        counter = 0
        best_g = {start: 0}
        closed = set()

        h0 = manhattan(start, hg) if hg is not None else 0
        frontier.append((h0, counter, start))

        while frontier:
            #Frontier ANTES de extraer
            frontier_before = list(frontier)

            best_i = 0
            for i in range(1, len(frontier)):
                if frontier[i] < frontier[best_i]:
                    best_i = i

            f_u, _, u = frontier.pop(best_i)
            if u in closed:
                continue

            closed.add(u)
            explored_order.append(u)

            if trace:
                frontier_str = _fmt_frontier_tuples(frontier_before, val_index=0, cell_index=-1)
                removed_str = f"{u}({f_u})"
                explored_str = _fmt_cells_with_vals(
                    explored_order,
                    lambda p: (best_g.get(p, 0) + (manhattan(p, hg) if hg is not None else 0)),
                )
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if u == goal:
                break

            gu = best_g[u]
            for v in neighbors_allowed(n, allowed, u):
                if v in closed:
                    continue
                gv = gu + 1
                if gv < best_g.get(v, 10**9):
                    best_g[v] = gv
                    parent[v] = u
                    counter += 1
                    hv = manhattan(v, hg) if hg is not None else 0
                    frontier.append((gv + hv, counter, v))

        return reconstruct_path(parent, start, goal)

    raise ValueError("Método no soportado:" + str(method))


def plan_path(kb, start, goal, method, trace=False, trace_prefix="[Plan]"):
    """Planifica un camino start->goal usando solo celdas demostrablemente seguras.

    Esto usa plan_path_allowed(...) por debajo. Si trace=True, delega la traza del proceso
    de búsqueda (Explorados/Frontera/Extraído) en el planificador interno.

    Args:
        kb (dict): KB.
        start (tuple[int,int]): Origen.
        goal (tuple[int,int]): Destino.
        method (str): "bfs"|"dfs"|"gbfs"|"astar".
        trace (bool): Si True, imprime traza de la búsqueda interna.
        trace_prefix (str): Prefijo para las líneas de traza.

    Returns:
        list[tuple[int,int]]|None: Camino o None si no existe.
    """
    allowed = safe_cells(kb)
    allowed.add(start)
    n = kb["n"]
    if goal not in allowed:
        return None

    #Para planificar hacia una meta conocida, la heurística (si aplica) usa el propio goal.
    return plan_path_allowed(
        n,
        start,
        goal,
        allowed,
        method=method,
        heuristic_goal=goal,
        trace=trace,
        trace_prefix=trace_prefix,
    )


def path_to_actions(path):
    """Convierte un camino de celdas en acciones U/D/L/R.

    Args:
        path (list[tuple[int,int]]):Camino [p0,p1,...].

    Returns:
        list[str]:Acciones.
    """
    if not path or len(path) < 2:
        return []

    acts = []
    for a, b in zip(path, path[1:]):
        dr = b[0] - a[0]
        dc = b[1] - a[1]
        for d in DIRS:
            x, y = DIRS[d]
            if (dr, dc) == (x, y):
                acts.append(d)
                break
    return acts


def unvisited_neighbor_count(kb, pos):
    """Cuenta vecinos no visitados de pos.

    Args:
        kb (dict):KB.
        pos (tuple[int,int]):Celda.

    Returns:
        int:Conteo de vecinos no visitados.
    """
    n = kb["n"]
    visited = kb["visited"]
    cnt = 0
    for nb in neighbors4(n, pos):
        if nb not in visited:
            cnt += 1
    return cnt

#Modos de ejecución

def run_manual(world, kb):
    """Bucle del modo manual.

    Args:
        world (dict): Estado real.
        kb (dict): KB.

    Returns:
        None
    """
    print("\nModo MANUAL")
    print("Controles:")
    print("  - w/a/s/d : moverte")
    print("  - g       : lanzar granada (te pedirá dirección w/a/s/d)")
    print("  - x       : salir (solo funciona si estás en la salida)")
    print("  - q       : terminar partida\n")

    while True:
        if not world["alive"]:
            render(world, kb, per=None)
            print("\nHas muerto. Fin.")
            return

        per = percept(world)
        update_kb(kb, world["agent"], per, world["soldier_alive"])

        render(world, kb, per=per)
        print_percept(per)
        if per[7]:
            print("Se oye un grito a lo lejos.")
        recommend(kb)

        #Recordatorio explícito (para que se vea claro cuándo tocar 'x')
        if world["agent"] == world["exit"]:
            if world["kurtz_found"]:
                print(">>> Estás en la salida. Pulsa 'x' para SALIR.")
            else:
                print(">>> Estás en la salida, pero aún no llevas a Kurtz (todavía no puedes completar la misión).")

        cmd = input("\nComando> ").strip().lower()

        if cmd == "q":
            print("Saliendo.")
            return

        if cmd == "x":
            if step_exit(world):
                render(world, kb, per=None)
                print("\n¡Misión completada! Has salido con Kurtz.")
                return
            print("No se puede salir: tienes que estar EN la salida y haber encontrado a Kurtz.")
            continue

        if cmd == "g":
            if not world["grenade"]:
                print("No te queda granada.")
                continue

            dkey = input("Dirección granada (w/a/s/d)> ").strip().lower()
            if dkey not in KEY_TO_DIR:
                print("Dirección inválida.")
                continue

            d = KEY_TO_DIR[dkey]
            tgt = move_pos(world["agent"], d)
            killed = step_grenade(world, d)

            #Si no lo matamos y el soldado sigue vivo, sabemos que NO estaba en esa celda.
            #(La granada actúa como "prueba": si hubiera estado, lo habríamos matado.)
            if (not killed) and world["soldier_alive"] and in_bounds(world["n"], tgt):
                kb.setdefault("soldier_forbidden", set()).add(tgt)
                infer_all(kb)

            continue

        if cmd in KEY_TO_DIR:
            step_move(world, KEY_TO_DIR[cmd])
            continue

        print("Comando no reconocido.")


def clone_kb(kb):
    """
    Copia profunda mínima de la base de conocimiento (KB).

    Copia claves escalares y duplica las estructuras mutables (sets/dicts) necesarias para
    planificar sin modificar la KB original.

    Args:
        kb (dict): Base de conocimiento.

    Returns:
        dict: Copia independiente de `kb`.
    """
    kb2 = {
        "n": kb["n"],
        "start": kb["start"],
        "visited": set(kb.get("visited", set())),
        "breeze_obs": dict(kb.get("breeze_obs", {})),
        "snore_obs": dict(kb.get("snore_obs", {})),
        "glow_obs": dict(kb.get("glow_obs", {})),
        "soldier_alive": bool(kb.get("soldier_alive", True)),
        "soldier_known": kb.get("soldier_known", None),
        "exit_known": kb.get("exit_known", None),
        "pit_worlds": [set(w) for w in kb.get("pit_worlds", [])],
        "soldier_cand": set(kb.get("soldier_cand", set())),
        "exit_cand": set(kb.get("exit_cand", set())),
        "soldier_forbidden": set(kb.get("soldier_forbidden", set())),
    }
    return kb2


def _auto_goal_reached(pos, heuristic_fn):
    """
    Comprueba si se ha alcanzado el objetivo usando Manhattan.

    Se considera que se ha llegado al objetivo cuando la heurística Manhattan vale 0.

    Args:
        pos (tuple[int, int]): Celda actual.
        heuristic_fn (callable): Función h(pos) -> int (distancia Manhattan al objetivo).

    Returns:
        bool: True si heuristic_fn(pos) == 0; False en caso contrario.

    Raises:
        ValueError: Si `heuristic_fn` es None.
    """
    if heuristic_fn is None:
        raise ValueError("Falta heuristic_fn para comprobar llegada al objetivo (Manhattan).")
    return heuristic_fn(pos) == 0



def _auto_observe_if_needed(world, kb_plan, pos, observed):
    """
    Observa un percepto de planificación si todavía no se ha observado esa celda.

    En planificación, se permite consultar perceptos del mundo real únicamente para celdas que se
    extraen de la frontera (Removed / exploradas), sin mover al agente real.

    Args:
        world (dict): Mundo real.
        kb_plan (dict): KB de planificación (se actualiza con el percepto observado).
        pos (tuple[int, int]): Celda a observar.
        observed (set[tuple[int, int]]): Conjunto de celdas ya observadas en esta planificación.

    Returns:
        None
    """
    if pos in observed:
        return
    per = percept_at(world, pos)
    update_kb(kb_plan, pos, per, soldier_alive=world["soldier_alive"])
    observed.add(pos)

def _auto_boundary_risky_candidates(n, kb_plan, explored_set, frontier_nodes_set):
    """
    Devuelve las celdas candidatas de riesgo cuando no existen celdas
    demostrablemente seguras en la frontera.

    Una celda se considera candidata si:
    - Es vecina (4-direcciones) de alguna celda explorada.
    - No ha sido explorada previamente.
    - No pertenece ya a la frontera.
    - No es demostrablemente segura según la base de conocimiento.
    - Su etiqueta contiene '?' (riesgo incierto) y NO contiene '!' (muerte segura).

    Estas celdas representan decisiones potencialmente letales que pueden
    desbloquear nueva información durante la planificación.

    Parámetros
    ----------
    n : int
        Tamaño del mundo (n x n).
    kb_plan : KnowledgeBase
        Base de conocimiento usada durante la planificación.
    explored_set : set[tuple[int, int]]
        Conjunto de celdas ya exploradas.
    frontier_nodes_set : set[tuple[int, int]]
        Conjunto de celdas actualmente en la frontera.

    Retorna
    -------
    list[tuple[int, int]]
        Lista ordenada de celdas candidatas no seguras.
    """
    cand = set()
    for u in explored_set:
        for v in neighbors4_dir_order(n, u, FRONTIER_DIR_ORDER):
            if v in explored_set:
                continue
            if v in frontier_nodes_set:
                continue
            if is_safe(kb_plan, v):
                continue

            #Solo proponemos celdas con riesgo INCIERTO ('?') y descartamos
            #aquellas marcadas como muerte segura ('!').
            tag = cell_tag(kb_plan, v)
            if ("?" not in tag) or ("!" in tag):
                continue

            cand.add(v)

    return sorted(cand)

def _auto_pick_parent_for_candidate(n, v, explored_set, g_map=None, best_g=None):
    """
    Selecciona una celda explorada adyacente que pueda actuar como padre
    de una celda forzada (no segura), permitiendo reconstruir el camino.

    El criterio de selección prioriza:
    - Menor coste acumulado g (si está disponible).
    - Desempate determinista por coordenadas.

    Parámetros
    ----------
    n : int
        Tamaño del mundo (n x n).
    v : tuple[int, int]
        Celda candidata a expandir.
    explored_set : set[tuple[int, int]]
        Conjunto de celdas ya exploradas.
    g_map : dict[tuple[int, int], int], opcional
        Costes g para BFS/DFS.
    best_g : dict[tuple[int, int], int], opcional
        Costes g óptimos para A*.

    Retorna
    -------
    tuple[int, int] o None
        Celda padre seleccionada o None si no existe ninguna válida.
    """
    parents = []
    for u in neighbors4(n, v):
        if u in explored_set:
            if g_map is not None:
                parents.append((g_map.get(u, 10**9), u))
            elif best_g is not None:
                parents.append((best_g.get(u, 10**9), u))
            else:
                parents.append((0, u))

    if not parents:
        return None

    parents.sort(key=lambda x: (x[0], x[1][0], x[1][1]))
    return parents[0][1]

def _auto_ask_user_expand_risky(n, kb_plan, explored_set, frontier_nodes_set, trace_prefix="[Plan]"):
    """
    Solicita al usuario la expansión manual de una celda no segura cuando
    no existen celdas demostrablemente seguras en la frontera.

    Esta función informa explícitamente del riesgo asociado a la decisión:
    la celda elegida puede contener un peligro y provocar la muerte del
    agente durante la ejecución real, aunque permita avanzar en planificación.

    Parámetros
    ----------
    n : int
        Tamaño del mundo (n x n).
    kb_plan : KnowledgeBase
        Base de conocimiento usada durante la planificación.
    explored_set : set[tuple[int, int]]
        Conjunto de celdas ya exploradas.
    frontier_nodes_set : set[tuple[int, int]]
        Conjunto de celdas actualmente en la frontera.
    trace_prefix : str
        Prefijo usado para trazas y mensajes por pantalla.

    Retorna
    -------
    tuple[int, int] o None
        Celda seleccionada por el usuario o None si aborta la decisión.
    """
    candidates = _auto_boundary_risky_candidates(
        n, kb_plan, explored_set, frontier_nodes_set
    )

    if not candidates:
        return None

    print(f"\n{trace_prefix} AVISO: no quedan celdas demostrablemente seguras en la frontera.")
    print(f"{trace_prefix} Puedes forzar la expansión de una celda NO segura.")
    print(f"{trace_prefix} Esto puede provocar la muerte del agente en ejecución.\n")

    for i, p in enumerate(candidates, 1):
        print(f"  {i:>2d}) {p}   [{cell_tag(kb_plan, p)}]")

    while True:
        ans = input(
            f"\n{trace_prefix} Introduce un número (1-{len(candidates)}) o 'q' para abortar: "
        ).strip().lower()

        if ans == "q":
            return None

        try:
            k = int(ans)
            if 1 <= k <= len(candidates):
                return candidates[k - 1]
        except ValueError:
            pass

        print("Entrada inválida.")


def auto_plan_search(
    world,
    kb_plan,
    start,
    method,
    heuristic_fn=None,
    trace=True,
    trace_prefix="[Plan]",
):
    """
    Planifica (sin mover al agente real) usando perceptos solo de nodos explorados (Removed) y del inicio.

    Notas de diseño:
    - El objetivo NO se pasa explícitamente: se considera alcanzado cuando
      `heuristic_fn(pos) == 0` (p. ej. Manhattan al objetivo).
    - Si la frontera se vacía (no hay más celdas demostrablemente seguras),
      se pide al usuario que elija una celda NO segura para forzar su expansión.
      Esto puede permitir avanzar en planificación, pero puede llevar a la muerte
      del agente en ejecución real.

    Args:
        world (dict): Mundo real.
        kb_plan: Base de conocimiento usada durante la planificación.
        start (tuple[int,int]): Celda inicial del plan.
        method (str): Método de búsqueda ("bfs", "dfs", "gbfs", "astar").
        heuristic_fn (callable | None): Heurística h(pos) usada para:
            - determinar objetivo cuando h(pos)==0
            - priorización en GBFS/A*
        trace (bool): Si True, imprime trazas.
        trace_prefix (str): Prefijo de trazas.

    Returns:
        tuple[list[tuple[int, int]] | None, str | None, bool]:
            (path, reason, risky_used)
            - path: camino start->objetivo (lista de celdas) o None si no hay solución.
            - reason: None si hay solución; si no, string explicativo.
            - risky_used: True si en algún punto se forzó la expansión de una celda
              NO demostrablemente segura (con riesgo incierto), por falta de seguras.
    """
    method = method.lower()
    n = world["n"]

    risky_used = False

    explored_order = []
    explored_set = set()
    observed = set()

    #Observación del inicio (el agente está ahí al comenzar)
    _auto_observe_if_needed(world, kb_plan, start, observed)

    parent = {}
    step_k = 0

    #---------------- BFS ----------------
    if method == "bfs":
        q = [start]
        qi = 0
        frontier_set = {start}
        g = {start: 0}

        while True:
            if qi >= len(q):
                #No quedan nodos -> pedir expansión arriesgada
                risky = _auto_ask_user_expand_risky(
                    n, kb_plan, explored_set, frontier_set, trace_prefix=trace_prefix
                )
                if risky is None:
                    return (
                        None,
                        "No se ha encontrado solución segura y el usuario no seleccionó una expansión arriesgada.",
                        risky_used,
                    )

                risky_used = True

                pu = _auto_pick_parent_for_candidate(n, risky, explored_set, g_map=g)
                if pu is None:
                    return (
                        None,
                        "No se pudo encadenar la celda arriesgada a ninguna celda explorada.",
                        risky_used,
                    )

                if risky not in parent:
                    parent[risky] = pu
                g[risky] = g.get(pu, 0) + 1

                q.append(risky)
                frontier_set.add(risky)

                #No observamos aquí: el percepto se consultará si llega a ser removido (explorado).
                continue

            frontier_before = q[qi:]
            u = q[qi]
            qi += 1
            frontier_set.discard(u)

            explored_order.append(u)
            explored_set.add(u)

            _auto_observe_if_needed(world, kb_plan, u, observed)

            if trace:
                frontier_str = _fmt_cells_with_vals(frontier_before, lambda p: g.get(p, "?"))
                removed_str = f"{u}({g.get(u, 0)})"
                explored_str = _fmt_cells_with_vals(explored_order, lambda p: g.get(p, "?"))
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if _auto_goal_reached(u, heuristic_fn):
                return reconstruct_path(parent, start, u), None, risky_used

            allowed_now = safe_cells(kb_plan) | {start}
            for v in neighbors_allowed(n, allowed_now, u):
                if (v in explored_set) or (v in frontier_set):
                    continue
                if not is_safe(kb_plan, v):
                    continue
                parent[v] = u
                g[v] = g[u] + 1
                q.append(v)
                frontier_set.add(v)

    #---------------- DFS ----------------
    if method == "dfs":
        stack = [start]
        frontier_set = {start}
        g = {start: 0}

        while True:
            if not stack:
                risky = _auto_ask_user_expand_risky(
                    n, kb_plan, explored_set, frontier_set, trace_prefix=trace_prefix
                )
                if risky is None:
                    return (
                        None,
                        "No se ha encontrado solución segura y el usuario no seleccionó una expansión arriesgada.",
                        risky_used,
                    )

                risky_used = True

                pu = _auto_pick_parent_for_candidate(n, risky, explored_set, g_map=g)
                if pu is None:
                    return (
                        None,
                        "No se pudo encadenar la celda arriesgada a ninguna celda explorada.",
                        risky_used,
                    )

                if risky not in parent:
                    parent[risky] = pu
                g[risky] = g.get(pu, 0) + 1

                stack.append(risky)
                frontier_set.add(risky)
                continue

            frontier_before = list(stack)
            u = stack.pop()
            frontier_set.discard(u)

            if u in explored_set:
                continue

            explored_order.append(u)
            explored_set.add(u)

            _auto_observe_if_needed(world, kb_plan, u, observed)

            if trace:
                frontier_str = _fmt_cells_with_vals(frontier_before, lambda p: g.get(p, "?"))
                removed_str = f"{u}({g.get(u, 0)})"
                explored_str = _fmt_cells_with_vals(explored_order, lambda p: g.get(p, "?"))
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if _auto_goal_reached(u, heuristic_fn):
                return reconstruct_path(parent, start, u), None, risky_used

            allowed_now = safe_cells(kb_plan) | {start}
            for v in neighbors_allowed(n, allowed_now, u):
                if (v in explored_set) or (v in frontier_set):
                    continue
                if not is_safe(kb_plan, v):
                    continue
                parent[v] = u
                g[v] = g[u] + 1
                stack.append(v)
                frontier_set.add(v)

    #---------------- GBFS ----------------
    if method == "gbfs":
        frontier = []
        open_map = {}
        counter = 0

        h0 = heuristic_fn(start) if heuristic_fn is not None else 0
        frontier.append((h0, counter, start))
        open_map[start] = (h0, counter)

        while True:
            if not frontier:
                #frontera vacía -> pedir expansión arriesgada
                frontier_nodes_set = set(open_map.keys())
                risky = _auto_ask_user_expand_risky(
                    n, kb_plan, explored_set, frontier_nodes_set, trace_prefix=trace_prefix
                )
                if risky is None:
                    return (
                        None,
                        "No se ha encontrado solución segura y el usuario no seleccionó una expansión arriesgada.",
                        risky_used,
                    )

                risky_used = True

                pu = _auto_pick_parent_for_candidate(n, risky, explored_set)
                if pu is None:
                    return (
                        None,
                        "No se pudo encadenar la celda arriesgada a ninguna celda explorada.",
                        risky_used,
                    )

                if risky not in parent:
                    parent[risky] = pu

                hv = heuristic_fn(risky) if heuristic_fn is not None else 0
                counter += 1
                frontier.append((hv, counter, risky))
                open_map[risky] = (hv, counter)

                continue

            frontier_before = list(frontier)

            best_i = 0
            for i in range(1, len(frontier)):
                if frontier[i] < frontier[best_i]:
                    best_i = i

            h_u, stamp_u, u = frontier.pop(best_i)
            open_map.pop(u, None)

            if u in explored_set:
                continue

            explored_order.append(u)
            explored_set.add(u)

            _auto_observe_if_needed(world, kb_plan, u, observed)

            if trace:
                frontier_str = _fmt_frontier_tuples(frontier_before, val_index=0, cell_index=-1)
                removed_str = f"{u}({h_u})"
                explored_str = _fmt_cells_with_vals(
                    explored_order,
                    lambda p: (heuristic_fn(p) if heuristic_fn is not None else 0)
                )
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if _auto_goal_reached(u, heuristic_fn):
                return reconstruct_path(parent, start, u), None, risky_used

            allowed_now = safe_cells(kb_plan) | {start}
            for v in neighbors_allowed(n, allowed_now, u):
                if v in explored_set:
                    continue
                if not is_safe(kb_plan, v):
                    continue

                hv = heuristic_fn(v) if heuristic_fn is not None else 0

                if v not in open_map:
                    counter += 1
                    parent[v] = u
                    frontier.append((hv, counter, v))
                    open_map[v] = (hv, counter)
                else:
                    old_h, old_stamp = open_map[v]
                    if hv < old_h:
                        open_map[v] = (hv, old_stamp)
                        for i, item in enumerate(frontier):
                            if item[-1] == v:
                                frontier[i] = (hv, old_stamp, v)
                                break
                        parent[v] = u

    #---------------- A* ----------------
    if method == "astar":
        frontier = []
        open_map = {}
        counter = 0

        best_g = {start: 0}
        h0 = heuristic_fn(start) if heuristic_fn is not None else 0
        f0 = 0 + h0

        frontier.append((f0, counter, start))
        open_map[start] = (f0, counter)

        closed = set()

        while True:
            if not frontier:
                frontier_nodes_set = set(open_map.keys())
                risky = _auto_ask_user_expand_risky(
                    n, kb_plan, explored_set, frontier_nodes_set, trace_prefix=trace_prefix
                )
                if risky is None:
                    return (
                        None,
                        "No se ha encontrado solución segura y el usuario no seleccionó una expansión arriesgada.",
                        risky_used,
                    )

                risky_used = True

                pu = _auto_pick_parent_for_candidate(n, risky, explored_set, best_g=best_g)
                if pu is None:
                    return (
                        None,
                        "No se pudo encadenar la celda arriesgada a ninguna celda explorada.",
                        risky_used,
                    )

                #coste g para poder dar prioridad en A*
                gv = best_g.get(pu, 0) + 1
                best_g[risky] = min(best_g.get(risky, 10**9), gv)
                parent[risky] = pu

                hv = heuristic_fn(risky) if heuristic_fn is not None else 0
                fv = gv + hv

                counter += 1
                frontier.append((fv, counter, risky))
                open_map[risky] = (fv, counter)

                continue

            frontier_before = list(frontier)

            best_i = 0
            for i in range(1, len(frontier)):
                if frontier[i] < frontier[best_i]:
                    best_i = i

            f_u, stamp_u, u = frontier.pop(best_i)
            open_map.pop(u, None)

            if u in closed:
                continue

            closed.add(u)
            explored_order.append(u)
            explored_set.add(u)

            _auto_observe_if_needed(world, kb_plan, u, observed)

            if trace:
                frontier_str = _fmt_frontier_tuples(frontier_before, val_index=0, cell_index=-1)
                removed_str = f"{u}({f_u})"
                explored_str = _fmt_cells_with_vals(
                    explored_order,
                    lambda p: (best_g.get(p, 0) + (heuristic_fn(p) if heuristic_fn is not None else 0)),
                )
                print(f"{trace_prefix} Step {step_k} | Frontier={frontier_str} | Removed={removed_str} | Explored={explored_str}")
                step_k += 1

            if _auto_goal_reached(u, heuristic_fn):
                return reconstruct_path(parent, start, u), None, risky_used

            gu = best_g[u]
            allowed_now = safe_cells(kb_plan) | {start}

            for v in neighbors_allowed(n, allowed_now, u):
                if v in closed:
                    continue
                if not is_safe(kb_plan, v):
                    continue

                gv = gu + 1
                hv = heuristic_fn(v) if heuristic_fn is not None else 0
                fv = gv + hv

                if gv < best_g.get(v, 10**9):
                    best_g[v] = gv
                    parent[v] = u

                    if v not in open_map:
                        counter += 1
                        frontier.append((fv, counter, v))
                        open_map[v] = (fv, counter)
                    else:
                        old_f, old_stamp = open_map[v]
                        if fv < old_f:
                            open_map[v] = (fv, old_stamp)
                            for i, item in enumerate(frontier):
                                if item[-1] == v:
                                    frontier[i] = (fv, old_stamp, v)
                                    break

    raise ValueError("Método no soportado: " + str(method))


def run_auto(world, kb, search_method, steps_max=500, verbose=True, trace_search=True):
    """
    Ejecuta el modo automático: planifica primero y ejecuta después.

    El automático funciona en dos fases:
    1) Planifica una trayectoria hasta Kurtz.
    2) Planifica una trayectoria hasta la salida.

    Durante la planificación se usa una KB separada (kb_plan) y se consultan perceptos
    solo cuando se extraen nodos (Removed / explorados) y en la celda inicial, sin mover al agente real.

    Args:
        world (dict): Mundo real y estado dinámico del agente (se modifica al ejecutar acciones).
        kb (dict): KB "real" del agente (se actualiza al moverse durante la ejecución).
        search_method (str): Algoritmo de búsqueda: "bfs", "dfs", "gbfs" o "astar".
        steps_max (int): Límite máximo de acciones ejecutadas.
        verbose (bool): Si True, imprime información y el mapa durante la ejecución.
        trace_search (bool): Si True, imprime traza de planificación (frontier/removed/explored).

    Returns:
        dict: Resumen de la ejecución. Incluye claves como:
            - "result": {"success","dead","timeout","no_safe_solution","done"}
            - "positions": lista de posiciones recorridas
            - "actions": lista de acciones ejecutadas
            - (y, si aplica, trazas/planes intermedios)
    """
    method = search_method.lower()
    start = world["agent"]

    #Heurísticas (si aplica) como "oráculo de distancia" al objetivo
    h_kurtz = (lambda p: manhattan(p, world["kurtz"])) 
    h_exit = (lambda p: manhattan(p, world["exit"]))

    #---------------- PLANIFICACIÓN (KB separada) ----------------
    kb_plan = clone_kb(kb)

    print("\n=== PLANIFICACIÓN A KURTZ ===")
    path1, reason1, risky1 = auto_plan_search(
        world=world,
        kb_plan=kb_plan,
        start=start,
        method=method,
        heuristic_fn=h_kurtz,
        trace=trace_search,
        trace_prefix="[Plan]",
    )
    if path1 is None:
        print("\n[Auto] Parado:", reason1)
        return {
            "result": "no_safe_solution",
            "reason": reason1,
            "risky_used": False,
            "risky_used_plan_1": False,
            "risky_used_plan_2": False,
            "death_due_to_risky": False,
            "plan_positions_1": None,
            "plan_actions_1": None,
            "plan_positions_2": None,
            "plan_actions_2": None,
            "positions": [start],
            "actions": [],
        }

    actions1 = path_to_actions(path1)
    kurtz_pos = path1[-1]

    print("\n=== PLANIFICACIÓN A SALIDA ===")
    path2, reason2, risky2 = auto_plan_search(
        world=world,
        kb_plan=kb_plan,
        start=kurtz_pos,
        method=method,
        heuristic_fn=h_exit,
        trace=trace_search,
        trace_prefix="[Plan]",
    )
    if path2 is None:
        print("\n[Auto] Parado:", reason2)
        return {
            "result": "no_safe_solution",
            "reason": reason2,
            "risky_used": bool(risky1),
            "risky_used_plan_1": bool(risky1),
            "risky_used_plan_2": False,
            "death_due_to_risky": False,
            "plan_positions_1": path1,
            "plan_actions_1": actions1,
            "plan_positions_2": None,
            "plan_actions_2": None,
            "positions": [start],
            "actions": [],
        }

    actions2 = path_to_actions(path2)

    risky_used = bool(risky1 or risky2)

    print("\n[Auto] Plan 1 (posiciones):", " -> ".join(map(str, path1)))
    print("[Auto] Plan 1 (teclas):    ", " ".join(DIR_TO_KEY[a] for a in actions1))
    print("\n[Auto] Plan 2 (posiciones):", " -> ".join(map(str, path2)))
    print("[Auto] Plan 2 (teclas):    ", " ".join(DIR_TO_KEY[a] for a in actions2))
    print("\n=== EJECUCIÓN ===\n")

    #---------------- EJECUCIÓN REAL (KB real) ----------------
    positions_exec = [world["agent"]]
    actions_exec = []
    steps = 0

    per0 = percept(world)
    update_kb(kb, world["agent"], per0, soldier_alive=world["soldier_alive"])
    if verbose:
        render(world, kb, per=per0)
        print_percept(per0)

    for act in actions1 + actions2:
        steps += 1
        if steps > steps_max:
            return {
                "result": "timeout",
                "risky_used": risky_used,
                "risky_used_plan_1": bool(risky1),
                "risky_used_plan_2": bool(risky2),
                "death_due_to_risky": False,
                "plan_positions_1": path1,
                "plan_actions_1": actions1,
                "plan_positions_2": path2,
                "plan_actions_2": actions2,
                "positions": positions_exec,
                "actions": actions_exec,
            }

        step_move(world, act)
        actions_exec.append(act)
        positions_exec.append(world["agent"])

        if not world["alive"]:
            if verbose:
                render(world, kb, per=None)
            if risky_used:
                print("\n[Auto] Resultado final: HAS MUERTO debido a que, al elegir una celda NO segura en planificación, la decisión falló durante la ejecución.")
            else:
                print("\n[Auto] Resultado final: HAS MUERTO.")
            return {
                "result": "dead",
                "risky_used": risky_used,
                "risky_used_plan_1": bool(risky1),
                "risky_used_plan_2": bool(risky2),
                "death_due_to_risky": bool(risky_used),
                "plan_positions_1": path1,
                "plan_actions_1": actions1,
                "plan_positions_2": path2,
                "plan_actions_2": actions2,
                "positions": positions_exec,
                "actions": actions_exec,
            }

        per = percept(world)
        update_kb(kb, world["agent"], per, soldier_alive=world["soldier_alive"])

        if verbose:
            render(world, kb, per=per)
            print_percept(per)
            if per[7]:
                print("Se oye un grito a lo lejos.")

    if world["agent"] == world["exit"] and world["kurtz_found"]:
        if step_exit(world):
            actions_exec.append("X")
            if verbose:
                render(world, kb, per=None)
            print("\n[Auto] Resultado final: ÉXITO (has salido con Kurtz).")
            return {
                "result": "success",
                "risky_used": risky_used,
                "risky_used_plan_1": bool(risky1),
                "risky_used_plan_2": bool(risky2),
                "death_due_to_risky": False,
                "plan_positions_1": path1,
                "plan_actions_1": actions1,
                "plan_positions_2": path2,
                "plan_actions_2": actions2,
                "positions": positions_exec,
                "actions": actions_exec,
            }

    return {
        "result": "done",
        "risky_used": risky_used,
        "risky_used_plan_1": bool(risky1),
        "risky_used_plan_2": bool(risky2),
        "death_due_to_risky": False,
        "plan_positions_1": path1,
        "plan_actions_1": actions1,
        "plan_positions_2": path2,
        "plan_actions_2": actions2,
        "positions": positions_exec,
        "actions": actions_exec,
    }

def ask_int(prompt: str, default: int | None = None, min_value: int | None = None) -> int:
    """Pide un entero al usuario con soporte de valor por defecto y mínimo.

    Args:
        prompt (str): Texto mostrado en el input.
        default (int | None): Valor por defecto si el usuario pulsa ENTER.
        min_value (int | None): Mínimo permitido (inclusive). Si se da, se valida.

    Returns:
        int: Entero válido introducido por el usuario (o default).

    """
    while True:
        s = input(prompt).strip()
        if s == "":
            if default is not None:
                x = default
            else:
                print("Debes introducir un número entero.")
                continue
        else:
            try:
                x = int(s)
            except ValueError:
                print("Valor inválido: introduce un número entero.")
                continue

        if min_value is not None and x < min_value:
            print(f"Valor inválido: debe ser >= {min_value}.")
            continue

        return x

def ask_choice(prompt: str, choices: list[str]) -> str:
    """Pide una opción al usuario hasta que sea válida.

    Args:
        prompt: Texto del input.
        choices: Lista de opciones permitidas (minúsculas o mayúsculas).

    Returns:
        La opción elegida en minúsculas.
    """
    valid = [c.lower() for c in choices]
    while True:
        ans = input(prompt).strip().lower()
        if ans in valid:
            return ans
        print("Opción inválida. Opciones válidas: " + "/".join(valid))


def ask_yes_no(prompt: str, default=None) -> bool:
    """Pregunta sí/no (s/n). ENTER devuelve default si se proporciona.

    Args:
        prompt: Texto del input.
        default: Valor por defecto si el usuario pulsa ENTER (True/False) o None.

    Returns:
        True si responde sí, False si responde no.
    """
    yes = {"s", "si", "sí", "y", "yes"}
    no = {"n", "no"}
    while True:
        ans = input(prompt).strip().lower()
        if ans == "" and default is not None:
            return bool(default)
        if ans in yes:
            return True
        if ans in no:
            return False
        print("Respuesta inválida. Escribe 's' o 'n'.")


def enable_utf8_output():
    """Fuerza la salida estandar a UTF-8 para que no fallen los simbolos del tablero.

    Por que hace falta:
    -El tablero usa caracteres que no existen en las codificaciones antiguas de Windows
     (por ejemplo el visto bueno y las flechas).
    -En una consola normal Python ya los imprime bien, pero al redirigir la salida a un
     fichero o a otro programa usa la codificacion local (cp1252) y salta UnicodeEncodeError.
    -Con errors="replace" el programa nunca se cae: como mucho se ve un simbolo sustituto.

    Returns:
        None
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main():
    """Punto de entrada.

    Returns:
        None
    """
    print("==============================================")
    print(" Buscando al Coronel Kurtz - Parte 1 (FIA) ")
    print("==============================================\n")

    mode = ask_choice("Elige modo [manual/auto]: ", ["manual", "auto"])

    search_method = "bfs"
    verbose = True
    if mode == "auto":
        search_method = ask_choice("Elige búsqueda [bfs/dfs/gbfs/astar]: ", ["bfs", "dfs", "gbfs", "astar"])
        verbose = not ask_yes_no("¿Modo silencioso (menos prints)?[s/n] (por defecto n): ", default=False)

    #Validamos la semilla:si no es un entero,volvemos a pedirla
    #Esto evita errores si el usuario escribe "p" u otra cosa
    seed = None
    while True:
        seed_txt = input("Semilla (ENTER para aleatorio): ").strip()
        if seed_txt == "":
            seed = None
            break
        try:
            seed = int(seed_txt)
            break
        except ValueError:
            print("Semilla inválida:introduce un número entero o pulsa ENTER para aleatorio.")


    #Tamaño del tablero (mínimo lógico: 3, porque deben caber 7 celdas distintas:
    #start + 3 pits + soldier + exit + kurtz)
    n = ask_int("Tamaño del tablero n (ENTER para 6): ", default=6, min_value=3)
    world = make_world(n)

    reset_world(world, seed=seed)
    kb = make_kb(world["n"], world["start"])

    if mode == "manual":
        run_manual(world, kb)
    else:
        res = run_auto(
            world,
            kb,
            search_method=search_method,
            steps_max=500,
            verbose=verbose,
            trace_search=verbose,
        )

        #Resumen útil para corregir: camino y acciones realmente ejecutadas
        print("\n=== RESUMEN AUTO ===")
        print("Resultado:", res["result"])
        print("Posiciones:", res["positions"])
        print("Acciones  :", res["actions"])



if __name__ == "__main__":
    enable_utf8_output()
    main()
