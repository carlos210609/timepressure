"""Natural operator controls for TimePressure."""

import re


def parse_pressure_command(message, current=1.5):
    text = " ".join(str(message).strip().lower().split())
    aliases = {
        "aumente a pressão": 2.5,
        "aumentar a pressão": 2.5,
        "mais pressão": 2.5,
        "pressão máxima": 3.0,
        "pressao maxima": 3.0,
        "modo pressão máxima": 3.0,
        "modo pressao maxima": 3.0,
        "pressão normal": 1.5,
        "pressao normal": 1.5,
        "pressão padrão": 1.5,
        "pressao padrao": 1.5,
        "diminua a pressão": 1.0,
        "diminuir a pressão": 1.0,
        "menos pressão": 1.0,
    }
    for phrase, value in aliases.items():
        if phrase in text:
            return value

    match = re.search(r"(?:press(?:ão|ao)|multiplicador)\s*(?:para|em|=)?\s*(\d+(?:[\.,]\d+)?)\s*(x|%)?", text)
    if match:
        value = float(match.group(1).replace(",", "."))
        if match.group(2) == "%":
            value /= 100
        return max(1.0, min(3.0, value))

    return None


def pressure_status(current):
    return f"Multiplicador de pressão: {current:.2f}x (limite seguro: 1.00x–3.00x)."
