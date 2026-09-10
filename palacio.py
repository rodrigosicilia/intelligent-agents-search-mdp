#palacio.py
#Parte 2 - Palacio Bayesiano (FIA)



import math
import random
import sys

import numpy as np

import kurtz_colors as kc

kc.USE_COLOR = True



#Parámetros por defecto


DEFAULT_N = 6
DEFAULT_RISK_CUTOFF = 0.20
DEFAULT_SEED = None

#Para pintar "?" como candidato, pedimos que (1) se haya visto ese estímulo alguna vez y (2) destaque.
HINT_THRESHOLD = 0.20

EPS_SURE = 1e-12

TRAPS = ["F", "P", "D"]
NONTRAP = ["M", "S", "CK"]
ALL_TAU = TRAPS + NONTRAP

DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
KEY_TO_DIR = {"w": "U", "s": "D", "a": "L", "d": "R"}
ARROW = {"U": "^", "D": "v", "L": "<", "R": ">"}



#Helpers básicos


def ask_yes_no(prompt, default=True):
    """Pregunta al usuario una confirmación (sí/no) por consola.
    
        Args:
            prompt (str): Texto que se muestra al pedir la respuesta.
            default (bool): Valor que se devuelve si el usuario pulsa Enter sin escribir nada.
    
        Returns:
            bool: True si la respuesta es afirmativa, False si es negativa.
        
    """
    while True:
        ans = input(prompt).strip().lower()
        if ans == "":
            return default
        if ans in ("s", "si", "sí", "y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Responde con s/n (o enter para valor por defecto).")


def ask_choice(prompt, choices, default=None):
    """Pide al usuario que elija una opción entre un conjunto, ignorando mayúsculas.
    
        Args:
            prompt (str): Texto que se muestra al pedir la opción.
            choices (list[str] | tuple[str, ...]): Opciones válidas.
            default (str | None): Opción por defecto si el usuario pulsa Enter.
    
        Returns:
            str: Opción elegida, siempre en minúsculas.
        
    """
    choices_lc = [c.lower() for c in choices]
    default_lc = None if default is None else default.lower()

    while True:
        txt = input(prompt).strip().lower()
        if txt == "" and default_lc is not None:
            return default_lc
        if txt in choices_lc:
            return txt
        print(f"Opción no válida. Opciones: {', '.join(choices_lc)}")


def ask_int(prompt, default=None, min_value=None, max_value=None):
    """Pide un entero por consola y vuelve a preguntar mientras no sea válido.

        Args:
            prompt (str): Texto que se muestra al pedir el número.
            default (int | None): Valor que se devuelve si el usuario pulsa Enter.
            min_value (int | None): Mínimo permitido (inclusive).
            max_value (int | None): Máximo permitido (inclusive).

        Returns:
            int: Entero válido dentro del rango pedido.

    """
    while True:
        txt = input(prompt).strip()

        if txt == "":
            if default is None:
                print("Debes introducir un número entero.")
                continue
            val = int(default)
        else:
            try:
                val = int(txt)
            except ValueError:
                print("Entrada no válida: escribe un número entero (o enter para el valor por defecto).")
                continue

        if min_value is not None and val < min_value:
            print(f"Valor fuera de rango: debe ser >= {min_value}.")
            continue
        if max_value is not None and val > max_value:
            print(f"Valor fuera de rango: debe ser <= {max_value}.")
            continue

        return val


def ask_float(prompt, default=None, min_value=None, max_value=None):
    """Pide un número decimal por consola y vuelve a preguntar mientras no sea válido.

        Args:
            prompt (str): Texto que se muestra al pedir el número.
            default (float | None): Valor que se devuelve si el usuario pulsa Enter.
            min_value (float | None): Mínimo permitido (inclusive).
            max_value (float | None): Máximo permitido (inclusive).

        Returns:
            float: Número válido dentro del rango pedido.

    """
    while True:
        txt = input(prompt).strip()

        if txt == "":
            if default is None:
                print("Debes introducir un número.")
                continue
            val = float(default)
        else:
            try:
                val = float(txt)
            except ValueError:
                print("Entrada no válida: escribe un número (ej: 0.25) o pulsa enter para el valor por defecto.")
                continue
            if not math.isfinite(val):
                print("Entrada no válida: escribe un número finito.")
                continue

        if min_value is not None and val < min_value:
            print(f"Valor fuera de rango: debe ser >= {min_value}.")
            continue
        if max_value is not None and val > max_value:
            print(f"Valor fuera de rango: debe ser <= {max_value}.")
            continue

        return val


def in_bounds(n, r, c):
    """Comprueba si una posición (fila, columna) está dentro del tablero.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            r (int): Índice de fila (0-indexado).
            c (int): Índice de columna (0-indexado).
    
        Returns:
            bool: True si (r, c) está dentro de los límites; False en caso contrario.
        
    """
    return 0 <= r < n and 0 <= c < n


def neighbors4(n, pos):
    """Devuelve las celdas adyacentes en 4 direcciones (arriba, abajo, izquierda, derecha).
    
        Args:
            n (int): Tamaño del tablero (n x n).
            pos (tuple[int, int]): Posición actual (fila, columna), 0-indexada.
    
        Returns:
            list[tuple[int, int]]: Lista de vecinos válidos dentro del tablero.
        
    """
    r, c = pos
    out = []
    for d in DIRS:
        dr, dc = DIRS[d]
        rr, cc = r + dr, c + dc
        if in_bounds(n, rr, cc):
            out.append((rr, cc))
    return out


def adj_plus_self(n, pos):
    """Devuelve la vecindad 4 de una celda incluyendo la propia celda.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            pos (tuple[int, int]): Posición (fila, columna), 0-indexada.
    
        Returns:
            list[tuple[int, int]]: Vecinos 4 válidos más la propia celda.
        
    """
    out = neighbors4(n, pos)
    out.append(pos)
    return out


