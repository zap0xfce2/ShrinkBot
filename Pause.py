from datetime import datetime, timedelta
from Logger import log
import time as time_module


def check_pause_time(settings):
    """
    Überprüft, ob die aktuelle Zeit innerhalb eines Pausenzeitraums liegt.
    Wenn ja, wartet bis der Pausenzeitraum vorbei ist.
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
                time_module.sleep(wait_seconds)
                log("Pausenzeit beendet. Fortsetzung der Verarbeitung.")
                return  # Nach der Pause weiterarbeiten
