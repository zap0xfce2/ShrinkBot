def format_number(value):
    """
    Formatiert eine Zahl auf zwei Dezimalstellen mit Komma als Dezimaltrennzeichen.

    Args:
        value (float): Die zu formatierende Zahl.

    Returns:
        str: Die formatierte Zahl als String.
    """
    return f"{value:.2f}".replace(".", ",")


def format_time(seconds):
    """
    Formatiert eine Zeitdauer in Sekunden in eine lesbare Form (Sekunden, Minuten, Stunden).

    Args:
        seconds (float): Die Zeitdauer in Sekunden.

    Returns:
        str: Die formatierte Zeitdauer.
    """
    if seconds < 60:
        return f"{format_number(seconds)} Sekunden"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{format_number(minutes)} Minuten"
    else:
        hours = seconds / 3600
        return f"{format_number(hours)} Stunden"