def manhattan(a, b):
    """Calcula la distancia Manhattan entre dos celdas.
    
        Args:
            a (tuple[int, int]): Primera celda (fila, columna), 0-indexada.
            b (tuple[int, int]): Segunda celda (fila, columna), 0-indexada.
    
        Returns:
            int: Distancia Manhattan |a_r-b_r| + |a_c-b_c|.
        
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def fmt_cell(text, width):
    """Formatea una celda a ancho fijo.
    
        Args:
            text (Any): Contenido a mostrar en la celda (se convierte a str).
            width (int): Ancho objetivo de la celda.
    
        Returns:
            str: Texto centrado y recortado a `width` caracteres.
        
    """
    t = str(text)
    if len(t) > width:
        t = t[:width]
    pad = width - len(t)
    left = pad // 2
    right = pad - left
    return (" " * left) + t + (" " * right)


def paint(text, color_code):
    """Aplica color a un texto si el modo de color está habilitado.
    
        Args:
            text (str): Texto a colorear.
            color_code (str): Código de color (según `kurtz_colors`).
    
        Returns:
            str: Texto original o texto coloreado, según la configuración.
        
    """
    if not kc.USE_COLOR:
        return text
    return kc.paint(text, color_code)


def apply_zero_cells(g, cells):
    """Pone a cero (probabilidad 0) un conjunto de celdas en una cuadrícula.
    
        Args:
            g (np.ndarray): Cuadrícula numérica (típicamente de probabilidades).
            cells (Iterable[tuple[int, int]]): Celdas (r, c) que se deben anular.
    
        Returns:
            np.ndarray: La misma cuadrícula `g`, tras aplicar los ceros.
        
    """
    for (r, c) in cells:
        g[r, c] = 0.0
    return g


def normalize_grid(g, fallback_mask=None):
    """Normaliza una cuadrícula para que su suma total sea 1, con manejo de casos degenerados.
    
        Args:
            g (np.ndarray): Cuadrícula a normalizar.
            fallback_mask (np.ndarray | None): Máscara booleana (o 0/1) usada como soporte alternativo
                si la suma de `g` queda en 0.
    
        Returns:
            np.ndarray: Cuadrícula normalizada (o sin cambios si no es posible normalizar).
    
        Notes:
            Si `np.sum(g) == 0` y se proporciona `fallback_mask`, se normaliza la máscara como distribución
            uniforme sobre las celdas permitidas por dicha máscara.
        
    """
    s = float(np.sum(g))
    if s > 0.0:
        return g / s

    #Caso degenerado: si el posterior queda imposible (suma 0),
    #hacemos fallback a una máscara (pero OJO: respetando prohibiciones).
    if fallback_mask is None:
        return g

    m = fallback_mask.astype(float)
    ms = float(np.sum(m))
    if ms == 0.0:
        return g
    return m / ms


def snap_onehot_if_forced(g):
    """Fuerza una distribución one-hot cuando la incertidumbre ya está resuelta.
    
        Args:
            g (np.ndarray): Cuadrícula de probabilidades.
    
        Returns:
            np.ndarray: Si solo queda una celda posible (o el máximo es ~1), devuelve una one-hot exacta.
        
    """
    nz = np.argwhere(g > 0.0)
    if nz.shape[0] == 1:
        rr, cc = int(nz[0, 0]), int(nz[0, 1])
        out = np.zeros_like(g)
        out[rr, cc] = 1.0
        return out

    m = float(np.max(g))
    if m >= 1.0 - EPS_SURE:
        rr, cc = np.unravel_index(int(np.argmax(g)), g.shape)
        out = np.zeros_like(g)
        out[rr, cc] = 1.0
        return out

    return g


def delta_at(n, cell):
    """Crea una distribución delta (one-hot) en una celda concreta.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            cell (tuple[int, int]): Celda (fila, columna) donde colocar la masa de probabilidad.
    
        Returns:
            np.ndarray: Cuadrícula con 1.0 en `cell` y 0.0 en el resto.
        
    """
    g = np.zeros((n, n), dtype=float)
    r, c = cell
    g[r, c] = 1.0
    return g



#Mundo


def make_world(n, rng, start):
    """Genera un mundo aleatorio válido según las reglas del enunciado.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            rng (random.Random): Generador de números pseudoaleatorios.
            start (tuple[int, int]): Celda inicial del capitán (debe estar vacía).
    
        Returns:
            dict: Estructura con la configuración del mundo (posiciones de trampas, militar, salida y Kurtz).
    
        Notes:
            - Hay exactamente una trampa de cada tipo (F, P, D) y pueden coincidir entre sí.
            - M, S y CK no pueden estar en una celda con trampa, pero sí pueden coincidir entre ellos.
            - La celda `start` siempre queda libre.
        
    """
    all_cells = [(r, c) for r in range(n) for c in range(n)]

    traps_pos = {}
    for t in TRAPS:
        choices = [p for p in all_cells if p != start]
        traps_pos[t] = choices[rng.randrange(len(choices))]

    trap_cells = set(traps_pos[t] for t in TRAPS)

    safe_choices = [p for p in all_cells if p != start and p not in trap_cells]
    m_pos = safe_choices[rng.randrange(len(safe_choices))]
    s_pos = safe_choices[rng.randrange(len(safe_choices))]
    ck_pos = safe_choices[rng.randrange(len(safe_choices))]

    return {
        "n": n,
        "start": start,
        "traps": traps_pos,     #{"F":(r,c),...}
        "trap_cells": trap_cells,
        "M": m_pos,
        "S": s_pos,
        "CK": ck_pos,
    }



#Perceptos (PDF)


def percept_at(world, pos, soldier_alive, grito_flag):
    """Calcula el percepto del agente en una posición, siguiendo el modelo determinista del PDF.
    
        Args:
            world (dict): Mundo (tablero y posiciones de elementos).
            pos (tuple[int, int]): Posición actual del capitán (fila, columna), 0-indexada.
            soldier_alive (bool): Indica si el militar sigue vivo (afecta a e^M).
            grito_flag (bool): Si True, añade el percepto puntual de "Grito".
    
        Returns:
            dict: Diccionario con estímulos (eF/eP/eD/eM/eS), paredes y grito.
        
    """
    n = world["n"]
    zone = set(adj_plus_self(n, pos))

    eF = 1 if world["traps"]["F"] in zone else 0
    eP = 1 if world["traps"]["P"] in zone else 0
    eD = 1 if world["traps"]["D"] in zone else 0

    eM = 0
    if soldier_alive:
        eM = 1 if world["M"] in zone else 0

    eS = 1 if world["S"] in zone else 0

    r, c = pos
    wall_up = 1 if r == 0 else 0
    wall_dn = 1 if r == n - 1 else 0
    wall_lt = 1 if c == 0 else 0
    wall_rt = 1 if c == n - 1 else 0

    return {
        "eF": eF, "eP": eP, "eD": eD,
        "eM": eM, "eS": eS,
        "Pared_arriba": wall_up,
        "Pared_abajo": wall_dn,
        "Pared_izq": wall_lt,
        "Pared_dcha": wall_rt,
        "Grito": 1 if grito_flag else 0,
    }


def percept_to_string(per):
    """Convierte un percepto (diccionario) a una representación legible en una sola línea.
    
        Args:
            per (dict): Percepto devuelto por `percept_at`.
    
        Returns:
            str: Cadena con los campos del percepto formateados.
        
    """
    parts = [
        f"e^F={per['eF']}", f"e^P={per['eP']}", f"e^D={per['eD']}",
        f"e^M={per['eM']}", f"e^S={per['eS']}",
        f"Pared_arriba (^)={per['Pared_arriba']}",
        f"Pared_abajo (v)={per['Pared_abajo']}",
        f"Pared_izq (<)={per['Pared_izq']}",
        f"Pared_dcha (>)={per['Pared_dcha']}",
        f"Grito={per['Grito']}",
    ]
    return "[" + ", ".join(parts) + "]"


def active_stimuli(per):
    """Lista los estímulos y señales activas presentes en un percepto.
    
        Args:
            per (dict): Percepto devuelto por `percept_at`.
    
        Returns:
            list[str]: Etiquetas de los estímulos activos (incluye paredes y grito si aplica).
        
    """
    out = []
    if per["eF"] == 1:
        out.append("e^F")
    if per["eP"] == 1:
        out.append("e^P")
    if per["eD"] == 1:
        out.append("e^D")
    if per["eM"] == 1:
        out.append("e^M")
    if per["eS"] == 1:
        out.append("e^S")

    if per["Pared_arriba"] == 1:
        out.append("Pared_arriba(^)")
    if per["Pared_abajo"] == 1:
        out.append("Pared_abajo(v)")
    if per["Pared_izq"] == 1:
        out.append("Pared_izq(<)")
    if per["Pared_dcha"] == 1:
        out.append("Pared_dcha(>)")

    if per["Grito"] == 1:
        out.append("Grito")
    return out


def cw_tag(per, kurtz_found, on_exit):
    """Construye la etiqueta de la celda actual (CW/CWK/CWS/CWKS) con sufijo de estímulos.
    
        Args:
            per (dict): Percepto actual.
            kurtz_found (bool): True si el capitán lleva a Kurtz.
            on_exit (bool): True si el capitán está sobre la salida.
    
        Returns:
            str: Etiqueta base (CW...) con sufijo opcional tipo "_eFeP..." si hay estímulos.
        
    """
    base = "CW"
    if kurtz_found:
        base += "K"
    if on_exit:
        base += "S"

    stim = []
    if per["eF"] == 1:
        stim.append("eF")
    if per["eP"] == 1:
        stim.append("eP")
    if per["eD"] == 1:
        stim.append("eD")
    if per["eM"] == 1:
        stim.append("eM")
    if per["eS"] == 1:
        stim.append("eS")

    if len(stim) == 0:
        return base
    return base + "_" + "".join(stim)



#Bayes (likelihood 0/1)


def feasible_mask_for_evidence(n, pos, evidence_is_present):
    """Construye una máscara de celdas compatibles con una evidencia (likelihood 0/1).
    
        Args:
            n (int): Tamaño del tablero (n x n).
            pos (tuple[int, int]): Celda de referencia donde se observa la evidencia.
            evidence_is_present (bool): True si se observa el estímulo; False si no se observa.
    
        Returns:
            np.ndarray: Máscara 0/1 con las celdas compatibles con la evidencia.
    
        Notes:
            - Si e=1, el elemento debe estar en Adj(pos) ∪ {pos}.
            - Si e=0, el elemento no puede estar en ese conjunto.
        
    """
    zone = adj_plus_self(n, pos)
    mask = np.ones((n, n), dtype=float)

    if evidence_is_present:
        mask[:] = 0.0
        for (rr, cc) in zone:
            mask[rr, cc] = 1.0
    else:
        for (rr, cc) in zone:
            mask[rr, cc] = 0.0

    return mask


def init_beliefs(n, start):
    """Inicializa las creencias a priori como distribuciones uniformes fuera de la celda inicial.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            start (tuple[int, int]): Celda inicial (se asigna probabilidad 0).
    
        Returns:
            dict[str, np.ndarray]: Diccionario `tau -> grid` para cada entidad (F, P, D, M, S, CK).
        
    """
    mask = np.ones((n, n), dtype=float)
    mask[start[0], start[1]] = 0.0
    base = normalize_grid(mask.copy(), fallback_mask=mask)

    beliefs = {}
    for tau in ALL_TAU:
        beliefs[tau] = base.copy()
    return beliefs


def apply_bayes_step(prior, mask, forbidden_cells):
    """Aplica un paso de actualización bayesiana con verosimilitud determinista (0/1).
    
        Args:
            prior (np.ndarray): Distribución a priori sobre posiciones.
            mask (np.ndarray): Máscara 0/1 que representa la evidencia (likelihood).
            forbidden_cells (set[tuple[int, int]]): Celdas prohibidas (probabilidad 0 como evidencia dura).
    
        Returns:
            np.ndarray: Distribución posterior normalizada tras aplicar evidencia y prohibiciones.
    
        Notes:
            Si la evidencia deja la distribución sin masa (suma 0), se aplica un fallback conservador:
            se mantiene el prior (respetando prohibiciones) y se renormaliza sin "resucitar" celdas descartadas.
        
    """
    g = prior * mask
    g = apply_zero_cells(g, forbidden_cells)

    s = float(np.sum(g))
    if s <= 0.0:
        #Fallback conservador: conservar lo ya aprendido (prior + prohibiciones).
        g = prior.copy()
        g = apply_zero_cells(g, forbidden_cells)
        g = normalize_grid(g, fallback_mask=(g > 0).astype(float))
        g = snap_onehot_if_forced(g)
        return g

    g = g / s
    g = snap_onehot_if_forced(g)
    return g


def trap_certain_mask(beliefs):
    """Calcula una máscara booleana de celdas donde alguna trampa es prácticamente segura (p≈1).
    
        Args:
            beliefs (dict[str, np.ndarray]): Creencias actuales.
    
        Returns:
            np.ndarray: Máscara booleana (n x n) con True donde F o P o D tienen probabilidad ~1.
        
    """
    return ((beliefs["F"] >= 1.0 - EPS_SURE) |
            (beliefs["P"] >= 1.0 - EPS_SURE) |
            (beliefs["D"] >= 1.0 - EPS_SURE))


def enforce_no_trap_for_entity(entity_grid, trap_certain):
    """Impone la restricción dura: una entidad no-trampa no puede estar donde hay trampa segura.
    
        Args:
            entity_grid (np.ndarray): Distribución de la entidad (M, S o CK).
            trap_certain (np.ndarray): Máscara booleana donde alguna trampa es segura.
    
        Returns:
            np.ndarray: Distribución re-normalizada tras anular celdas incompatibles.
        
    """
    g = entity_grid.copy()
    g[trap_certain] = 0.0
    g = normalize_grid(g, fallback_mask=(g > 0).astype(float))
    g = snap_onehot_if_forced(g)
    return g


def enforce_entity_not_on_traps_soft(entity_grid, beliefs):
    """Impone la incompatibilidad de forma suave reponderando por P(no_trampa).
    
        Args:
            entity_grid (np.ndarray): Distribución de la entidad (M, S o CK).
            beliefs (dict[str, np.ndarray]): Creencias completas (para obtener pF/pP/pD).
    
        Returns:
            np.ndarray: Distribución re-normalizada tras penalizar celdas con alta probabilidad de trampa.
    
        Notes:
            Se utiliza el supuesto de independencia entre F, P y D, igual que en `trap_union_prob`:
            P(no_trampa) = (1-pF)(1-pP)(1-pD).
        
    """
    no_trap = (1.0 - beliefs["F"]) * (1.0 - beliefs["P"]) * (1.0 - beliefs["D"])
    g = entity_grid * no_trap
    g = normalize_grid(g, fallback_mask=(g > 0).astype(float))
    g = snap_onehot_if_forced(g)
    return g



def bayes_nontrap_location_weight(beliefs, start):
    """Calcula el factor bayesiano que impone que (M, S, CK) no pueden estar en trampas.

        Args:
            beliefs (dict[str, np.ndarray]): Creencias actuales, incluyendo F/P/D.
            start (tuple[int, int]): Celda inicial (se excluye del soporte, como en el prior).

        Returns:
            np.ndarray: Cuadrícula W(c) proporcional a P(c es elegible para una entidad no-trampa),
            integrando (marginalizando) sobre las posiciones posibles de las tres trampas.

        Notes:
            El modelo implícito es generativo:
              1) Se muestrean las posiciones de F, P y D (pueden coincidir).
              2) Condicionado a esas trampas, una entidad no-trampa τ∈{M,S,CK} se coloca uniforme
                 entre las celdas seguras (sin trampas) y distintas de la inicial.

            Por tanto, el término que repondera una celda c es:

                W(c) =  Σ_{a,b,d}  Bel_F(a) Bel_P(b) Bel_D(d) *  𝟙[c ∉ {a,b,d}] / (N-1-|{a,b,d}|)

            donde N = n·n y |{a,b,d}| es el número de celdas distintas ocupadas por las trampas
            en esa combinación (1, 2 o 3 si coinciden o no). Este factor es el que hace el
            tratamiento completamente bayesiano cuando las trampas pueden compartir celda.
    """
    n = beliefs["F"].shape[0]
    N = n * n

    start_idx = start[0] * n + start[1]

    pF = beliefs["F"].reshape(-1)
    pP = beliefs["P"].reshape(-1)
    pD = beliefs["D"].reshape(-1)

    #W en formato plano para poder aplicar actualizaciones O(1) por combinación.
    w = np.zeros(N, dtype=float)

    for a in range(N):
        pa = float(pF[a])
        if pa == 0.0:
            continue
        for b in range(N):
            pb = float(pP[b])
            if pb == 0.0:
                continue
            pab = pa * pb
            for d in range(N):
                pd = float(pD[d])
                if pd == 0.0:
                    continue

                prob = pab * pd
                #Número de celdas distintas ocupadas por trampas en esta combinación.
                #OJO: pueden coincidir, y eso cambia el denominador.
                traps = {a, b, d}
                k = len(traps)
                denom = (N - 1 - k)
                if denom <= 0:
                    continue

                inc = prob / float(denom)

                #Añadimos masa uniforme a todas las celdas elegibles (todas menos start),
                #y luego restamos las celdas que están ocupadas por trampas.
                w += inc
                w[start_idx] -= inc
                for t in traps:
                    w[t] -= inc

    w = w.reshape((n, n))
    #Si por algún motivo queda todo a 0, devolvemos una máscara uniforme fuera del start.
    w = normalize_grid(w, fallback_mask=(w > 0).astype(float))
    return w


def apply_nontrap_constraint_bayes(entity_grid, w_nontrap):
    """Aplica la restricción bayesiana de "no puede estar en una trampa" a una entidad no-trampa.

        Args:
            entity_grid (np.ndarray): Distribución de la entidad (M, S o CK), ya actualizada por evidencia.
            w_nontrap (np.ndarray): Factor W(c) de `bayes_nontrap_location_weight`.

        Returns:
            np.ndarray: Distribución re-normalizada tras reponderar por W(c).
    """
    g = entity_grid * w_nontrap
    g = normalize_grid(g, fallback_mask=(g > 0).astype(float))
    g = snap_onehot_if_forced(g)
    return g



def update_beliefs(world, beliefs, pos, visited, per,
                   soldier_alive, soldier_dead,
                   soldier_forbidden,
                   fixed_exit, fixed_kurtz):
    """Actualiza las creencias (posteriors) a partir del percepto actual y restricciones del problema.
    
        Args:
            world (dict): Mundo (incluye tamaño y posiciones reales).
            beliefs (dict[str, np.ndarray]): Diccionario `tau -> grid` con las creencias actuales.
            pos (tuple[int, int]): Posición actual del capitán.
            visited (Iterable[tuple[int, int]]): Celdas ya visitadas (se consideran prohibidas para elementos ocultos).
            per (dict): Percepto observado en `pos`.
            soldier_alive (bool): Indica si el militar sigue vivo.
            soldier_dead (bool): Indica si el militar ha sido neutralizado.
            soldier_forbidden (Iterable[tuple[int, int]]): Celdas descartadas para el militar (por granada fallida).
            fixed_exit (bool): Si True, fija S a la posición real (ya descubierta).
            fixed_kurtz (bool): Si True, fija CK a la posición real (ya rescatado).
    
        Returns:
            dict[str, np.ndarray]: El diccionario de creencias actualizado.
    
        Notes:
            Se actualizan F/P/D usando e^F/e^P/e^D (más prohibición de celdas visitadas).
            Para M y S se usan e^M y e^S respectivamente. Para CK (sin estímulo) se descartan visitadas.
            Finalmente se aplican restricciones de incompatibilidad entre (M,S,CK) y trampas.
        
    """
    n = world["n"]
    visited_cells = set(visited)

    if fixed_exit:
        beliefs["S"] = delta_at(n, world["S"])
    if fixed_kurtz:
        beliefs["CK"] = delta_at(n, world["CK"])

    if soldier_dead:
        beliefs["M"] = np.zeros((n, n), dtype=float)

    #Trampas (PDF literal)
    for t, key in [("F", "eF"), ("P", "eP"), ("D", "eD")]:
        m = feasible_mask_for_evidence(n, pos, per[key] == 1)
        beliefs[t] = apply_bayes_step(beliefs[t], m, visited_cells)

    #Militar
    if (not soldier_dead) and soldier_alive:
        mM = feasible_mask_for_evidence(n, pos, per["eM"] == 1)
        forb = set(visited_cells) | set(soldier_forbidden)
        beliefs["M"] = apply_bayes_step(beliefs["M"], mM, forb)

    #Salida
    if not fixed_exit:
        mS = feasible_mask_for_evidence(n, pos, per["eS"] == 1)
        beliefs["S"] = apply_bayes_step(beliefs["S"], mS, visited_cells)

    #Kurtz (sin estímulo)
    if not fixed_kurtz:
        g = beliefs["CK"].copy()
        g = apply_zero_cells(g, visited_cells)
        g = normalize_grid(g, fallback_mask=(g > 0).astype(float))
        g = snap_onehot_if_forced(g)
        beliefs["CK"] = g



    #Restricción del PDF (bayesiana): M/S/CK no pueden ocupar una celda con trampa.
    #En vez de "capar" celdas por heurística, reponderamos con el factor W(c) derivado
    #de marginalizar sobre (F,P,D) permitiendo coincidencias (ver `bayes_nontrap_location_weight`).
    w_nontrap = bayes_nontrap_location_weight(beliefs, world["start"])

    if (not soldier_dead) and soldier_alive:
        beliefs["M"] = apply_nontrap_constraint_bayes(beliefs["M"], w_nontrap)
    if not fixed_exit:
        beliefs["S"] = apply_nontrap_constraint_bayes(beliefs["S"], w_nontrap)
    if not fixed_kurtz:
        beliefs["CK"] = apply_nontrap_constraint_bayes(beliefs["CK"], w_nontrap)

    return beliefs



#Mapas derivados (riesgo)


def trap_union_prob(beliefs):
    """Calcula P(hay al menos una trampa en la celda), asumiendo independencia entre F, P y D.
    
        Args:
            beliefs (dict[str, np.ndarray]): Creencias actuales (incluye grids de F, P y D).
    
        Returns:
            np.ndarray: Cuadrícula con P(F ∪ P ∪ D) para cada celda.
        
    """
    pF, pP, pD = beliefs["F"], beliefs["P"], beliefs["D"]
    return 1.0 - (1.0 - pF) * (1.0 - pP) * (1.0 - pD)


def death_risk_union(beliefs, soldier_dead):
    """Calcula el riesgo de morir al pisar una celda (trampa o militar), respetando incompatibilidades.
    
        Args:
            beliefs (dict[str, np.ndarray]): Creencias actuales.
            soldier_dead (bool): Si True, el riesgo por militar se considera 0.
    
        Returns:
            np.ndarray: Cuadrícula con P(muerte) al entrar en cada celda (acotada a 1.0).
    
        Notes:
            Dado que M no puede coexistir con trampas, el modelo usa:
            P(muerte) = P(trampa) + P(militar), con saturación a 1.
        
    """
    pTrap = trap_union_prob(beliefs)
    pM = np.zeros_like(beliefs["M"]) if soldier_dead else beliefs["M"]
    return np.minimum(1.0, pTrap + pM)


def trap_heat_sum(beliefs):
    """Construye un mapa de "calor" intuitivo sumando probabilidades marginales de trampas.
    
        Args:
            beliefs (dict[str, np.ndarray]): Creencias actuales (incluye F, P y D).
    
        Returns:
            np.ndarray: Cuadrícula con p(F)+p(P)+p(D) por celda.
        
    """
    return beliefs["F"] + beliefs["P"] + beliefs["D"]



#Tablero (estilo parte 1)


def seen_update(seen, per):
    """Actualiza el registro de estímulos que ya se han observado alguna vez.
    
        Args:
            seen (dict[str, bool]): Diccionario con claves eF/eP/eD/eM/eS.
            per (dict): Percepto observado.
    
        Returns:
            dict[str, bool]: El mismo diccionario `seen` tras actualizarlo.
        
    """
    if per["eF"] == 1:
        seen["eF"] = True
    if per["eP"] == 1:
        seen["eP"] = True
    if per["eD"] == 1:
        seen["eD"] = True
    if per["eM"] == 1:
        seen["eM"] = True
    if per["eS"] == 1:
        seen["eS"] = True
    return seen


def build_cell_tags(beliefs, r, c, seen, soldier_dead):
    """Construye la etiqueta informativa de una celda para el tablero final.
    
        Args:
            beliefs (dict[str, np.ndarray]): Creencias actuales.
            r (int): Fila de la celda (0-indexada).
            c (int): Columna de la celda (0-indexada).
            seen (dict[str, bool]): Registro de estímulos observados.
            soldier_dead (bool): Si True, se omiten etiquetas asociadas al militar.
    
        Returns:
            str: Etiqueta combinada (por ejemplo "F?", "D!", "S?", etc.) o "." si no hay nada relevante.
    
        Notes:
            - '!' se usa solo si p≈1 (certeza).
            - '?' se usa solo si el estímulo correspondiente se ha visto y la probabilidad supera el umbral.
        
    """
    tags = []

    for t, ek in [("F", "eF"), ("P", "eP"), ("D", "eD")]:
        p = float(beliefs[t][r, c])
        if p >= 1.0 - EPS_SURE:
            tags.append(f"{t}!")
        elif seen[ek] and p >= HINT_THRESHOLD:
            tags.append(f"{t}?")

    if not soldier_dead:
        pM = float(beliefs["M"][r, c])
        if pM >= 1.0 - EPS_SURE:
            tags.append("M!")
        elif seen["eM"] and pM >= HINT_THRESHOLD:
            tags.append("M?")

    pS = float(beliefs["S"][r, c])
    if pS >= 1.0 - EPS_SURE:
        tags.append("S!")
    elif seen["eS"] and pS > 0.0:
        tags.append("S?")


    if len(tags) == 0:
        return "."
    return "".join(tags)


def safe_set_from_risk(n, visited, beliefs, risk_cutoff, soldier_dead):
    """Calcula el conjunto de celdas seguras según un umbral de riesgo.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            visited (set[tuple[int, int]]): Celdas ya visitadas (se excluyen del conjunto).
            beliefs (dict[str, np.ndarray]): Creencias actuales.
            risk_cutoff (float): Umbral p: se considera segura si P(muerte) < p.
            soldier_dead (bool): Si True, el militar no contribuye al riesgo.
    
        Returns:
            set[tuple[int, int]]: Celdas no visitadas con riesgo estricto por debajo del umbral.
        
    """
    risk = death_risk_union(beliefs, soldier_dead)
    s = set()
    for r in range(n):
        for c in range(n):
            if (r, c) in visited:
                continue
            if float(risk[r, c]) < risk_cutoff:
                s.add((r, c))
    return s


def choose_color_for_tag(tag):
    """Selecciona el color asociado a una etiqueta del tablero, siguiendo el estilo de la Parte 1.
    
        Args:
            tag (str): Etiqueta de la celda (por ejemplo "CW", "✓", "F?", "S!", etc.).
    
        Returns:
            str: Código de color de `kurtz_colors` (o cadena vacía si no hay color).
        
    """
    if not tag:
        return ""

    if tag.startswith("CW"):
        return kc.GREEN
    if tag == "v":
        return kc.GREEN
    if tag == "✓":
        return kc.BLUE

    #Salida (PDF usa S, pero color como E en parte 1)
    if tag == "S" or "S!" in tag:
        return kc.YELLOW_DARK
    if "S?" in tag:
        return kc.YELLOW_LIGHT

    if ("F!" in tag) or ("P!" in tag) or ("D!" in tag) or ("M!" in tag):
        return kc.RED
    if ("F?" in tag) or ("P?" in tag) or ("D?" in tag) or ("M?" in tag):
        return kc.ORANGE

    return ""


def colorize_cell(padded, tag):
    """Colorea el texto ya alineado de una celda según su etiqueta.
    
        Args:
            padded (str): Texto de la celda ya formateado a ancho fijo.
            tag (str): Etiqueta de la celda (la que se usa para decidir el color).
    
        Returns:
            str: Texto coloreado (o sin cambios si no procede).
        
    """
    col = choose_color_for_tag(tag)
    if col == "":
        return padded
    return paint(padded, col)



def print_prob_grid(title, grid, pos, cell_width=9, decimals=2, heatmap=True, kurtz_found=False, on_exit=False):
    """Imprime un mapa numérico (opcionalmente con heatmap) para una cuadrícula de valores.
    
        Args:
            title (str): Título del mapa.
            grid (np.ndarray): Cuadrícula de valores a mostrar.
            pos (tuple[int, int]): Posición actual del capitán (se marca como CW/CWK/CWS/CWKS).
            cell_width (int): Ancho fijo de cada celda impresa.
            decimals (int): Número de decimales al formatear los valores.
            heatmap (bool): Si True, colorea celdas por rangos de valor.
            kurtz_found (bool): Si True, marca CWK en la posición del capitán.
            on_exit (bool): Si True, marca CWS/CWKS en la posición del capitán.
    
        Returns:
            None: Solo imprime en consola.
        
    """
    def _color_for_value(v):
        #Rangos simples (funciona tanto para probabilidades [0,1] como para sumas >1)
        """Selecciona un color discreto en función del valor numérico de una celda (heatmap).
        
            Args:
                v (float): Valor a clasificar.
        
            Returns:
                str: Código de color (o cadena vacía si no se colorea).
            
        """
        if v >= 1.0 - 1e-12:
            return kc.RED
        if v >= 0.50:
            return kc.RED
        if v >= 0.20:
            return kc.ORANGE
        if v >= 0.10:
            return kc.YELLOW_LIGHT
        if v >= 0.05:
            return kc.BLUE
        return ""

    n = grid.shape[0]
    print(f"\n{title}")
    if heatmap:
        #Leyenda del degradado de colores utilizado en los mapas de probabilidad.
        #(Los valores numéricos siguen siendo la referencia para corregir.)
        legend = (
            "Leyenda heatmap: "
            + paint("ROJO", kc.RED) + " >=0.50 | "
            + paint("NARANJA", kc.ORANGE) + " [0.20,0.50) | "
            + paint("AMARILLO", kc.YELLOW_LIGHT) + " [0.10,0.20) | "
            + paint("AZUL", kc.BLUE) + " [0.05,0.10) | "
            + "sin color <0.05"
        )
        print("     " + legend)
    header = "     " + "".join([fmt_cell(str(c + 1), cell_width) for c in range(n)])
    print(header)
    print("     " + "-" * (n * cell_width))

    pr, pc = pos
    for r in range(n):
        line = fmt_cell(str(r + 1), 5)
        for c in range(n):
            if (r, c) == (pr, pc):
                cw = "CW"
                if kurtz_found:
                    cw += "K"
                if on_exit:
                    cw += "S"
                line += paint(fmt_cell(cw, cell_width), kc.GREEN)
            else:
                v = float(grid[r, c])
                cell_txt = fmt_cell(f"{v:.{decimals}f}", cell_width)
                if heatmap:
                    col = _color_for_value(v)
                    if col:
                        cell_txt = paint(cell_txt, col)
                line += cell_txt
        print(line)



def print_all_maps(world, beliefs, pos, soldier_dead, kurtz_found=False, on_exit=False):
    """Imprime los mapas requeridos y mapas extra útiles para depuración y comprensión.
    
        Args:
            world (dict): Mundo actual.
            beliefs (dict[str, np.ndarray]): Creencias actuales.
            pos (tuple[int, int]): Posición del capitán.
            soldier_dead (bool): Si True, el militar no contribuye al riesgo.
            kurtz_found (bool): Si True, el capitán lleva a Kurtz.
            on_exit (bool): Si True, el capitán está sobre la salida.
    
        Returns:
            None: Solo imprime en consola.
        
    """
    #=== Requeridos por el PDF ===
    print_prob_grid("Mapa requerido (PDF): Trampa cualquiera (pF+pP+pD)", trap_heat_sum(beliefs), pos, kurtz_found=kurtz_found, on_exit=on_exit)
    print_prob_grid("Mapa requerido (PDF): Soldado enemigo (M)", beliefs["M"], pos, kurtz_found=kurtz_found, on_exit=on_exit)
    print_prob_grid("Mapa requerido (PDF): Salida (S)", beliefs["S"], pos, kurtz_found=kurtz_found, on_exit=on_exit)

    #=== Extras (ayudan a depurar / entender) ===
    print_prob_grid("Extra: P(muerte) al pisar celda", death_risk_union(beliefs, soldier_dead), pos, kurtz_found=kurtz_found, on_exit=on_exit)
    print_prob_grid("Extra: Posterior F", beliefs["F"], pos, kurtz_found=kurtz_found, on_exit=on_exit)
    print_prob_grid("Extra: Posterior P", beliefs["P"], pos, kurtz_found=kurtz_found, on_exit=on_exit)
    print_prob_grid("Extra: Posterior D", beliefs["D"], pos, kurtz_found=kurtz_found, on_exit=on_exit)
    print_prob_grid("Extra: Posterior CK", beliefs["CK"], pos, kurtz_found=kurtz_found, on_exit=on_exit)


def print_palace_board(world, pos, visited, safe_set, beliefs, per,
                       risk_cutoff, soldier_dead, kurtz_found, exit_seen, seen, cell_width=16):
    """Imprime el tablero final con etiquetas y colores (estilo Parte 1).
    
        Args:
            world (dict): Mundo actual.
            pos (tuple[int, int]): Posición del capitán.
            visited (set[tuple[int, int]]): Celdas ya visitadas.
            safe_set (set[tuple[int, int]]): Celdas consideradas seguras con el umbral actual.
            beliefs (dict[str, np.ndarray]): Creencias actuales.
            per (dict): Percepto actual (para mostrar estímulos en la celda del capitán).
            risk_cutoff (float): Umbral p para marcar celdas seguras (✓).
            soldier_dead (bool): Si True, se omiten marcas relacionadas con el militar.
            kurtz_found (bool): Si True, se marca CWK.
            exit_seen (bool): Si True, se marca la salida S cuando corresponda.
            seen (dict[str, bool]): Registro de estímulos observados (habilita candidatos '?').
            cell_width (int): Ancho fijo de cada celda impresa.
    
        Returns:
            None: Solo imprime en consola.
        
    """
    n = world["n"]
    on_exit = (pos == world["S"])

    print("\nLeyenda:")
    print(" ", paint("CW", kc.GREEN), ": capitán")
    print(" ", paint("CWK", kc.GREEN), ": capitán con Kurtz")
    print(" ", paint("CWS / CWKS", kc.GREEN), ": estás en la salida (pulsa 'x' para salir si llevas a Kurtz)")
    print(" ", paint("v", kc.GREEN), ": visitada")
    print(" ", paint("✓", kc.BLUE), f": segura (P(muerte) < p={risk_cutoff:.2f})")
    print(" ", paint("F?/P?/D?/M?/S?", kc.ORANGE), ": candidato (hay evidencia positiva y destaca)")
    print(" ", paint("F!/P!/D!/M!/S!", kc.RED), ": seguro (p=1)")
    print(" ", paint("S", kc.YELLOW_DARK), ": salida descubierta (se marca cuando la pisas)")
    print(" ", ".", ": desconocida (no segura y sin evidencias claras todavía)")
    print()

    header = "     " + "".join([fmt_cell(str(c + 1), cell_width) for c in range(n)])
    print(header)
    print("     " + "-" * (n * cell_width))

    for r in range(n):
        line = fmt_cell(str(r + 1), 5)
        for c in range(n):
            p = (r, c)

            if p == pos:
                tag = cw_tag(per, kurtz_found, on_exit)
            else:
                if exit_seen and p == world["S"]:
                    tag = "S"
                elif p in visited:
                    tag = "v"
                else:
                    hint = build_cell_tags(beliefs, r, c, seen, soldier_dead)
                    if hint != ".":
                        tag = ("✓" + hint) if ((p in safe_set) and (not hint.startswith("S"))) else hint
                    elif p in safe_set:
                        tag = "✓"
                    else:
                        tag = "."

            padded = fmt_cell(tag, cell_width)
            padded = colorize_cell(padded, tag)
            line += padded

        print(line)



#Mecánicas (muerte / granada)


def step_into(world, new_pos, soldier_alive):
    """Evalúa el resultado de entrar en una celda del mundo real.
    
        Args:
            world (dict): Mundo actual (posiciones reales).
            new_pos (tuple[int, int]): Celda de destino.
            soldier_alive (bool): Indica si el militar sigue vivo.
    
        Returns:
            str: "TRAP" si hay trampa, "MILITAR" si está el militar vivo, u "OK" en caso contrario.
        
    """
    for t in TRAPS:
        if world["traps"][t] == new_pos:
            return "TRAP"
    if soldier_alive and (world["M"] == new_pos):
        return "MILITAR"
    return "OK"


def throw_grenade(world, pos, direction, soldier_alive, soldier_dead):
    """Simula el lanzamiento de una granada a la celda contigua en una dirección.
    
        Args:
            world (dict): Mundo actual.
            pos (tuple[int, int]): Posición del capitán.
            direction (str): Dirección en {U, D, L, R}.
            soldier_alive (bool): Indica si el militar está vivo antes del lanzamiento.
            soldier_dead (bool): Indica si el militar ya está muerto (en cuyo caso no hay efecto).
    
        Returns:
            tuple[bool, bool, bool, tuple[int, int] | None]:
                - soldier_alive: estado actualizado (puede pasar a False si se acierta).
                - soldier_dead: estado actualizado.
                - grito_flag: True si se acierta al militar (se oye grito).
                - target: celda objetivo (o None si la dirección sale del tablero).
        
    """
    if soldier_dead:
        return soldier_alive, soldier_dead, False, None

    dr, dc = DIRS[direction]
    target = (pos[0] + dr, pos[1] + dc)
    if not in_bounds(world["n"], target[0], target[1]):
        return soldier_alive, soldier_dead, False, None

    if soldier_alive and (world["M"] == target):
        return False, True, True, target

    return soldier_alive, soldier_dead, False, target


def can_exit(pos, kurtz_found, world):
    """Comprueba si el agente puede salir del palacio.
    
        Args:
            pos (tuple[int, int]): Posición actual del capitán.
            kurtz_found (bool): True si el capitán lleva a Kurtz.
            world (dict): Mundo actual (incluye la posición de la salida).
    
        Returns:
            bool: True si está en la salida y lleva a Kurtz; False en caso contrario.
        
    """
    return kurtz_found and (pos == world["S"])





#Búsqueda con traza (Frontier/Explored)


def _fmt_val(val):
    """Formatea un valor numérico (g, h o f) para mostrarse en la traza de búsqueda.
    
        Args:
            val (Any): Valor a formatear.
    
        Returns:
            str: Representación compacta (enteros sin decimales, flotantes con pocos decimales, etc.).
        
    """
    if val is None:
        return ""
    #si es prácticamente entero, lo imprimimos como entero
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    try:
        v = float(val)
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(val)


def _fmt_node_with_val(node, val):
    """Formatea un nodo (fila, columna) junto con su valor asociado para la traza.
    
        Args:
            node (tuple[int, int]): Celda (fila, columna), 0-indexada.
            val (Any): Valor asociado al nodo (g/h/f según el método).
    
        Returns:
            str: Cadena del tipo "(r,c)(val)" usando coordenadas 1-indexadas para mostrar.
        
    """
    r, c = node
    return f"({r+1},{c+1})({_fmt_val(val)})"


def _fmt_nodeset(nodes_to_val):
    """Formatea un conjunto/diccionario de nodos para imprimir Frontier/Explored en la traza.
    
        Args:
            nodes_to_val (dict[tuple[int, int], Any]): Mapa `nodo -> valor`.
    
        Returns:
            str: Representación tipo "{(r,c)(v),...}" ordenada para facilitar lectura.
        
    """
    if not nodes_to_val:
        return "{}"
    items = sorted(nodes_to_val.items(), key=lambda kv: (kv[1], kv[0][0], kv[0][1]))
    inner = ",".join(_fmt_node_with_val(n, v) for n, v in items)
    return "{" + inner + "}"


def _reconstruct_path(parent, start, goal):
    """Reconstruye un camino desde un diccionario de padres.
    
        Args:
            parent (dict[tuple[int, int], tuple[int, int]]): Mapa `nodo -> padre`.
            start (tuple[int, int]): Nodo inicial.
            goal (tuple[int, int]): Nodo objetivo.
    
        Returns:
            list[tuple[int, int]] | None: Camino desde start a goal (incluidos) o None si no existe.
        
    """
    if goal not in parent and goal != start:
        return None
    cur = goal
    path = [cur]
    while cur != start:
        cur = parent[cur]
        path.append(cur)
    path.reverse()
    return path


def search_path_with_trace(n, start, goal, passable, method,
                           risk=None, risk_weight=0.0,
                           heuristic_fn=None,
                           max_expansions=10_000,
                           trace_prefix="[Plan]"):
    """Realiza una búsqueda en una cuadrícula 4-neighbor e imprime la traza de Frontier/Explored.
    
        Args:
            n (int): Tamaño del tablero (n x n).
            start (tuple[int, int]): Nodo inicial.
            goal (tuple[int, int]): Nodo objetivo.
            passable (set[tuple[int, int]]): Celdas por las que se permite transitar.
            method (str): Algoritmo de búsqueda: "bfs", "dfs", "gbfs" o "astar".
            risk (np.ndarray | None): Mapa de riesgo (solo se usa en A* si se proporciona).
            risk_weight (float): Peso del riesgo en el coste (solo A*).
            heuristic_fn (callable | None): Heurística h(nodo)->float. Si es None, usa Manhattan al objetivo.
            max_expansions (int): Límite de extracciones de la frontera.
            trace_prefix (str): Prefijo impreso en cada línea de traza.
    
        Returns:
            tuple[list[tuple[int, int]] | None, list[dict]]:
                - path: camino encontrado (o None).
                - trace_records: registros por paso con snapshot de frontera, removed y explored.
    
        Side Effects:
            Imprime en consola una línea por expansión con el estado de Frontier/Explored.
        
    """
    method = method.lower()
    if heuristic_fn is None:
        heuristic_fn = lambda x: manhattan(x, goal)

    def val_for(node, g):
        """Calcula el valor escalar que se muestra/usa para ordenar un nodo según el método de búsqueda.
        
            Args:
                node (tuple[int, int]): Nodo (fila, columna).
                g (float): Coste acumulado hasta el nodo.
        
            Returns:
                float: Valor asociado (g para BFS/DFS, h para GBFS, g+h para A*).
            
        """
        if method == "bfs" or method == "dfs":
            return float(g)
        if method == "gbfs":
            return float(heuristic_fn(node))
        if method == "astar":
            h = float(heuristic_fn(node))
            return float(g) + h
        raise ValueError("Método desconocido")

    def key_for(node, g, stamp):
        """Construye la clave de prioridad para ordenar nodos en la frontera.
        
            Args:
                node (tuple[int, int]): Nodo candidato.
                g (float): Coste acumulado hasta el nodo.
                stamp (int): Contador para desempates (mantiene estabilidad del orden).
        
            Returns:
                tuple[tuple, float]: (clave_ordenación, valor_visible) para almacenar en la frontera.
            
        """
        v = val_for(node, g)
        if method == "bfs":
            return (g, stamp), v
        if method == "dfs":
            #LIFO: priorizamos mayor profundidad y más reciente
            return (-g, -stamp), v
        if method == "gbfs":
            return (v, stamp), v
        if method == "astar":
            return (v, stamp), v
        raise ValueError("Método desconocido")

    open_map = {}  #node -> (key_tuple, val, g, stamp)
    parent = {}
    gscore = {start: 0.0}
    stamp = 0

    k, v0 = key_for(start, 0.0, stamp)
    open_map[start] = (k, v0, 0.0, stamp)

    explored = {}  #node -> val (solo para imprimir)
    trace = []
    step = 0

    while open_map and step < max_expansions:
        #snapshot frontier antes de extraer
        frontier_snapshot = {node: open_map[node][1] for node in open_map}

        #elegir removed por prioridad
        removed = min(open_map.items(), key=lambda kv: kv[1][0])[0]
        removed_key, removed_val, removed_g, removed_stamp = open_map.pop(removed)
        explored[removed] = removed_val

        line = (f"{trace_prefix} Step {step} | "
                f"Frontier={_fmt_nodeset(frontier_snapshot)} | "
                f"Removed={_fmt_node_with_val(removed, removed_val)} | "
                f"Explored={_fmt_nodeset(explored)}")
        print(line)

        trace.append({
            "step": step,
            "frontier": frontier_snapshot,
            "removed": (removed, removed_val),
            "explored": dict(explored),
        })

        if removed == goal:
            return _reconstruct_path(parent, start, goal), trace

        #expandimos vecinos
        for nb in neighbors4(n, removed):
            if nb not in passable:
                continue
            if nb in explored:
                continue

            step_cost = 1.0
            if method == "astar" and risk is not None and risk_weight > 0.0:
                step_cost = 1.0 + risk_weight * float(risk[nb[0], nb[1]])

            new_g = gscore[removed] + step_cost

            if nb not in gscore:
                better = True
            else:
                better = (method == "astar") and (new_g + 1e-12 < gscore[nb])
                #BFS/DFS/GBFS: si ya fue descubierto, no lo reinsertamos
                if method != "astar":
                    better = False

            if better:
                gscore[nb] = new_g
                parent[nb] = removed
                stamp += 1
                k2, v2 = key_for(nb, new_g, stamp)
                open_map[nb] = (k2, v2, new_g, stamp)

        step += 1

    return None, trace
def choose_target(pos, visited, beliefs, risk, risk_cutoff, kurtz_found):
    """Elige el siguiente objetivo para el modo automático a partir de creencias y riesgo.
    
        Args:
            pos (tuple[int, int]): Posición actual del agente.
            visited (set[tuple[int, int]]): Celdas ya visitadas.
            beliefs (dict[str, np.ndarray]): Creencias actuales.
            risk (np.ndarray): Mapa de riesgo de muerte por celda.
            risk_cutoff (float): Umbral p para considerar una celda "aceptable".
            kurtz_found (bool): True si Kurtz ya ha sido rescatado.
    
        Returns:
            tuple[int, int] | None: Celda objetivo elegida, o None si no hay candidatas válidas.
    
        Notes:
            Antes de rescatar a Kurtz se prioriza explorar con riesgo aceptable, favoreciendo salida y cercanía.
            Tras rescatarlo se prioriza ir hacia la salida (máximo a posteriori de S).
        
    """
    n = risk.shape[0]
    pS = beliefs["S"]
    pCK = beliefs["CK"]

    best = None
    best_key = None

    for r in range(n):
        for c in range(n):
            cell = (r, c)
            if cell == pos:
                continue

            #descartamos muerte segura
            if float(risk[r, c]) >= 1.0 - EPS_SURE:
                continue

            #solo celdas permitidas por KB
            ok = (cell in visited) or (float(risk[r, c]) < risk_cutoff)
            if not ok:
                continue

            dist = manhattan(pos, cell)
            rr = float(risk[r, c])

            if kurtz_found:
                #fase 2: salida
                score_main = float(pS[r, c])
            else:
                #fase 1: explorar (salida + kurtz)
                score_main = float(pS[r, c]) + 0.25 * float(pCK[r, c])

            #Queremos: score alto, distancia baja, riesgo bajo
            key = (-score_main, dist, rr, r, c)
            if best_key is None or key < best_key:
                best_key = key
                best = cell

    return best



#Modo automático


def path_to_actions_wasd(path):
    """Convierte un camino de celdas (lista de posiciones) en acciones w/a/s/d.
    
        Args:
            path (list[tuple[int, int]]): Secuencia de celdas consecutivas.
    
        Returns:
            list[str]: Lista de acciones ("w", "a", "s", "d") que reproducen el camino.
        
    """
    if not path or len(path) < 2:
        return []
    out = []
    for a, b in zip(path, path[1:]):
        dr = b[0] - a[0]
        dc = b[1] - a[1]
        if dr == -1 and dc == 0:
            out.append("w")
        elif dr == 1 and dc == 0:
            out.append("s")
        elif dr == 0 and dc == -1:
            out.append("a")
        elif dr == 0 and dc == 1:
            out.append("d")
        else:
            out.append("?")
    return out


def run_auto(world, risk_cutoff, search_method="astar", steps_max=500, verbose=True, show_maps=False):
    """Ejecuta el modo automático: planifica y recorre rutas usando búsqueda, riesgo y creencias bayesianas.
    
        Args:
            world (dict): Mundo generado (tablero y posiciones reales).
            risk_cutoff (float): Umbral inicial p para considerar celdas transitables (P(muerte) < p).
            search_method (str): Método de búsqueda ("bfs", "dfs", "gbfs" o "astar").
            steps_max (int): Límite máximo de pasos de ejecución.
            verbose (bool): Si True, imprime mensajes de progreso.
            show_maps (bool): Si True, imprime además mapas numéricos en cada paso.
    
        Returns:
            dict: Resumen de la ejecución con claves:
                - "result": estado final ("DONE" o motivo de fin).
                - "positions": posiciones visitadas (1-indexadas para mostrar).
                - "actions": acciones ejecutadas (incluye granadas como "g<dir>").
                - "plan_traces": trazas de planificación (a Kurtz y a la salida).
    
        Notes:
            La planificación puede solicitar (interactivamente) subir temporalmente el umbral p si no existe ruta
            con el valor actual. Durante la ejecución se actualizan creencias con perceptos observados y, si
            procede, se usa la granada de forma reactiva para reducir riesgo asociado al militar.
        
    """
    n = world["n"]
    method = search_method.lower()

    #Heurísticas-oráculo (permitidas): distancia Manhattan al objetivo real.
    #IMPORTANTE: en planificación NO se compara por coordenadas; se considera alcanzado el objetivo
    #cuando h(pos)==0 (igual que en kurtz.py).
    h_kurtz = (lambda p: manhattan(p, world["CK"]))
    h_exit  = (lambda p: manhattan(p, world["S"]))

    risk_cutoff_base = float(risk_cutoff)

    #Estado "real" del agente (se actualizará en ejecución)
    pos = world["start"]
    visited = set([pos])

    soldier_alive = True
    soldier_dead = False
    kurtz_found = False
    exit_seen = False
    fixed_exit = False
    fixed_kurtz = False

    #Granada: el plan se calcula solo con movimientos, y durante la ejecución se puede
    #usar la granada de forma reactiva si evita relajar el umbral de riesgo por militar.
    grenade_used = False
    grito_flag = False
    soldier_forbidden = set()

    beliefs = init_beliefs(n, world["start"])
    seen = {"eF": False, "eP": False, "eD": False, "eM": False, "eS": False}

    #Memoria de perceptos conocidos (incluye los "vistos" en planificación)
    known_percepts = {}

    #---------- Helpers locales ----------
    def _observe_if_needed(cell, planning=False, grito=False):
        """Obtiene perceptos del mundo real y los memoriza para reutilizarlos.
        
            Args:
                cell (tuple[int, int]): Celda sobre la que se observan perceptos.
                planning (bool): Si True, permite observar también celdas de frontera/explorados durante planificación.
                grito (bool): Si True, fuerza un percepto "fresco" con Grito (no se cachea).
        
            Returns:
                dict: Percepto observado en `cell`.
        
            Notes:
                - e^M depende de si el militar sigue vivo.
                - "Grito" es un evento puntual: cuando `grito=True` se devuelve sin cachear para no congelarlo.
            
        """
        nonlocal seen, known_percepts
        cache_key = (cell, bool(soldier_dead))
        if (not grito) and (cache_key in known_percepts):
            return dict(known_percepts[cache_key])
        per = percept_at(world, cell, soldier_alive and (not soldier_dead), grito)
        if not grito:
            known_percepts[cache_key] = per
        seen = seen_update(seen, per)
        return per

    def _update_beliefs_at(cell, per):
        """Actualiza las creencias globales del modo automático para una celda dada.
        
            Args:
                cell (tuple[int, int]): Celda donde se ha observado el percepto.
                per (dict): Percepto observado en `cell`.
        
            Returns:
                None: Actualiza `beliefs` en el cierre (nonlocal).
            
        """
        nonlocal beliefs
        beliefs = update_beliefs(
            world, beliefs, cell, visited, per,
            soldier_alive=soldier_alive,
            soldier_dead=soldier_dead,
            soldier_forbidden=soldier_forbidden,
            fixed_exit=fixed_exit,
            fixed_kurtz=fixed_kurtz
        )

    def _recompute_passable(p):
        """Recalcula el conjunto de celdas transitables con un umbral de riesgo dado.
        
            Args:
                p (float): Umbral de riesgo (P(muerte) < p) usado para definir "seguro".
        
            Returns:
                tuple[set[tuple[int, int]], set[tuple[int, int]], np.ndarray]:
                    - passable: celdas por las que el plan puede transitar.
                    - safe_set: celdas no visitadas consideradas seguras con el umbral.
                    - risk: mapa de riesgo de muerte por celda.
            
        """
        safe_set = safe_set_from_risk(n, visited, beliefs, p, soldier_dead)
        risk = death_risk_union(beliefs, soldier_dead)
        passable = set(visited) | set(safe_set) | {pos}
        return passable, safe_set, risk

    def _grenade_can_reduce_risk(cell, p_allow):
        """Comprueba si una granada hacia una celda podría reducir el riesgo por militar.
        
            Args:
                cell (tuple[int, int]): Celda candidata (normalmente el siguiente paso planificado).
                p_allow (float): Umbral de riesgo que se quiere respetar.
        
            Returns:
                bool: True si la granada podría hacer que el paso sea aceptable (bajando pM), False en caso contrario.
        
            Notes:
                La granada no afecta a trampas, así que solo tiene sentido cuando:
                pTrap(cell) < p_allow y pTrap(cell) + pM(cell) >= p_allow.
            
        """
        if grenade_used or soldier_dead or (not soldier_alive):
            return False
        p_trap = float(trap_union_prob(beliefs)[cell[0], cell[1]])
        p_m = float(beliefs["M"][cell[0], cell[1]])
        if p_m <= 0.0:
            return False
        if p_trap >= p_allow - 1e-12:
            return False
        return (p_trap + p_m) >= p_allow - 1e-12

    def _apply_grenade_evidence(target):
        """Aplica evidencia dura de granada fallida: el militar NO está en una celda.
        
            Args:
                target (tuple[int, int] | None): Celda objetivo del lanzamiento (None si no hubo objetivo válido).
        
            Returns:
                None: Actualiza `beliefs["M"]` en el cierre (nonlocal).
            
        """
        nonlocal beliefs
        if soldier_dead:
            beliefs["M"] = np.zeros((n, n), dtype=float)
            return
        if target is None:
            return
        g = beliefs["M"].copy()
        g[target[0], target[1]] = 0.0
        g = normalize_grid(g, fallback_mask=(g > 0).astype(float))
        g = snap_onehot_if_forced(g)
        #Reaplicamos restricciones (coherencia con update_beliefs)
        trap_certain = trap_certain_mask(beliefs)
        g = enforce_no_trap_for_entity(g, trap_certain)
        g = enforce_entity_not_on_traps_soft(g, beliefs)
        beliefs["M"] = g

    def _maybe_throw_grenade(next_cell, move_key, p_allow):
        """Decide y ejecuta un lanzamiento de granada si ayuda a mantener el umbral de riesgo.
        
            Args:
                next_cell (tuple[int, int]): Siguiente celda a la que se pretende entrar.
                move_key (str): Acción de movimiento asociada ("w", "a", "s" o "d") para derivar la dirección.
                p_allow (float): Umbral actual de riesgo que se quiere respetar.
        
            Returns:
                bool: True si se lanza la granada (y se actualiza el estado), False si no se usa.
            
        """
        nonlocal grenade_used, grito_flag, soldier_alive, soldier_dead, soldier_forbidden, beliefs
        if not _grenade_can_reduce_risk(next_cell, p_allow):
            return False
        if move_key not in KEY_TO_DIR:
            return False

        direction = KEY_TO_DIR[move_key]
        grenade_used = True

        soldier_alive2, soldier_dead2, grito_now, target = throw_grenade(
            world, pos, direction, soldier_alive, soldier_dead
        )
        soldier_alive, soldier_dead = soldier_alive2, soldier_dead2

        if soldier_dead:
            beliefs["M"] = np.zeros((n, n), dtype=float)
        else:
            if target is not None and (not grito_now):
                soldier_forbidden.add(target)
                _apply_grenade_evidence(target)

        if grito_now:
            grito_flag = True
            if target is not None:
                print(paint(f"[AUTO] Granada -> ({target[0]+1},{target[1]+1}): ¡GRITO! Militar neutralizado.", kc.GREEN))
            else:
                print(paint("[AUTO] Granada: ¡GRITO! Militar neutralizado.", kc.GREEN))
        else:
            if target is not None:
                print(paint(f"[AUTO] Granada -> ({target[0]+1},{target[1]+1}): sin grito (M no estaba ahí).", kc.YELLOW_LIGHT))
            else:
                print(paint("[AUTO] Granada: sin efecto.", kc.YELLOW_LIGHT))

        return True

    
    def _auto_plan_path(start_cell, p, heuristic_fn, trace_prefix="[Plan]"):
        """Planifica un camino con traza, observando nodos de frontera/explorados.
        
            Objetivo (criterio Kurtz):
                Se considera alcanzado cuando `heuristic_fn(pos) == 0` (sin comparar coordenadas explícitas).
        
            Args:
                start_cell (tuple[int, int]): Celda inicial desde la que planificar.
                p (float): Umbral de riesgo usado para definir transitabilidad.
                heuristic_fn (callable): Heurística h(celda)->float para el objetivo deseado.
                trace_prefix (str): Prefijo impreso en cada línea de traza.
        
            Returns:
                tuple[list[tuple[int, int]] | None, list[dict]]:
                    - path: camino planificado, o None si no existe con el umbral actual.
                    - trace: registros de traza por expansión.
            
        """
        if heuristic_fn is None:
            raise ValueError("Falta heuristic_fn para planificar con objetivo por h(pos)==0.")

        if heuristic_fn(start_cell) == 0:
            return [start_cell], []

        def val_for(node, g):
            """Calcula el valor (g/h/f) asociado a un nodo durante la planificación interna.
            
                Args:
                    node (tuple[int, int]): Nodo (celda) a evaluar.
                    g (float): Coste acumulado hasta el nodo.
            
                Returns:
                    float: Valor que define la prioridad/visualización según el método de búsqueda.
                
            """
            if method in ("bfs", "dfs"):
                return float(g)
            if method == "gbfs":
                return float(heuristic_fn(node))
            if method == "astar":
                return float(g) + float(heuristic_fn(node))
            raise ValueError("Método desconocido")

        def key_for(node, g, stamp):
            """Construye la clave de prioridad para la frontera en la planificación interna.
            
                Args:
                    node (tuple[int, int]): Nodo candidato.
                    g (float): Coste acumulado.
                    stamp (int): Contador para desempates.
            
                Returns:
                    tuple[tuple, float]: (clave_ordenación, valor_visible) para almacenar en la frontera.
                
            """
            v = val_for(node, g)
            if method == "bfs":
                return (g, stamp), v
            if method == "dfs":
                return (-g, -stamp), v
            if method in ("gbfs", "astar"):
                return (v, stamp), v
            raise ValueError("Método desconocido")

        parent = {}
        gscore = {start_cell: 0.0}
        stamp = 0

        k0, v0 = key_for(start_cell, 0.0, stamp)
        open_map = {start_cell: (k0, v0, 0.0, stamp)}
        explored = {}  #node -> val (solo imprimir)
        trace = []
        step = 0

        while open_map and step < 10_000:
            #snapshot frontier antes de extraer
            frontier_snapshot = {node: open_map[node][1] for node in open_map}

            removed = min(open_map.items(), key=lambda kv: kv[1][0])[0]
            _, removed_val, _, _ = open_map.pop(removed)
            explored[removed] = removed_val

            line = (f"{trace_prefix} Step {step} | "
                    f"Frontier={_fmt_nodeset(frontier_snapshot)} | "
                    f"Removed={_fmt_node_with_val(removed, removed_val)} | "
                    f"Explored={_fmt_nodeset(explored)}")
            print(line)

            trace.append({
                "step": step,
                "frontier": frontier_snapshot,
                "removed": (removed, removed_val),
                "explored": dict(explored),
            })

            #Observación (permitida en planificación)
            per_u = _observe_if_needed(removed, planning=True)
            _update_beliefs_at(removed, per_u)

            #Recalcular passable con el nuevo posterior y podar frontera
            passable_now, _, _ = _recompute_passable(p)
            for node in list(open_map.keys()):
                if node not in passable_now:
                    open_map.pop(node)

            #Objetivo por heurística
            if heuristic_fn(removed) == 0:
                return _reconstruct_path(parent, start_cell, removed), trace

            #expandir vecinos
            for nb in neighbors4(n, removed):
                if nb not in passable_now:
                    continue
                if nb in explored:
                    continue

                new_g = gscore[removed] + 1.0

                if nb not in gscore:
                    better = True
                else:
                    better = (method == "astar") and (new_g + 1e-12 < gscore[nb])
                    if method != "astar":
                        better = False

                if better:
                    gscore[nb] = new_g
                    parent[nb] = removed
                    stamp += 1
                    k2, v2 = key_for(nb, new_g, stamp)
                    open_map[nb] = (k2, v2, new_g, stamp)

            step += 1

        return None, trace

    def _plan_with_escalation(start_cell, heuristic_fn, p_base, title):
        """Intenta planificar y, si no hay ruta con el umbral actual, ofrece aumentar p.
        
            Args:
                start_cell (tuple[int, int]): Celda desde la que se planifica.
                heuristic_fn (callable): Heurística del objetivo (h==0 implica objetivo alcanzado).
                p_base (float): Umbral inicial p.
                title (str): Título informativo de la planificación (se imprime).
        
            Returns:
                tuple[list[tuple[int, int]] | None, list[dict] | None, float]:
                    - path: camino encontrado (o None si se abandona).
                    - trace: última traza generada.
                    - p: valor de p con el que finalmente se planifica.
            
        """
        p = float(p_base)
        last_trace = None
        while True:
            print(f"\n=== PLANIFICACIÓN {title} (p={p:.2f}) ===")
            path, trace = _auto_plan_path(start_cell, p, heuristic_fn, trace_prefix="[Plan]")
            last_trace = trace
            if path is not None:
                return path, trace, p

            if p >= 1.0 - EPS_SURE:
                return None, trace, p

            new_p = min(1.0, p + 0.05)
            print(paint(f"[AUTO] No hay ruta con riesgo < p={p:.2f}.", kc.ORANGE))
            if ask_yes_no(
                f"¿Quieres subir TEMPORALMENTE el umbral a p={new_p:.2f} y reintentar? (podrías morir) [s/n] (enter=s): ",
                default=True
            ):
                p = new_p
                print(paint(f"[AUTO] (Temporal) planifico con p={p:.2f}.", kc.YELLOW_LIGHT))
                continue

            return None, last_trace, p

    #---------- Observación inicial (celda real) ----------
    per0 = _observe_if_needed(pos, planning=False)
    _update_beliefs_at(pos, per0)

    #---------- PLAN 1: hasta Kurtz ----------
    path1, trace1, p_plan1 = _plan_with_escalation(pos, h_kurtz, risk_cutoff_base, "A KURTZ")
    if path1 is None:
        print(paint("\n[AUTO] No se ha encontrado plan para llegar a Kurtz con el conocimiento actual.", kc.RED))
        return {
            "result": "NO_PLAN_KURTZ",
            "positions": [(r+1, c+1) for (r, c) in [pos]],
            "actions": [],
            "plan_traces": {"to_kurtz": trace1, "to_exit": None},
        }

    #---------- PLAN 2: desde Kurtz a la salida ----------
    path2, trace2, p_plan2 = _plan_with_escalation(path1[-1], h_exit, risk_cutoff_base, "A LA SALIDA")
    if path2 is None:
        print(paint("\n[AUTO] No se ha encontrado plan para llegar a la salida con el conocimiento actual.", kc.RED))
        return {
            "result": "NO_PLAN_EXIT",
            "positions": [(r+1, c+1) for (r, c) in [pos]],
            "actions": [],
            "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
        }

    #Unir planes (evitar duplicar el nodo de unión)
    full_path = list(path1) + list(path2[1:])
    full_actions = path_to_actions_wasd(full_path)

    print("\n[AUTO] Plan 1 (posiciones):", " -> ".join(f"({r+1},{c+1})" for (r, c) in path1))
    print("[AUTO] Plan 1 (teclas):    ", " ".join(full_actions[:max(0, len(path1)-1)]))
    print("\n[AUTO] Plan 2 (posiciones):", " -> ".join(f"({r+1},{c+1})" for (r, c) in path2))
    print("[AUTO] Plan 2 (teclas):    ", " ".join(full_actions[max(0, len(path1)-1):]))
    print("\n=== EJECUCIÓN ===\n")

    #---------- EJECUCIÓN ----------
    positions_exec = [pos]
    actions_exec = []
    steps = 0

    #Render inicial
    if verbose:
        safe_set = safe_set_from_risk(n, visited, beliefs, risk_cutoff, soldier_dead)
        print("\n------------------------------------------------------------")
        print(f"Posición: ({pos[0]+1},{pos[1]+1}) | Kurtz={kurtz_found} | Militar_muerto={soldier_dead} | Salida_pisada={exit_seen}")
        print("Perceptos:", percept_to_string(per0))
        if show_maps:
            print_all_maps(world, beliefs, pos, soldier_dead, kurtz_found=kurtz_found, on_exit=(pos == world["S"]))
        print_palace_board(
            world, pos, visited, safe_set, beliefs, per0,
            risk_cutoff=risk_cutoff,
            soldier_dead=soldier_dead,
            kurtz_found=kurtz_found,
            exit_seen=exit_seen,
            seen=seen,
        )

    for act, next_pos in zip(full_actions, full_path[1:]):
        steps += 1
        if steps > steps_max:
            return {
                "result": "TIMEOUT",
                "positions": [(r+1, c+1) for (r, c) in positions_exec],
                "actions": actions_exec,
                "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
            }

        #Comprobar si el siguiente paso sigue siendo "seguro" con el p actual
        #Comprobar si el siguiente paso es "seguro" con el umbral BASE.
        #Si no lo es, permitimos (si el usuario quiere) relajar p SOLO para ESTE paso,
        #y luego se vuelve automáticamente al umbral base.
        risk_now = death_risk_union(beliefs, soldier_dead)
        step_risk = float(risk_now[next_pos[0], next_pos[1]])

        if next_pos not in visited:
            p_allow = float(risk_cutoff_base)

            while step_risk >= p_allow - 1e-12 and p_allow < 1.0 - EPS_SURE:
                #Antes de asumir más riesgo, intentamos usar la granada si puede
                #reducir el riesgo por soldado en la celda a la que queremos entrar.
                if _maybe_throw_grenade(next_pos, act, p_allow):
                    actions_exec.append("g" + act)
                    risk_now = death_risk_union(beliefs, soldier_dead)
                    step_risk = float(risk_now[next_pos[0], next_pos[1]])
                    continue

                new_p = min(1.0, p_allow + 0.05)
                print(paint(
                    f"[AUTO] El siguiente paso ({next_pos[0]+1},{next_pos[1]+1}) tiene riesgo={step_risk:.2f} >= p={p_allow:.2f}.",
                    kc.ORANGE
                ))
                if ask_yes_no(
                    f"¿Quieres aumentar TEMPORALMENTE p a {new_p:.2f} para permitir ESTE paso? [s/n] (enter=s): ",
                    default=True
                ):
                    p_allow = new_p
                    print(paint(f"[AUTO] (Temporal) permito este paso con p={p_allow:.2f}.", kc.YELLOW_LIGHT))
                    continue

                print(paint("[AUTO] Me detengo para no asumir más riesgo.", kc.RED))
                return {
                    "result": "STOPPED_UNSAFE_STEP",
                    "positions": [(r+1, c+1) for (r, c) in positions_exec],
                    "actions": actions_exec,
                    "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
                }

            if step_risk >= p_allow - 1e-12:
                #muerte segura (o ya en p=1). No avanzamos.
                print(paint(
                    f"[AUTO] Paso rechazado: riesgo={step_risk:.2f} (muerte segura).",
                    kc.RED
                ))
                return {
                    "result": "STOPPED_UNSAFE_STEP",
                    "positions": [(r+1, c+1) for (r, c) in positions_exec],
                    "actions": actions_exec,
                    "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
                }

        #Mover
        outcome = step_into(world, next_pos, soldier_alive and (not soldier_dead))
        actions_exec.append(act)
        pos = next_pos
        visited.add(pos)
        positions_exec.append(pos)

        #Eventos de mundo al pisar
        if pos == world["CK"]:
            kurtz_found = True
            fixed_kurtz = True
        if pos == world["S"]:
            exit_seen = True
            fixed_exit = True

        if outcome == "TRAP":
            print(paint("\n[AUTO] He caído en una trampa. Fin.", kc.RED))
            return {
                "result": "DEAD_TRAP",
                "positions": [(r+1, c+1) for (r, c) in positions_exec],
                "actions": actions_exec,
                "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
            }
        if outcome == "MILITAR":
            print(paint("\n[AUTO] El militar me ha abatido. Fin.", kc.RED))
            return {
                "result": "DEAD_MILITAR",
                "positions": [(r+1, c+1) for (r, c) in positions_exec],
                "actions": actions_exec,
                "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
            }

        #Observación real (en la celda actual)
        per = _observe_if_needed(pos, planning=False, grito=grito_flag)
        grito_flag = False
        _update_beliefs_at(pos, per)

        safe_set = safe_set_from_risk(n, visited, beliefs, risk_cutoff, soldier_dead)

        if verbose:
            print("\n------------------------------------------------------------")
            print(f"Posición: ({pos[0]+1},{pos[1]+1}) | Kurtz={kurtz_found} | Militar_muerto={soldier_dead} | Salida_pisada={exit_seen}")
            print("Perceptos:", percept_to_string(per))
            stim = active_stimuli(per)
            print("Estímulos activos:", "(ninguno)" if len(stim) == 0 else ", ".join(stim))

            if can_exit(pos, kurtz_found, world):
                print(paint(">>> Estás en la salida con Kurtz: puedes SALIR.", kc.YELLOW_DARK))

            if show_maps:
                print_all_maps(world, beliefs, pos, soldier_dead, kurtz_found=kurtz_found, on_exit=(pos == world["S"]))

            print_palace_board(
                world, pos, visited, safe_set, beliefs, per,
                risk_cutoff=risk_cutoff,
                soldier_dead=soldier_dead,
                kurtz_found=kurtz_found,
                exit_seen=exit_seen,
                seen=seen,
            )

        #Si llegamos a salida con Kurtz, pedimos 'x' (estilo parte 1)
        if can_exit(pos, kurtz_found, world):
            actions_exec.append("x")
            print(paint("\n[AUTO] Estás en la salida con Kurtz: salgo automáticamente (x).", kc.YELLOW_DARK))
            print(paint("\n[AUTO] ÉXITO: has salido con Kurtz.", kc.GREEN))
            return {
                "result": "SUCCESS",
                "positions": [(r+1, c+1) for (r, c) in positions_exec],
                "actions": actions_exec,
                "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
            }

    #Si termina el plan sin haber salido, devolvemos estado
    if can_exit(pos, kurtz_found, world):
        actions_exec.append("x")
        print(paint("\n[AUTO] Estás en la salida con Kurtz al finalizar el plan: salgo automáticamente (x).", kc.YELLOW_DARK))
        print(paint("\n[AUTO] ÉXITO: has salido con Kurtz.", kc.GREEN))
        return {
            "result": "SUCCESS",
            "positions": [(r+1, c+1) for (r, c) in positions_exec],
            "actions": actions_exec,
            "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
        }

    return {
        "result": "DONE",
        "positions": [(r+1, c+1) for (r, c) in positions_exec],
        "actions": actions_exec,
        "plan_traces": {"to_kurtz": trace1, "to_exit": trace2},
    }

def run_manual(world, risk_cutoff):
    """Ejecuta el modo manual (interactivo) del palacio bayesiano.
    
        Controles:
            - w/a/s/d: mover
            - g: granada (1 uso)
            - x: salir (solo si estás en la salida y llevas a Kurtz)
            - m: alternar impresión de mapas numéricos
            - q: terminar
    
        Args:
            world (dict): Mundo generado.
            risk_cutoff (float): Umbral p para marcar celdas seguras (✓).
    
        Returns:
            None: Controla la partida por consola hasta que el usuario salga o termine.
        
    """
    n = world["n"]
    pos = world["start"]
    visited = set([pos])

    soldier_alive = True
    soldier_dead = False
    kurtz_found = False

    exit_seen = False
    fixed_exit = False
    fixed_kurtz = False

    grenade_used = False
    grito_flag = False
    soldier_forbidden = set()

    beliefs = init_beliefs(n, world["start"])
    show_maps = True

    seen = {"eF": False, "eP": False, "eD": False, "eM": False, "eS": False}

    while True:
        if pos == world["CK"]:
            kurtz_found = True
            fixed_kurtz = True

        if pos == world["S"]:
            exit_seen = True
            fixed_exit = True

        per = percept_at(world, pos, soldier_alive, grito_flag)
        grito_flag = False
        seen = seen_update(seen, per)

        beliefs = update_beliefs(
            world, beliefs, pos, visited, per,
            soldier_alive=soldier_alive,
            soldier_dead=soldier_dead,
            soldier_forbidden=soldier_forbidden,
            fixed_exit=fixed_exit,
            fixed_kurtz=fixed_kurtz
        )

        safe_set = safe_set_from_risk(n, visited, beliefs, risk_cutoff, soldier_dead)

        print("\n------------------------------------------------------------")
        print(f"Posición: ({pos[0]+1},{pos[1]+1}) | Kurtz={kurtz_found} | Militar_muerto={soldier_dead} | Salida_pisada={exit_seen}")
        print("Perceptos:", percept_to_string(per))
        stim = active_stimuli(per)
        print("Estímulos activos:", "(ninguno)" if len(stim) == 0 else ", ".join(stim))

        if can_exit(pos, kurtz_found, world):
            print(paint(">>> Estás en la salida con Kurtz: pulsa 'x' para SALIR.", kc.YELLOW_DARK))

        if show_maps:
            print_all_maps(world, beliefs, pos, soldier_dead, kurtz_found=kurtz_found, on_exit=(pos == world['S']))

        #Tablero al final (más visual)
        print_palace_board(
            world, pos, visited, safe_set, beliefs, per,
            risk_cutoff=risk_cutoff,
            soldier_dead=soldier_dead,
            kurtz_found=kurtz_found,
            exit_seen=exit_seen,
            seen=seen
        )

        cmd = input("\nAcción (w/a/s/d mover, g granada, x salir, m mapas, q terminar): ").strip().lower()

        if cmd == "q":
            print("Saliendo.")
            return

        if cmd == "m":
            show_maps = not show_maps
            continue

        if cmd == "x":
            if can_exit(pos, kurtz_found, world):
                print(paint("\n¡Misión completada! Has salido con Kurtz.", kc.GREEN))
                return
            print("No puedes salir todavía (tienes que estar en la salida y llevar a Kurtz).")
            continue

        if cmd == "g":
            if grenade_used:
                print("Ya has usado la granada.")
                continue

            dch = input("Dirección granada (w/a/s/d): ").strip().lower()
            if dch not in KEY_TO_DIR:
                print("Dirección inválida.")
                continue

            grenade_used = True
            direction = KEY_TO_DIR[dch]

            soldier_alive, soldier_dead, grito_now, target = throw_grenade(
                world, pos, direction, soldier_alive, soldier_dead
            )

            if target is not None:
                if grito_now:
                    grito_flag = True
                    print(paint("¡Granada acertada! Militar neutralizado. (Grito=1)", kc.GREEN))
                else:
                    soldier_forbidden.add(target)
                    print("Granada lanzada. No hay grito -> el militar NO estaba en esa celda.")
            continue

        if cmd not in KEY_TO_DIR:
            print("Comando inválido.")
            continue

        direction = KEY_TO_DIR[cmd]
        dr, dc = DIRS[direction]
        new_pos = (pos[0] + dr, pos[1] + dc)

        if not in_bounds(n, new_pos[0], new_pos[1]):
            print("Hay pared, no puedes salir del palacio.")
            continue

        outcome = step_into(world, new_pos, soldier_alive and (not soldier_dead))
        pos = new_pos
        visited.add(pos)

        if outcome == "TRAP":
            print(paint("\nHas caído en una trampa. Fin de la misión.", kc.RED))
            return
        if outcome == "MILITAR":
            print(paint("\nEl militar te ha abatido. Fin de la misión.", kc.RED))
            return



#Main


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


def run():
    """Punto de entrada del programa: configura parámetros, genera el mundo y lanza modo manual o automático.
    
        Returns:
            None: Ejecuta la interacción por consola.
        
    """
    print("\n=== Palacio Bayesiano (Parte 2) ===\n")
    #Colores: en esta parte se usan siempre (como en kurtz)
    kc.USE_COLOR = True

    mode = ask_choice("Modo [manual/auto] (enter=manual): ", ["manual", "auto"], default="manual")
    auto = (mode == "auto")

    search_method = "astar"
    verbose = True
    if auto:
        search_method = ask_choice("Búsqueda [bfs/dfs/gbfs/astar] (enter=astar): ",
                                   ["bfs", "dfs", "gbfs", "astar"], default="astar")
        verbose = not ask_yes_no("¿Modo silencioso (menos prints)? [s/n] (enter=n): ", default=False)



    while True:
        seed_in = input(f"Semilla (enter aleatorio) [{DEFAULT_SEED}]: ").strip()
        if seed_in == "":
            seed = None
            break
        try:
            seed = int(seed_in)
            break
        except ValueError:
            print("La semilla debe ser un número entero (o ENTER para aleatorio).")

    rng = random.Random(seed)

    #n >= 3 para que quepan las tres trampas, el soldado, la salida y Kurtz
    n = ask_int(f"Tamaño n (enter={DEFAULT_N}): ", default=DEFAULT_N, min_value=3)

    risk_cutoff = ask_float(f"Umbral de riesgo p (enter={DEFAULT_RISK_CUTOFF}): ",
                            default=DEFAULT_RISK_CUTOFF, min_value=0.0, max_value=1.0)

    start = (0, 0)
    world = make_world(n, rng, start)

    if auto:
        show_all_maps = ask_yes_no("¿En AUTO quieres imprimir TODOS los mapas numéricos además del tablero general? [s/n] (enter=n): ", default=False)
        res = run_auto(world, risk_cutoff,
                       search_method=search_method,
                       steps_max=500,
                       verbose=verbose,
                       show_maps=show_all_maps)
        print("\nResultado:", res["result"])
        print("Posiciones:", res["positions"])
        print("Acciones  :", res["actions"])
    else:
        run_manual(world, risk_cutoff)


if __name__ == "__main__":
    enable_utf8_output()
    run()
