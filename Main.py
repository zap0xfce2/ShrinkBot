import os
import json
import sys
import argparse
import subprocess
import logging
from datetime import datetime
import time  # Importiert für die Zeitmessung

# Aufruf
# screen -S ShrinkBot -m python Main.py <Pfad>

# Konfigurationsvariablen
CONFIG_FILE = "shrinkbot_config.json"
MIN_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB
TIME_FORMAT = "%d.%m.%Y %H:%M:%S"  # Deutsches Zeitformat
LOG_FILE = "shrinkbot.log"  # Name der Logdatei

# Konfiguriere das Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt=TIME_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


def log(message):
    logging.info(message)


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Stelle sicher, dass die Blacklist und Statistics existieren
                if "blacklist" not in config:
                    config["blacklist"] = []
                if "statistics" not in config:
                    config["statistics"] = {
                        "total_input_mb": 0.0,
                        "total_savings_mb": 0.0,
                        "total_files_converted": 0,
                        "total_conversion_time_seconds": 0.0,
                        "per_directory_savings_mb": {},
                    }
                return config
        except json.JSONDecodeError:
            log("Konfigurationsdatei ist beschädigt. Starte von vorne.")
            return {
                "last_path": None,
                "blacklist": [],
                "statistics": {
                    "total_input_mb": 0.0,
                    "total_savings_mb": 0.0,
                    "total_files_converted": 0,
                    "total_conversion_time_seconds": 0.0,
                    "per_directory_savings_mb": {},
                },
            }
    return {
        "last_path": None,
        "blacklist": [],
        "statistics": {
            "total_input_mb": 0.0,
            "total_savings_mb": 0.0,
            "total_files_converted": 0,
            "total_conversion_time_seconds": 0.0,
            "per_directory_savings_mb": {},
        },
    }


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log(f"Fehler beim Speichern der Konfiguration: {e}")


def reset_config(config):
    try:
        config["last_path"] = None
        # Behalte die Blacklist und Statistics bei
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log(f"Fehler beim Zurücksetzen des last_path in der Konfiguration: {e}")


def find_mkv_files(start_path, config):
    started = False
    for root, dirs, files in os.walk(start_path):
        if config["last_path"]:
            if not started:
                if os.path.abspath(root) == os.path.abspath(config["last_path"]):
                    started = True
                    log(f"Fortsetzen ab: {root}")
                else:
                    continue
        else:
            started = True

        for file in files:
            if file.lower().endswith(".mkv"):
                file_path = os.path.abspath(os.path.join(root, file))
                if file_path in config["blacklist"]:
                    log(f"Überspringen da auf Blacklist: {file_path}")
                    continue
                try:
                    size = os.path.getsize(file_path)
                    if size > MIN_SIZE_BYTES:
                        size_mb = size / (1024 * 1024)
                        log(f"Gefunden: {file} ({size_mb:.2f} MB)")
                        yield file_path
                except OSError as e:
                    log(f"Fehler beim Zugriff auf {file_path}: {e}")

        config["last_path"] = root
        save_config(config)


