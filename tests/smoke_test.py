"""
Smoke tests de los tres programas (kurtz.py, palacio.py y river.py).

Qué hace este script:
-Lanza cada programa como un proceso aparte, con una semilla fija y las respuestas
 ya preparadas en la entrada estándar
-Comprueba que el proceso termina con código 0 y sin traza de error
-Comprueba que en la salida aparecen las marcas esperadas (cabeceras, resumen final...)

Por qué así:
-Los tres programas son interactivos, así que la única forma de ejercitarlos de
 principio a fin sin tocar el código es alimentarles la entrada estándar
-No se comparan números concretos: solo estructura. Los valores dependen de la
 semilla y no interesa que el test se rompa por un decimal

No hace falta instalar nada aparte de las dependencias del proyecto.

Uso:
    python tests/smoke_test.py
"""

import pathlib
import subprocess
import sys


RAIZ = pathlib.Path(__file__).resolve().parent.parent

#En modo auto, kurtz.py puede preguntar qué celda insegura expandir cuando no queda
#ninguna ruta demostrablemente segura. Respondemos siempre "1" (el primer candidato).
RESPUESTAS_KURTZ = "1\n" * 60

#En modo auto, palacio.py puede ofrecer subir el umbral de riesgo. Respondemos "s".
RESPUESTAS_PALACIO = "s\n" * 60

#(nombre, script, entrada estándar, marcas que deben aparecer en la salida)
CASOS = [
    (
        "river / semilla 42 / mapa por defecto",
        "river.py",
        "42\n\n\n\n\nn\n5\nn\n",
        ["Mapa generado", "Tabla de valores V(s)", "Política óptima", "Resumen final de simulación"],
    ),
    (
        "river / semilla 7 / 8x7, islas peligrosas, descuento 0.95",
        "river.py",
        "7\nn\n8\n7\n3\n0.95\ns\nn\n4\nn\n",
        ["islas_peligrosas=True", "Tabla de valores V(s)", "Resumen final de simulación"],
    ),
    (
        "river / semilla 1 / 4x3 sin islas",
        "river.py",
        "1\nn\n4\n3\n0\n1.0\nn\ns\n2\nn\n",
        ["Mapa generado", "Resumen final de simulación"],
    ),
    (
        "kurtz / semilla 3 / auto A*",
        "kurtz.py",
        "auto\nastar\nn\n3\n6\n" + RESPUESTAS_KURTZ,
        ["=== PLANIFICACIÓN A KURTZ ===", "PALACIO (conocimiento del agente)", "=== RESUMEN AUTO ==="],
    ),
    (
        "kurtz / semilla 11 / auto BFS",
        "kurtz.py",
        "auto\nbfs\nn\n11\n6\n" + RESPUESTAS_KURTZ,
        ["=== PLANIFICACIÓN A KURTZ ===", "=== RESUMEN AUTO ==="],
    ),
    (
        "kurtz / semilla 5 / auto DFS, modo silencioso",
        "kurtz.py",
        "auto\ndfs\ns\n5\n7\n" + RESPUESTAS_KURTZ,
        ["=== RESUMEN AUTO ==="],
    ),
    (
        "kurtz / semilla 4 / manual",
        "kurtz.py",
        "manual\n4\n6\nd\ns\ns\nd\nq\n",
        ["PALACIO (conocimiento del agente)", "Percepto:"],
    ),
    (
        "palacio / semilla 42 / auto A*",
        "palacio.py",
        "auto\nastar\nn\n42\n6\n\nn\n" + RESPUESTAS_PALACIO,
        ["=== PLANIFICACIÓN A KURTZ (p=0.20) ===", "Resultado:"],
    ),
    (
        "palacio / semilla 8 / auto BFS, umbral 0.3",
        "palacio.py",
        "auto\nbfs\nn\n8\n6\n0.3\nn\n" + RESPUESTAS_PALACIO,
        ["=== PLANIFICACIÓN A KURTZ (p=0.30) ===", "Resultado:"],
    ),
    (
        "palacio / semilla 2 / manual, con mapas numéricos",
        "palacio.py",
        "manual\n2\n6\n\nd\ns\nm\nq\n",
        ["Posición:", "Perceptos:"],
    ),
    (
        "palacio / entrada inválida en tamaño y umbral",
        "palacio.py",
        "manual\n2\nabc\n1\n6\nnope\n2\n0.2\nq\n",
        ["Entrada no válida", "Valor fuera de rango", "Posición:"],
    ),
]


def ejecuta(script, entrada):
    """Lanza un programa del proyecto y devuelve (código de salida, salida completa).

    Args:
        script (str): Nombre del fichero a ejecutar, relativo a la raíz del repositorio.
        entrada (str): Texto que se envía por la entrada estándar.

    Returns:
        tuple[int, str]: Código de retorno y salida (stdout y stderr juntos).
    """
    proceso = subprocess.run(
        [sys.executable, script],
        cwd=RAIZ,
        input=entrada.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
    )
    return proceso.returncode, proceso.stdout.decode("utf-8", errors="replace")


def main():
    """Ejecuta todos los casos y devuelve el código de salida del script.

    Returns:
        int: 0 si todos los casos pasan, 1 si falla alguno.
    """
    #La salida se fuerza a UTF-8 por el mismo motivo que en los tres programas:
    #al redirigirla a un fichero en Windows se usaría cp1252 y saltaría UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    fallos = []

    for nombre, script, entrada, marcas in CASOS:
        codigo, salida = ejecuta(script, entrada)

        problemas = []
        if codigo != 0:
            problemas.append(f"código de salida {codigo}")
        if "Traceback (most recent call last)" in salida:
            problemas.append("traza de error en la salida")
        for marca in marcas:
            if marca not in salida:
                problemas.append(f"falta la marca {marca!r}")

        if problemas:
            fallos.append((nombre, problemas, salida))
            print(f"FALLO  {nombre}")
            for p in problemas:
                print(f"         - {p}")
        else:
            print(f"OK     {nombre}")

    print("")
    print(f"{len(CASOS) - len(fallos)}/{len(CASOS)} casos correctos.")

    if fallos:
        #Solo en caso de fallo imprimimos el final de la salida, para poder depurar en CI.
        for nombre, _, salida in fallos:
            print("")
            print(f"--- últimas líneas de: {nombre} ---")
            print("\n".join(salida.splitlines()[-25:]))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
