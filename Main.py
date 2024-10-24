#
# Erstellt von Zap0xfce2 im Oktober 2024
#
import os
import sys
import argparse
from Config import load_config, reset_statistics, reset_blacklist, reset_config
from Logger import log
from Processor import find_mkv_files, process_mkv
from Pause import check_pause_time
from Statistics import display_directory_savings, display_total_statistics
from Utils import format_number

VERSION = "v241024"


def main():
    parser = argparse.ArgumentParser(description="ShrinkBot")
    parser.add_argument(
        "start_path",
        nargs="?",
        default=os.getcwd(),
        help="Startverzeichnis für den ShrinkBot (standardmäßig aktuelles Verzeichnis)",
    )
    parser.add_argument(
        "--reset-stats",
        action="store_true",
        help="Setze die Statistiken zurück",
    )
    parser.add_argument(
        "--reset-blacklist",
        action="store_true",
        help="Setze die Blacklist zurück",
    )
    args = parser.parse_args()

    start_path = args.start_path
    config = load_config()

    # Handhabung der Reset-Parameter
    if args.reset_stats or args.reset_blacklist:
        if args.reset_stats:
            reset_statistics(config)
        if args.reset_blacklist:
            reset_blacklist(config)
        sys.exit(0)

    if not os.path.exists(start_path):
        log(f"Startpfad existiert nicht: {start_path}")
        sys.exit(1)

    settings = config.get("settings", {})
    min_size_mb = settings.get("min_size_bytes", 500 * 1024 * 1024) / (1024 * 1024)
    log(f"ShrinkBot {VERSION} gestartet!")
    log(
        f"Nur MKV-Dateien größer als {format_number(min_size_mb)} MB werden verarbeitet."
    )
    log(f"Durchsuche: {start_path}")

    current_directory = None
    try:
        for mkv_file in find_mkv_files(start_path, config):
            # Überprüfe vor der Verarbeitung auf Pausenzeiten
            check_pause_time(settings, config.get("statistics", {}))

            directory = os.path.dirname(mkv_file)
            # Überprüfe, ob wir in ein neues Verzeichnis wechseln
            if current_directory and directory != current_directory:
                # Zeige die Ersparnis für das vorherige Verzeichnis an
                display_directory_savings(config, current_directory)
            current_directory = directory

            process_mkv(mkv_file, config)

        # Nach der Schleife, zeige die Ersparnis für das letzte Verzeichnis an
        if current_directory:
            display_directory_savings(config, current_directory)

    except KeyboardInterrupt:
        log("Vorgang unterbrochen. Fortschritt gespeichert.")
    except Exception as e:
        log(f"Ein Fehler ist aufgetreten: {e}")
    else:
        log("Durchsuchen abgeschlossen.")
        # Setze last_path zurück nach erfolgreichem Durchlauf
        reset_config(config)

    # Zeige die Gesamtstatistiken an
    display_total_statistics(config)


if __name__ == "__main__":
    main()
