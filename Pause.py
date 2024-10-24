# Pause.py

from datetime import datetime, timedelta
from Logger import log
import time as time_module


def check_pause_time(settings, statistics):
    """
    Überprüft, ob die aktuelle Zeit innerhalb eines Pausenzeitraums liegt.
    Wenn ja, wartet bis der Pausenzeitraum vorbei ist und loggt die Gesamtersparnis und
    die durchschnittliche Konvertierungszeit pro Datei.

    Args:
        settings (dict): Die Einstellungen aus der Konfigurationsdatei.
        statistics (dict): Die aktuellen Statistiken aus der Konfigurationsdatei.
    """
    pause_times = settings.get("pause_times", [])
    if not pause_times:
        return  # Keine Pausen definiert

    now = datetime.now().time()

    for pause in pause_times:
        start_str = pause.get("start")
        end_str = pause.get("end")
        try:
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
        except ValueError:
            log(f"Ungültiges Zeitformat in Pausenzeit: {pause}")
            continue  # Überspringe ungültige Pausenzeiten

        if start_time < end_time:
            # Pausenzeit innerhalb eines Tages
            if start_time <= now < end_time:
                wait_until = datetime.combine(datetime.today(), end_time)
                wait_seconds = (wait_until - datetime.now()).total_seconds()
                log(
                    f"Pausenzeit aktiv: {start_str} - {end_str}. Warte {wait_seconds / 60:.0f} Minuten."
                )
                # Logge die aktuellen Statistiken
                log_current_statistics(statistics)
                time_module.sleep(wait_seconds)
                log("Pausenzeit beendet. Fortsetzung der Verarbeitung.")
                return  # Nach der Pause weiterarbeiten
        else:
            # Pausenzeit über Mitternacht hinweg
            if now >= start_time or now < end_time:
                if now >= start_time:
                    # Pause bis zum Ende der heutigen Pausezeit
                    wait_until = datetime.combine(
                        datetime.today() + timedelta(days=1), end_time
                    )
                else:
                    # Pause bis zum Ende der morgigen Pausezeit
                    wait_until = datetime.combine(datetime.today(), end_time)
                wait_seconds = (wait_until - datetime.now()).total_seconds()
                log(
                    f"Pausenzeit aktiv: {start_str} - {end_str}. Warte {wait_seconds / 60:.0f} Minuten."
                )
                # Logge die aktuellen Statistiken
                log_current_statistics(statistics)
                time_module.sleep(wait_seconds)
                log("Pausenzeit beendet. Fortsetzung der Verarbeitung.")
                return  # Nach der Pause weiterarbeiten


def log_current_statistics(statistics):
    """
    Loggt die aktuellen Gesamtersparnis und die durchschnittliche Konvertierungszeit pro Datei.

    Args:
        statistics (dict): Die aktuellen Statistiken aus der Konfigurationsdatei.
    """
    total_savings_mb = statistics.get("total_savings_mb", 0.0)
    total_files = statistics.get("total_files_converted", 0)
    total_time = statistics.get("total_conversion_time_seconds", 0.0)

    if total_files > 0:
        average_time = total_time / total_files
    else:
        average_time = 0.0

    log(f"Gesamtersparnis: {total_savings_mb:.2f} MB")
    log(f"Durchschnittliche Konvertierungszeit pro Datei: {average_time:.2f} Sekunden")