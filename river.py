"""
Parte 2 - Ejercicio 2
Cruce del río modelado como un Proceso de Decisión de Markov (MDP)

Qué hace este programa:
-Crea un mapa del río con orillas, corriente por columnas, islas y una salida
-Define el MDP: estados, acciones, probabilidades de transición y recompensas
-Resuelve el problema con Value Iteration para obtener V(s) y una política óptima
-Imprime V(s) y la política
-Simula varias partidas siguiendo la política y da un resumen final

Extra:
-Se puede elegir cuantas islas crear
-Se permite introducir un factor de descuento en (0,1], por defecto 1.0
-Se puede activar una variante donde las islas son "mortales" (entrar en I termina la partida con penalización)
"""

import math
import random
import sys
from collections import deque

import numpy as np


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[96m",
    "magenta": "\033[95m",
    "blue": "\033[94m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "gray": "\033[90m",
    "green": "\033[92m",
}

ARROW = {"up": "^", "down": "v", "left": "<", "right": ">", "stay": "o"}


def color(text: str, c: str) -> str:
    """Aplica un color ANSI a un texto.

    Args:
        text (str): Texto a colorear.
        c (str): Nombre del color dentro del diccionario ANSI.

    Returns:
        str: Texto con códigos ANSI (si el color existe), o texto sin cambios.

    """
    if c in ANSI:
        return ANSI[c] + text + ANSI["reset"]
    return text


def _is_int_str(s: str) -> bool:
    """Comprueba si un string representa un entero (con signo opcional).

    Args:
        s (str): Cadena a comprobar.

    Returns:
        bool: True si s es un entero válido, False en caso contrario.

    """
    if s == "":
        return False
    if s[0] == "-":
        return s[1:].isdigit() and (len(s) > 1)
    return s.isdigit()


def _parse_float(s: str) -> float | None:
    """Intenta convertir un texto a float de forma segura.

    Detalles prácticos:
    -Se aceptan formatos habituales: 1, 1., .5, 0.25, 1e-3, -2.7
    -Se rechazan NaN e infinitos para evitar comportamientos raros

    Args:
        s (str): Texto a convertir.

    Returns:
        float | None: Float si se puede; None si no.

    """
    try:
        x = float(s)
    except Exception:
        return None
    if not math.isfinite(x):
        return None
    return x


def ask_int(prompt: str, default: int | None = None, min_value: int | None = None, max_value: int | None = None) -> int:
    """Pide un entero al usuario con valor por defecto y validación de rango.

    Comportamiento:
    -ENTER aplica el default si existe
    -Si el usuario escribe algo inválido, se vuelve a pedir
    -Si hay rango, se valida (min_value<=x<=max_value) y si no, se vuelve a pedir

    Args:
        prompt (str): Texto mostrado en el input.
        default (int | None): Valor por defecto si el usuario pulsa ENTER.
        min_value (int | None): Mínimo permitido (inclusive).
        max_value (int | None): Máximo permitido (inclusive).

    Returns:
        int: Entero válido.

    """
    while True:
        t = input(prompt).strip()

        if t == "":
            if default is None:
                print("Debes introducir un entero.")
                continue
            val = int(default)
        else:
            if not _is_int_str(t):
                print("Entrada inválida. Escribe un entero o pulsa ENTER para el valor por defecto.")
                continue
            val = int(t)

        if min_value is not None and val < int(min_value):
            print(f"Valor fuera de rango: debe ser >= {int(min_value)}.")
            continue
        if max_value is not None and val > int(max_value):
            print(f"Valor fuera de rango: debe ser <= {int(max_value)}.")
            continue

        return val


def ask_int_or_none(prompt: str) -> int | None:
    """Pide un entero o permite ENTER para devolver None.

    Uso típico:
    -Para la semilla: si es None, el mapa será aleatorio
    -Si se da un entero, el mapa será reproducible

    Args:
        prompt (str): Texto mostrado en el input.

    Returns:
        int | None: Entero si se introduce correctamente; None si se pulsa ENTER.

    """
    while True:
        t = input(prompt).strip()
        if t == "":
            return None
        if _is_int_str(t):
            return int(t)
        print("Entrada inválida. Escribe un entero o pulsa ENTER.")


def ask_float(prompt: str, default: float | None = None, min_value: float | None = None, max_value: float | None = None) -> float:
    """Pide un float al usuario con valor por defecto y validación de rango.

    Comportamiento:
    -ENTER aplica el default si existe
    -Si el usuario escribe algo inválido, se vuelve a pedir
    -Si hay rango, se valida (min_value<=x<=max_value) y si no, se vuelve a pedir

    Args:
        prompt (str): Texto mostrado en el input.
        default (float | None): Valor por defecto si el usuario pulsa ENTER.
        min_value (float | None): Mínimo permitido (inclusive).
        max_value (float | None): Máximo permitido (inclusive).

    Returns:
        float: Float válido.

    """
    while True:
        t = input(prompt).strip()

        if t == "":
            if default is None:
                print("Debes introducir un número.")
                continue
            val = float(default)
        else:
            parsed = _parse_float(t)
            if parsed is None:
                print("Entrada inválida. Escribe un número (ej: 0.25) o pulsa ENTER para el valor por defecto.")
                continue
            val = float(parsed)

        if min_value is not None and val < float(min_value):
            print(f"Valor fuera de rango: debe ser >= {float(min_value)}.")
            continue
        if max_value is not None and val > float(max_value):
            print(f"Valor fuera de rango: debe ser <= {float(max_value)}.")
            continue

        return val


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """Pide una respuesta sí/no al usuario con valor por defecto.

    Acepta:
    -sí: s, si, sí, y, yes, 1, true
    -no: n, no, 0, false

    Args:
        prompt (str): Texto mostrado en el input.
        default_yes (bool): Respuesta por defecto si el usuario pulsa ENTER.

    Returns:
        bool: True si la respuesta es sí, False si es no.

    """
    while True:
        t = input(prompt).strip().lower()
        if t == "":
            return bool(default_yes)
        if t in ["s", "si", "sí", "y", "yes", "1", "true", "t"]:
            return True
        if t in ["n", "no", "0", "false", "f"]:
            return False
        print("Responde con s/n (o pulsa ENTER para el valor por defecto).")


def in_bounds(rows: int, cols: int, s: tuple[int, int]) -> bool:
    """Comprueba si un estado está dentro de la rejilla.

    Args:
        rows (int): Filas del mapa.
        cols (int): Columnas del mapa.
        s (tuple[int,int]): Coordenadas (fila, columna).

    Returns:
        bool: True si está dentro, False si no.

    """
    r, c = s
    return 0 <= r < rows and 0 <= c < cols


def try_move(s: tuple[int, int], action: str) -> tuple[int, int]:
    """Aplica un desplazamiento determinista según la acción.

    Nota:
    -Esta función solo calcula el destino "ideal"
    -Luego, las transiciones aplican reglas de choque (borde/isla) y corriente

    Args:
        s (tuple[int,int]): Estado actual.
        action (str): Acción ("up","down","left","right","stay").

    Returns:
        tuple[int,int]: Estado destino (puede quedar fuera; se valida después).

    """
    r, c = s
    if action == "up":
        return (r - 1, c)
    if action == "down":
        return (r + 1, c)
    if action == "left":
        return (r, c - 1)
    if action == "right":
        return (r, c + 1)
    return (r, c)


def _neighbors4(rows: int, cols: int, s: tuple[int, int]) -> list[tuple[int, int]]:
    """Vecinos 4-conexos dentro de límites.

    Args:
        rows (int): Filas.
        cols (int): Columnas.
        s (tuple[int,int]): Estado.

    Returns:
        list[tuple[int,int]]: Vecinos válidos en la rejilla.

    """
    r, c = s
    cand = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    out = []
    i = 0
    while i < len(cand):
        v = cand[i]
        if in_bounds(rows, cols, v):
            out.append(v)
        i += 1
    return out


def _has_path_avoiding_islands(rows: int, cols: int, start: tuple[int, int], goal: tuple[int, int], islands: set[tuple[int, int]]) -> bool:
    """Comprueba que existe un camino start->goal evitando islas (BFS simple).

    Por qué se hace esto:
    -Para evitar crear mapas imposibles al colocar islas aleatoriamente
    -Este chequeo garantiza que al menos existe una ruta geométrica (sin tener en cuenta la corriente)

    Args:
        rows (int): Filas.
        cols (int): Columnas.
        start (tuple[int,int]): Inicio.
        goal (tuple[int,int]): Objetivo.
        islands (set[tuple[int,int]]): Obstáculos.

    Returns:
        bool: True si hay camino, False si no.

    """
    if start == goal:
        return True
    if start in islands or goal in islands:
        return False

    q = deque([start])
    seen = {start}

    while len(q) > 0:
        u = q.popleft()
        neigh = _neighbors4(rows, cols, u)
        j = 0
        while j < len(neigh):
            v = neigh[j]
            if v not in seen and v not in islands:
                if v == goal:
                    return True
                seen.add(v)
                q.append(v)
            j += 1

    return False


def _interior_cells(rows: int, cols: int) -> list[tuple[int, int]]:
    """Devuelve las celdas interiores (no perímetro).

    Qué significa "interior" aquí:
    -No incluye primera ni última fila
    -No incluye primera ni última columna

    Motivo práctico:
    -Evita poner islas en el perímetro, manteniendo un pasillo exterior libre

    Args:
        rows (int): Filas.
        cols (int): Columnas.

    Returns:
        list[tuple[int,int]]: Lista de posiciones interiores.

    """
    out = []
    if rows < 3 or cols < 3:
        return out
    r = 1
    while r < rows - 1:
        c = 1
        while c < cols - 1:
            out.append((r, c))
            c += 1
        r += 1
    return out


def _make_river_strength(cols: int, min_strength: float, max_strength: float) -> list[float]:
    """Crea la fuerza de corriente por columna.

    Reglas:
    -Primera y última columna: corriente 0
    -Columnas interiores: valor aleatorio uniforme y redondeado a 1 decimal
    -Se fuerza a estar en [0,1] porque es una probabilidad
    -Si min>max, se intercambian

    Args:
        cols (int): Número de columnas.
        min_strength (float): Mínimo interior.
        max_strength (float): Máximo interior.

    Returns:
        list[float]: Fuerza por columna.

    """
    mn = float(min_strength)
    mx = float(max_strength)

    if mn < 0.0:
        mn = 0.0
    if mx > 1.0:
        mx = 1.0
    if mn > mx:
        tmp = mn
        mn = mx
        mx = tmp

    out = [0.0 for _ in range(cols)]
    j = 1
    while j < cols - 1:
        out[j] = round(random.uniform(mn, mx), 1)
        j += 1
    return out


def make_river_world(
    rows: int = 7,
    cols: int = 6,
    seed: int | None = None,
    n_islands: int = 2,
    min_strength: float = 0.06,
    max_strength: float = 0.94,
    step_cost: float = -1.0,
    reward_exit: float = 100.0,
    reward_island: float = -100.0,
    discount: float = 1.0,
    deadly_islands: bool = False,
) -> dict:
    """Genera el mundo del río y todos los parámetros del MDP.

    Elementos principales:
    -Inicio fijo en (0,0)
    -Salida en la última columna, fila aleatoria
    -Islas en el interior
    -Orillas en primera y última columna
    -Corriente por columna

    Extra controlado:
    -deadly_islands: si se activa, entrar en una isla termina la partida con penalización
    -discount: factor en (0,1], por defecto 1.0

    Args:
        rows (int): Filas del mapa.
        cols (int): Columnas del mapa.
        seed (int | None): Semilla opcional.
        n_islands (int): Número de islas.
        min_strength (float): Corriente mínima interior.
        max_strength (float): Corriente máxima interior.
        step_cost (float): Coste por paso.
        reward_exit (float): Recompensa al llegar a la salida.
        reward_island (float): Penalización al caer en isla (solo si deadly_islands=True).
        discount (float): Factor de descuento extra en (0,1].
        deadly_islands (bool): Variante de islas "mortales".

    Returns:
        dict: Diccionario con la información completa del mundo.

    """
    if seed is not None:
        #Se fija semilla para que el mapa sea reproducible
        random.seed(int(seed))
        np.random.seed(int(seed))

    rows = int(rows)
    cols = int(cols)

    if cols < 2:
        cols = 2
    if rows < 2:
        rows = 2

    disc = float(discount)
    if disc <= 0.0 or disc > 1.0:
        disc = 1.0

    start = (0, 0)
    exit_pos = (random.randint(0, rows - 1), cols - 1)

    interior = _interior_cells(rows, cols)
    max_islands = len(interior)

    n_islands = int(n_islands)
    if n_islands < 0:
        n_islands = 0

    islands = set()

    if max_islands > 0 and n_islands > 0:
        if n_islands >= max_islands:
            #Si se piden más islas de las que caben, todo el interior pasa a ser isla
            islands = set(interior)
        else:
            tries = 0
            placed = False
            #Se intentan varias colocaciones para evitar bloquear el camino hacia la salida
            while tries < 3000 and not placed:
                islands = set(random.sample(interior, n_islands))
                if _has_path_avoiding_islands(rows, cols, start, exit_pos, islands):
                    placed = True
                tries += 1
            if not placed:
                #Si no se consigue colocar sin bloquear, se prefiere no poner islas a crear un mundo imposible
                islands = set()

    river_strength = _make_river_strength(cols, min_strength, max_strength)
    actions = ["up", "down", "left", "right", "stay"]

    return {
        "rows": rows,
        "cols": cols,
        "seed": seed,
        "start": start,
        "exit": exit_pos,
        "actions": actions,
        "islands": islands,
        "deadly_islands": bool(deadly_islands),
        "river_strength": river_strength,
        "step_cost": float(step_cost),
        "reward_exit": float(reward_exit),
        "reward_island": float(reward_island),
        "discount": float(disc),
        "max_islands": max_islands,
        "min_strength": float(min_strength),
        "max_strength": float(max_strength),
    }


def is_terminal(world: dict, s: tuple[int, int]) -> bool:
    """Comprueba si un estado es terminal.

    Regla principal:
    -La partida termina cuando se alcanza la salida

    Variante:
    -Si deadly_islands=True, también termina si se entra en una isla

    Args:
        world (dict): Mundo.
        s (tuple[int,int]): Estado.

    Returns:
        bool: True si es terminal, False si no.

    """
    if s == world["exit"]:
        return True
    if world["deadly_islands"] and (s in world["islands"]):
        return True
    return False


def _action_invalid_as_chosen(world: dict, s: tuple[int, int], a: str) -> bool:
    """Indica si la acción elegida apunta fuera del mapa o a una isla (cuando son obstáculo).

    Regla:
    -Si la acción elegida llevaría fuera o a una isla (cuando no son mortales), entonces pstay=1
    -En ese caso se ignora el efecto de la corriente en ese turno

    Si deadly_islands=True:
    -Entrar en isla sí es un movimiento válido (y termina)

    Args:
        world (dict): Mundo.
        s (tuple[int,int]): Estado.
        a (str): Acción.

    Returns:
        bool: True si el destino directo es inválido, False si es válido.

    """
    rows, cols = world["rows"], world["cols"]
    ns = try_move(s, a)
    if not in_bounds(rows, cols, ns):
        return True
    if (not world["deadly_islands"]) and (ns in world["islands"]):
        return True
    return False


def transition_probs(world: dict, s: tuple[int, int], a: str) -> list[tuple[tuple[int, int], float]]:
    """Calcula la distribución P(s'|s,a).

    Reglas:
    -Si estás en terminal, te quedas con probabilidad 1
    -Si la acción elegida es inválida (borde o isla obstáculo), te quedas con probabilidad 1
    -Si a=="down", se intenta bajar con probabilidad 1
    -Si a!="down", hay mezcla:
        ir en la dirección elegida con prob 1-river_strength(col)
        ser empujado hacia abajo con prob river_strength(col)
    -Si alguno de esos dos destinos es inválido, esa parte de probabilidad se convierte en quedarse

    Args:
        world (dict): Mundo.
        s (tuple[int,int]): Estado.
        a (str): Acción.

    Returns:
        list[tuple[tuple[int,int],float]]: Lista (estado, probabilidad).

    """
    if is_terminal(world, s):
        return [(s, 1.0)]

    rows, cols = world["rows"], world["cols"]
    j = s[1]
    strength = float(world["river_strength"][j])

    if _action_invalid_as_chosen(world, s, a):
        return [(s, 1.0)]

    if a == "down":
        ns = try_move(s, "down")
        if not in_bounds(rows, cols, ns):
            return [(s, 1.0)]
        if (not world["deadly_islands"]) and (ns in world["islands"]):
            return [(s, 1.0)]
        return [(ns, 1.0)]

    pdir = 1.0 - strength
    pdown = strength

    dist = {}

    ns_dir = try_move(s, a)
    if not in_bounds(rows, cols, ns_dir):
        ns_dir = s
    else:
        if (not world["deadly_islands"]) and (ns_dir in world["islands"]):
            ns_dir = s
    dist[ns_dir] = dist.get(ns_dir, 0.0) + pdir

    ns_down = try_move(s, "down")
    if not in_bounds(rows, cols, ns_down):
        ns_down = s
    else:
        if (not world["deadly_islands"]) and (ns_down in world["islands"]):
            ns_down = s
    dist[ns_down] = dist.get(ns_down, 0.0) + pdown

    out = []
    total = 0.0
    for k in dist:
        total += dist[k]

    if total <= 0.0:
        return [(s, 1.0)]

    for k in dist:
        out.append((k, dist[k] / total))
    return out


def reward(world: dict, s: tuple[int, int], a: str, ns: tuple[int, int]) -> float:
    """Función de recompensas.

    Interpretación:
    -Cada paso cuesta step_cost (por defecto -1)
    -Llegar a la salida suma reward_exit (por defecto +100)
    -Si deadly_islands=True y se entra en isla, suma reward_island (por defecto -100)

    Args:
        world (dict): Mundo.
        s (tuple[int,int]): Estado actual.
        a (str): Acción.
        ns (tuple[int,int]): Estado siguiente.

    Returns:
        float: Recompensa de la transición.

    """
    r = float(world["step_cost"])

    if ns == world["exit"]:
        r += float(world["reward_exit"])

    if world["deadly_islands"] and (ns in world["islands"]):
        r += float(world["reward_island"])

    return r


def build_state_list(world: dict) -> list[tuple[int, int]]:
    """Construye la lista de estados para Value Iteration.

    Regla:
    -Si las islas son obstáculo, se excluyen porque no se puede estar en ellas
    -Si deadly_islands=True, se incluyen porque sí se puede entrar (y son terminales)

    Args:
        world (dict): Mundo.

    Returns:
        list[tuple[int,int]]: Estados.

    """
    rows, cols = world["rows"], world["cols"]
    states = []
    r = 0
    while r < rows:
        c = 0
        while c < cols:
            s = (r, c)
            if (not world["deadly_islands"]) and (s in world["islands"]):
                c += 1
            else:
                states.append(s)
                c += 1
        r += 1
    return states


def value_iteration(world: dict, theta: float = 1e-6, max_iter: int = 20000, show_progress: bool = True) -> tuple[np.ndarray, dict, dict]:
    """Calcula V(s) y una política óptima con Value Iteration.

    Qué es theta:
    -Umbral de parada
    -En cada iteración medimos delta = máximo cambio absoluto en V
    -Si delta<theta, paramos

    Nota importante sobre el descuento:
    -Con discount<1, la convergencia es mucho más estable
    -Con discount=1, puede tardar mucho o no alcanzar theta en el límite de iteraciones
    -En ese caso el programa no falla: devuelve la mejor aproximación tras max_iter

    ç
    Args:
        world (dict): Mundo.
        theta (float): Tolerancia de convergencia.
        max_iter (int): Máximo de iteraciones.
        show_progress (bool): Si True, imprime información de delta cada cierto número de iteraciones.

    Returns:
        tuple[np.ndarray, dict, dict]:
            V (np.ndarray): Tabla de valores.
            policy (dict): Política greedy óptima.
            info (dict): Información de convergencia.

    """
    rows, cols = world["rows"], world["cols"]
    discount = float(world["discount"])
    states = build_state_list(world)
    actions = world["actions"]

    V = np.zeros((rows, cols), dtype=float)

    it = 0
    stop = False
    last_delta = 0.0

    while it < int(max_iter) and not stop:
        it += 1
        delta = 0.0
        newV = V.copy()

        i = 0
        while i < len(states):
            s = states[i]
            if is_terminal(world, s):
                newV[s[0], s[1]] = 0.0
            else:
                best_q = None
                ai = 0
                while ai < len(actions):
                    a = actions[ai]
                    trans = transition_probs(world, s, a)
                    q = 0.0
                    tj = 0
                    while tj < len(trans):
                        ns, p = trans[tj]
                        q += float(p) * (reward(world, s, a, ns) + discount * V[ns[0], ns[1]])
                        tj += 1
                    if best_q is None or q > best_q:
                        best_q = q
                    ai += 1

                if best_q is None:
                    best_q = 0.0
                newV[s[0], s[1]] = float(best_q)

            diff = abs(newV[s[0], s[1]] - V[s[0], s[1]])
            if diff > delta:
                delta = diff
            i += 1

        V = newV
        last_delta = float(delta)

        if show_progress:
            if it == 1 or it == 2 or it == 5 or it == 10 or it % 50 == 0:
                print(f"Iteración {it}: delta={delta:.3e}")

        if delta < float(theta):
            stop = True

    policy = {}
    i = 0
    while i < len(states):
        s = states[i]
        if is_terminal(world, s):
            policy[s] = None
        else:
            best_a = None
            best_q = None
            ai = 0
            while ai < len(actions):
                a = actions[ai]
                trans = transition_probs(world, s, a)
                q = 0.0
                tj = 0
                while tj < len(trans):
                    ns, p = trans[tj]
                    q += float(p) * (reward(world, s, a, ns) + discount * V[ns[0], ns[1]])
                    tj += 1
                if best_q is None or q > best_q:
                    best_q = q
                    best_a = a
                ai += 1
            policy[s] = best_a

        i += 1

    info = {"iterations": it, "delta": last_delta, "converged": bool(stop)}
    return V, policy, info


def _legend_lines(world: dict) -> list[str]:
    """Construye la lista de líneas de leyenda a imprimir.

    Args:
        world (dict): Mundo.

    Returns:
        list[str]: Líneas de la leyenda.

    """
    lines = []
    lines.append(color("LEYENDA (mapa):", "bold"))
    lines.append("  " + color("CWCK", "cyan") + " inicio")
    lines.append("  " + color("E", "magenta") + " salida")
    lines.append("  " + color("R", "blue") + " río seguro")
    lines.append("  " + color("|", "gray") + " orilla (columna 0 y última; corriente 0)")
    if world["deadly_islands"]:
        lines.append("  " + color("I", "red") + " isla peligrosa (si entras, termina)")
    else:
        lines.append("  " + color("I", "yellow") + " isla/obstáculo (no se puede entrar)")

    lines.append(color("LEYENDA (política):", "bold"))
    lines.append("  " + color("^ v < > o", "green") + " up down left right stay")
    lines.append("  " + color("S>", "cyan") + " inicio con acción recomendada (ejemplo)")
    lines.append("  " + color("E", "magenta") + " salida (terminal)")
    lines.append("  " + color("·", "gray") + " terminal/sin acción")
    return lines


def print_legend(world: dict) -> None:
    """Imprime la leyenda de símbolos y colores.

    Args:
        world (dict): Mundo.

    """
    lines = _legend_lines(world)
    i = 0
    while i < len(lines):
        print(lines[i])
        i += 1


def print_world(world: dict, agent: tuple[int, int] | None = None, title: str = "RÍO") -> None:
    """Imprime el mapa del río con colores.

    Detalle sobre las orillas:
    -Se muestran como '|'
    -La primera y última columna tienen corriente 0

    Args:
        world (dict): Mundo.
        agent (tuple[int,int] | None): Posición del agente para resaltarla.
        title (str): Título.

    """
    rows, cols = world["rows"], world["cols"]
    seed_txt = str(world["seed"]) if world["seed"] is not None else "aleatoria"

    print("")
    print(color(title, "bold"))
    print(f"Seed={seed_txt} | start={world['start']} | exit={world['exit']}")
    print(f"Islas={len(world['islands'])}/{world['max_islands']} | islas_peligrosas={world['deadly_islands']} | descuento(extra)={world['discount']}")
    print("river_strength por columna:", world["river_strength"])

    cell_w = 5
    r = 0
    while r < rows:
        line = "|| "
        c = 0
        while c < cols:
            s = (r, c)

            tok = "R"
            tok_col = "blue"

            if c == 0 or c == cols - 1:
                tok = "|"
                tok_col = "gray"

            if s in world["islands"]:
                tok = "I"
                tok_col = "red" if world["deadly_islands"] else "yellow"

            if s == world["exit"]:
                tok = "E"
                tok_col = "magenta"

            if agent is not None and s == agent:
                tok = "CWCK"
                tok_col = "cyan"

            cell = tok
            if len(cell) < cell_w:
                pad = cell_w - len(cell)
                k = 0
                while k < pad:
                    cell += " "
                    k += 1
            else:
                cell = cell[:cell_w]

            line += color(cell, tok_col)
            if c < cols - 1:
                line += " "
            c += 1

        line += " ||"
        print(line)
        r += 1


def print_policy(world: dict, policy: dict) -> None:
    """Imprime la política óptima como flechas sobre el mapa.

    -En el inicio se muestra S + flecha centrado (ej: " S>  ")
    -La salida se muestra como E (terminal)

    Args:
        world (dict): Mundo.
        policy (dict): Política estado->acción.

    """
    rows, cols = world["rows"], world["cols"]
    cell_w = 5

    print("")
    print(color("Política óptima:", "bold"))

    r = 0
    while r < rows:
        line = "|| "
        c = 0
        while c < cols:
            s = (r, c)

            if s == world["exit"]:
                tok_col = "magenta"
                cell = "E".center(cell_w)
            elif world["deadly_islands"] and (s in world["islands"]):
                tok_col = "red"
                cell = "I".center(cell_w)
            elif (not world["deadly_islands"]) and (s in world["islands"]):
                tok_col = "yellow"
                cell = "I".center(cell_w)
            elif s == world["start"]:
                tok_col = "cyan"
                a = policy.get(s, None)
                if a is None:
                    cell = "S".center(cell_w)
                else:
                    tok = "S" + ARROW[a]
                    if len(tok) > cell_w:
                        cell = tok[:cell_w]
                    else:
                        cell = tok.center(cell_w)
            else:
                a = policy.get(s, None)
                if a is None:
                    tok_col = "gray"
                    cell = "·".center(cell_w)
                else:
                    tok_col = "green"
                    cell = ARROW[a].center(cell_w)

            line += color(cell, tok_col)
            if c < cols - 1:
                line += " "
            c += 1

        line += " ||"
        print(line)
        r += 1


def print_values(world: dict, V: np.ndarray, decimals: int = 1) -> None:
    """Imprime la tabla V(s).

    Args:
        world (dict): Mundo.
        V (np.ndarray): Valores.
        decimals (int): Decimales a imprimir.

    """
    rows, cols = world["rows"], world["cols"]
    print("")
    print(color("Tabla de valores V(s):", "bold"))

    r = 0
    while r < rows:
        line = ""
        c = 0
        while c < cols:
            s = (r, c)
            if s == world["exit"]:
                cell = color("  E  ", "magenta")
            elif s == world["start"]:
                cell = color("  S  ", "cyan")
            elif (not world["deadly_islands"]) and (s in world["islands"]):
                cell = color("  I  ", "yellow")
            elif world["deadly_islands"] and (s in world["islands"]):
                cell = color("  I  ", "red")
            else:
                fmt = "{:>5." + str(int(decimals)) + "f}"
                cell = fmt.format(V[r, c])
            line += cell
            if c < cols - 1:
                line += " "
            c += 1
        print(line)
        r += 1


def sample_next(trans: list[tuple[tuple[int, int], float]]) -> tuple[int, int]:
    """Muestrea un siguiente estado según una distribución discreta.

    Args:
        trans (list[tuple[tuple[int,int],float]]): Lista (estado, prob).

    Returns:
        tuple[int,int]: Estado muestreado.

    """
    x = random.random()
    acc = 0.0
    i = 0
    chosen = trans[len(trans) - 1][0]
    while i < len(trans):
        ns, p = trans[i]
        acc += float(p)
        if x <= acc:
            chosen = ns
            i = len(trans)
        else:
            i += 1
    return chosen


def _format_trans(trans: list[tuple[tuple[int, int], float]]) -> str:
    """Formatea una distribución de transición para imprimirla.

    Args:
        trans (list[tuple[tuple[int,int],float]]): Distribución.

    Returns:
        str: Texto legible con estados y probabilidades.

    """
    out = ""
    i = 0
    while i < len(trans):
        ns, p = trans[i]
        piece = f"{ns}:{p:.2f}"
        if out == "":
            out = piece
        else:
            out = out + " | " + piece
        i += 1
    return out


def simulate(
    world: dict,
    policy: dict,
    episodes: int = 3,
    max_steps: int = 200,
    verbose: bool = True,
) -> dict:
    """Simula partidas siguiendo la política óptima y devuelve métricas.

    Qué se considera "puntos":
    -Es el retorno acumulado
    -Si discount=1.0: suma simple de recompensas
    -Si discount<1.0: suma descontada discount^t * r_t

    Al final se imprime:
    -Éxitos/total
    -Media de puntos
    -Pasos medios

    Args:
        world (dict): Mundo.
        policy (dict): Política.
        episodes (int): Número de partidas.
        max_steps (int): Máximo de pasos por partida.
        verbose (bool): Si True, imprime paso a paso.

    Returns:
        dict: Métricas del experimento.

    """
    discount = float(world["discount"])

    total_points = 0.0
    total_steps = 0
    success = 0

    ep = 1
    while ep <= int(max(1, episodes)):
        s = world["start"]
        points = 0.0
        steps = 0

        print("")
        print(color(f"Episodio {ep}:", "bold"))
        if verbose:
            print_world(world, agent=s, title="Estado inicial")

        finished = False
        while (steps < int(max_steps)) and (not finished):
            if is_terminal(world, s):
                finished = True
            else:
                a = policy.get(s, None)
                if a is None:
                    finished = True
                else:
                    trans = transition_probs(world, s, a)
                    ns = sample_next(trans)
                    r = reward(world, s, a, ns)
                    points += (discount ** steps) * r

                    if verbose:
                        txt = f"Paso {steps + 1} | s={s} | a={a}({ARROW[a]}) | trans={_format_trans(trans)} | ns={ns} | r={r:.2f}"
                        print(txt)
                        print_world(world, agent=ns, title="Tras el paso")

                    s = ns
                    steps += 1

        total_points += points
        total_steps += steps

        ok = (s == world["exit"])
        if ok:
            success += 1

        if ok:
            print(color("Resultado: ÉXITO (llega a la salida).", "green"))
        else:
            if world["deadly_islands"] and (s in world["islands"]):
                print(color("Resultado: FALLO (entra en isla peligrosa).", "red"))
            else:
                print(color("Resultado: FALLO (no llega a la salida).", "red"))

        print(f"Puntos: {points:.3f}")
        print(f"Pasos: {steps}")

        ep += 1

    denom = float(int(max(1, episodes)))
    avg_points = total_points / denom
    avg_steps = total_steps / denom

    print("")
    print(color("Resumen final de simulación:", "bold"))
    print(f"Éxitos: {success}/{int(max(1, episodes))}")
    print(f"Media de puntos: {avg_points:.3f}")
    print(f"Pasos medios: {avg_steps:.2f}")

    return {"success": success, "episodes": int(max(1, episodes)), "avg_points": avg_points, "avg_steps": avg_steps}


def _policy_stats(world: dict, policy: dict) -> dict:
    """Cuenta cuántas veces aparece cada acción en la política.

    Args:
        world (dict): Mundo.
        policy (dict): Política.

    Returns:
        dict: Conteos de acciones.

    """
    counts = {"up": 0, "down": 0, "left": 0, "right": 0, "stay": 0, "none": 0}
    rows, cols = world["rows"], world["cols"]
    r = 0
    while r < rows:
        c = 0
        while c < cols:
            s = (r, c)
            if (not world["deadly_islands"]) and (s in world["islands"]):
                c += 1
            else:
                a = policy.get(s, None)
                if a is None:
                    counts["none"] += 1
                else:
                    counts[a] += 1
                c += 1
        r += 1
    return counts


def print_analysis(world: dict, V: np.ndarray, policy: dict) -> None:
    """Imprime un análisis breve para entender la política y la corriente.

    Args:
        world (dict): Mundo.
        V (np.ndarray): Valores.
        policy (dict): Política.

    """
    print("")
    print(color("Análisis rápido:", "bold"))

    strengths = world["river_strength"]
    cols = world["cols"]

    print("Corriente por columna (j):")
    j = 0
    while j < cols:
        print(f"  j={j}: river_strength={strengths[j]}")
        j += 1

    print("")
    print("Lectura intuitiva:")
    print("Cuando river_strength(j) es alto, muchas acciones (que no sean down) tienen bastante probabilidad de acabar bajando.")
    print("Eso puede hacer que la política elija rutas que minimicen el riesgo de quedar mal colocado por el empuje.")

    stats = _policy_stats(world, policy)
    print("")
    print("Acciones en la politica (conteo en la rejilla):")
    for k in ["up", "down", "left", "right", "stay", "none"]:
        print(f"  {k}: {stats[k]}")


def _print_config_explanation() -> None:
    """Explica al usuario qué está configurando, de forma clara."""
    print("")
    print(color("Antes de empezar:", "bold"))
    print("Vas a crear un mundo del río y resolverlo con Value Iteration.")
    print("Se usan colores siempre para que el mapa se lea mejor.")
    print("")
    print("Cosas que se configuran:")
    print("  Semilla: si la das, el mapa será reproducible; si no, será aleatorio.")
    print("  Tamaño: por defecto 7x6.")
    print("  Número de islas: se colocan en el interior. Si pides más de las que caben, todo lo que no sea perímetro será isla.")
    print("  Descuento (extra): número en (0,1]. Con 1.0 no hay descuento.")
    print("  Islas peligrosas (extra): si lo activas, entrar en una isla termina la partida con penalización.")


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


def main() -> None:
    """Ejecuta el flujo completo: crear mundo, resolver, imprimir y simular."""
    print(color("MDP del río", "bold"))
    _print_config_explanation()

    seed = ask_int_or_none("Semilla (ENTER=aleatoria): ")

    rows = 7
    cols = 6

    use_default = ask_yes_no("¿Usar tamaño 7x6? (ENTER=s): ", True)

    if not use_default:
        print("Vas a cambiar el tamaño del mapa.")
        print("Consejo práctico: para que tenga sentido como 'río', suele interesar cols>=3.")
        rows = ask_int("Filas (mínimo 2, ENTER=7): ", 7, 2, None)
        cols = ask_int("Columnas (mínimo 2, ENTER=6): ", 6, 2, None)

    interior_cap = max(0, (rows - 2) * (cols - 2))
    if interior_cap == 0:
        print("Aviso: con este tamaño no existe interior, así que no se podrán colocar islas interiores.")
    else:
        print(f"Interior disponible para islas: {interior_cap} celdas (todo lo que no es perímetro).")

    n_islands = 2
    if interior_cap > 0:
        n_islands = ask_int("Número de islas (ENTER=2): ", 2, 0, None)

    if interior_cap > 0 and n_islands >= interior_cap:
        print("Has pedido tantas islas que el interior no da para más.")
        print("Se aplicará la regla: todo el interior será isla y el perímetro quedará libre.")

    print("")
    print("Descuento (extra):")
    print(" 1.0 significa que sumas recompensas sin descuento.")
    print(" Un valor menor reduce el peso de recompensas lejanas en el tiempo.")
    discount = ask_float("Factor de descuento en (0,1] (ENTER=1.0): ", 1.0, 0.0000001, 1.0)

    print("")
    print("Islas peligrosas (extra):")
    print(" Si NO: las islas son obstáculo y no se puede entrar.")
    print(" Si SÍ: se puede entrar, pero al entrar termina la partida con penalización.")
    deadly_islands = ask_yes_no("¿Activar islas peligrosas? (ENTER=n): ", False)

    world = make_river_world(
        rows=rows,
        cols=cols,
        seed=seed,
        n_islands=n_islands,
        min_strength=0.06,
        max_strength=0.94,
        step_cost=-1.0,
        reward_exit=100.0,
        reward_island=-100.0,
        discount=discount,
        deadly_islands=deadly_islands,
    )

    print("")
    print_legend(world)
    print_world(world, agent=world["start"], title="Mapa generado")

    print("")
    print(color("Value Iteration:", "bold"))
    print("Se repetirá la actualización de V hasta que el cambio máximo (delta) sea muy pequeño.")
    show_progress = ask_yes_no("¿Mostrar deltas de convergencia? (ENTER=s): ", True)
    V, policy, info = value_iteration(world, theta=1e-6, max_iter=20000, show_progress=show_progress)

    print("")
    print(f"Convergencia: iteraciones={info['iterations']} | delta_final={info['delta']:.3e} | convergido={info['converged']}")
    if (not info["converged"]) and float(world["discount"]) >= 0.999999:
        print("Aviso: con descuento=1.0 puede ocurrir que delta no baje de theta dentro del máximo de iteraciones.")
        print("Si quieres una convergencia más estable, prueba con descuento 0.99 o 0.95 (sigue siendo muy parecido a no descontar).")

    print_values(world, V, decimals=1)
    print_policy(world, policy)
    print_analysis(world, V, policy)

    print("")
    episodes = ask_int("Número de episodios a simular (ENTER=3): ", 3, 1, None)
    verbose = ask_yes_no("¿Imprimir cada paso de la simulación? (ENTER=s): ", True)
    simulate(world, policy, episodes=episodes, max_steps=200, verbose=verbose)


if __name__ == "__main__":
    enable_utf8_output()
    main()