def process_mkv(file_path, config):
    directory, filename = os.path.split(file_path)
    name, _ = os.path.splitext(filename)
    output_filename = f"{name}.mp4"
    output_path = os.path.join(directory, output_filename)

    command = [
        "docker",
        "run",
        "--rm",
        # "--cpuset-cpus",
        # "0,1",  # Nur einen CPU Core verwenden
        "-v",
        f"{directory}:/config",
        "linuxserver/ffmpeg",
        "-y",
        "-loglevel",
        "error",  # Reduziere die Ausgabe von ffmpeg
        "-i",
        f"/config/{filename}",
        "-c:v",
        "libx264",
        "-b:v",
        "4M",
        "-vf",
        "scale=1920:1080,fps=30",
        "-c:a",
        "copy",
        "-c:s",
        "mov_text",
        "-map",
        "0:v",
        "-map",
        "0:a",
        "-map",
        "0:s?",
        f"/config/{output_filename}",
    ]

    log(f"Konvertierung von {filename} läuft...")
    start_time = time.time()  # Startzeit für die Konvertierung
    try:
        result = subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        end_time = time.time()  # Endzeit nach der Konvertierung
        conversion_time = end_time - start_time
        log(f"Konvertierung abgeschlossen: {output_path}")

        # Überprüfen, ob das Ausgabefile existiert und größer als 0 Bytes ist
        if not os.path.exists(output_path):
            log(f"Ausgabedatei wurde nicht erstellt: {output_path}")
            return None
        output_size = os.path.getsize(output_path)
        if output_size == 0:
            log(f"Ausgabedatei ist leer: {output_path}")
            os.remove(output_path)
            log(f"Leere Ausgabedatei gelöscht: {output_path}")
            return None

        # Vergleiche Dateigrößen
        try:
            input_size = os.path.getsize(file_path)
            input_size_mb = input_size / (1024 * 1024)
            output_size_mb = output_size / (1024 * 1024)
            savings_mb = input_size_mb - output_size_mb
            savings_percent = (
                (savings_mb / input_size_mb) * 100 if input_size_mb > 0 else 0
            )

            if output_size < input_size:
                os.remove(file_path)
                log(f"MKV-Datei Gelöscht: {file_path}")
            else:
                os.remove(output_path)
                log(f"MP4-Datei Gelöscht: {output_path}")

                # Füge die Datei zur Blacklist hinzu
                if file_path not in config["blacklist"]:
                    config["blacklist"].append(file_path)
                    save_config(config)
                    log(f"Datei zur Blacklist hinzugefügt: {file_path}")

            # Nur positive Ersparnisse loggen und in die Statistik aufnehmen
            if savings_mb > 0 and savings_percent > 0:
                # Logge die Ersparnis pro Datei
                log(
                    f"Ersparnis für {filename}: {savings_mb:.2f} MB ({savings_percent:.2f}%)"
                )

                # Aktualisiere die Statistik
                update_statistics(
                    config, directory, input_size_mb, savings_mb, conversion_time
                )

            return (
                savings_mb,
                savings_percent,
                conversion_time if savings_mb > 0 else None,
            )

        except OSError as e:
            log(f"Fehler beim Vergleichen oder Löschen der Dateien: {e}")
            return None

    except subprocess.CalledProcessError as e:
        log(f"Fehler bei der Verarbeitung von {file_path}: {e}")
        return None


def update_statistics(config, directory, input_mb, savings_mb, conversion_time):
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
    stats = config["statistics"]
    savings_mb = stats["per_directory_savings_mb"].get(directory, 0.0)
    if savings_mb > 0:
        log(f"Ersparnis für Verzeichnis '{directory}': {savings_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description="ShrinkBot")
    parser.add_argument(
        "start_path",
        nargs="?",
        default=os.getcwd(),
        help="Startverzeichnis für den ShrinkBot (standardmäßig aktuelles Verzeichnis)",
    )
    args = parser.parse_args()

    start_path = args.start_path
    config = load_config()

    if not os.path.exists(start_path):
        log(f"Startpfad existiert nicht: {start_path}")
        sys.exit(1)

    min_size_mb = MIN_SIZE_BYTES / (1024 * 1024)
    log("ShrinkBot 1.0 gestartet!")
    log(f"Nur MKV-Dateien größer als {min_size_mb:.2f} MB werden verarbeitet.")
    log(f"Durchsuche: {start_path}")

    current_directory = None
    try:
        for mkv_file in find_mkv_files(start_path, config):
            directory = os.path.dirname(mkv_file)
            # Überprüfe, ob wir in ein neues Verzeichnis wechseln
            if current_directory and directory != current_directory:
                # Zeige die Ersparnis für das vorherige Verzeichnis an
                display_directory_savings(config, current_directory)
            current_directory = directory

            result = process_mkv(mkv_file, config)
            # result enthält (savings_mb, savings_percent, conversion_time) oder None
            # Weitere Verarbeitung kann hier erfolgen, falls nötig

        # Nach der Schleife, zeige die Ersparnis für das letzte Verzeichnis an
        if current_directory:
            display_directory_savings(config, current_directory)

    except KeyboardInterrupt:
        log("Vorgang unterbrochen. Fortschritt gespeichert.")
    except Exception as e:
        log(f"Ein Fehler ist aufgetreten: {e}")
    else:
        log("Durchsuchen abgeschlossen.")
        reset_config(config)

    # Zeige die Gesamtstatistiken an
    display_total_statistics(config)


def display_total_statistics(config):
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


if __name__ == "__main__":
    main()
