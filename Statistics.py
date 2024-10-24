from Logger import log
from Config import save_config


def update_statistics(config, directory, input_mb, savings_mb, conversion_time):
    """
    Aktualisiert die Statistiken basierend auf den Ersparnissen einer Datei.
    """
    # Stelle sicher, dass nur positive Ersparnisse hinzugefügt werden
    if savings_mb <= 0:
        return

    stats = config["statistics"]
    stats["total_input_mb"] += input_mb
    stats["total_savings_mb"] += savings_mb
    stats["total_files_converted"] += 1
    stats["total_conversion_time_seconds"] += conversion_time

    # Aktualisiere die Ersparnis pro Verzeichnis
    if directory not in stats["per_directory_savings_mb"]:
        stats["per_directory_savings_mb"][directory] = 0.0
    stats["per_directory_savings_mb"][directory] += savings_mb

    save_config(config)


def display_directory_savings(config, directory):
    """
    Zeigt die Ersparnis für ein bestimmtes Verzeichnis an.
    """
    stats = config["statistics"]
    savings_mb = stats["per_directory_savings_mb"].get(directory, 0.0)
    if savings_mb > 0:
        log(f"Ersparnis für Verzeichnis '{directory}': {savings_mb:.2f} MB")


def display_total_statistics(config):
    """
    Zeigt die Gesamtstatistiken an.
    """
    stats = config["statistics"]
    total_input_mb = stats["total_input_mb"]
    total_savings_mb = stats["total_savings_mb"]
    total_files = stats["total_files_converted"]
    total_time = stats["total_conversion_time_seconds"]

    if total_input_mb > 0:
        total_savings_percent = (total_savings_mb / total_input_mb) * 100
    else:
        total_savings_percent = 0.0

    if total_files > 0:
        average_time = total_time / total_files
    else:
        average_time = 0.0

    log(f"Gesamtersparnis: {total_savings_mb:.2f} MB ({total_savings_percent:.2f}%)")
    log(f"Durchschnittliche Konvertierungszeit pro Datei: {average_time:.2f} Sekunden")