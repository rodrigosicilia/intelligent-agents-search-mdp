#kurtz_colors.py
#Colores para imprimir el mapa en la terminal (sin usar librerías externas)

#Si tu terminal no soporta colores o ves símbolos raros, pon esto en False
USE_COLOR = True

#Código para “volver a la normalidad” (sin color)
RESET = "\033[0m"

#Colores básicos ANSI (suelen funcionar en casi cualquier terminal)
GREEN = "\033[32m"
BLUE = "\033[34m"
ORANGE = "\033[33m"      #Usamos amarillo como “naranja” para mantenerlo simple
RED = "\033[31m"

#Amarillos para la salida: clarito (brillante) vs normal
YELLOW_DARK = "\033[33m"
YELLOW_LIGHT = "\033[93m"


def paint(text: str, color_code: str) -> str:
    """Devuelve el texto envuelto en un color ANSI (si USE_COLOR=True).

    Idea:
    -Si USE_COLOR=False, devolvemos el texto sin tocar.
    -Si USE_COLOR=True, devolvemos: COLOR + texto + RESET.

    Args:
        text (str):Texto ya formateado que queremos colorear.
        color_code (str):Código ANSI del color a aplicar.

    Returns:
        str:Texto coloreado o texto original si USE_COLOR=False.
    """
    if (not USE_COLOR) or (not color_code):
        return text
    return color_code + text + RESET


def color_for_tag(tag: str) -> str:
    """
    Asigna un color ANSI según la etiqueta impresa en la celda.

    La función decide el color a partir del 'tag' lógico (sin padding). Si USE_COLOR=False,
    devuelve una cadena vacía para que el llamador imprima sin colores.

    Args:
        tag (str): Etiqueta de la celda (por ejemplo: "v", "✓", "P?", "P!", "S?", "E!", "CW"...).

    Returns:
        str: Código ANSI del color correspondiente, o "" si no se colorea.
    """
    if not USE_COLOR:
        return ""

    if tag.startswith("CW"):
        return GREEN

    if tag == "v":
        return GREEN
    if tag == "✓":
        return BLUE

    if ("P!" in tag) or ("S!" in tag):
        return RED
    if ("P?" in tag) or ("S?" in tag):
        return ORANGE

    if tag == "E" or ("E!" in tag):
        return YELLOW_DARK
    if "E?" in tag:
        return YELLOW_LIGHT

    return ""


def colorize_cell(padded_text: str, raw_tag: str) -> str:
    """Aplica color a una celda ya formateada a ancho fijo.

    Esto es clave:
    -Primero en kurtz.py centramos/recortamos el texto con _fmt_cell(...)
    -Luego aquí lo coloreamos
    Así no se rompe el centrado (porque los códigos ANSI “cuentan” como caracteres
    si coloreas antes de centrar).

    Args:
        padded_text (str):Texto ya centrado a ancho fijo (lo que se imprime).
        raw_tag (str):Etiqueta real sin padding (la que usamos para decidir color).

    Returns:
        str:Texto ya coloreado listo para imprimir.
    """
    return paint(padded_text, color_for_tag(raw_tag))
