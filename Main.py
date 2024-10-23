import os
import json
import sys
import argparse
import subprocess
import logging
from datetime import datetime

# Aufruf
# screen -S ShrinkBot -m python Main.py <Pfad>

# Konfigurationsvariablen
CRAWL_FILE = "shrinkbot_crawl.json"
MIN_SIZE_BYTES = 8 * 1024 * 1024  # 500 MB
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


def load_crawl_file():
    if os.path.exists(CRAWL_FILE):
        try:
            with open(CRAWL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            log("Crawlfile ist beschädigt. Starte von vorne.")
            return {"last_path": None}
    return {"last_path": None}


def save_crawl_file(config):
    try:
        with open(CRAWL_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log(f"Fehler beim Speichern der Konfiguration: {e}")


def reset_crawl_file():
    try:
        with open(CRAWL_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_path": None}, f, ensure_ascii=False, indent=4)
        log("Crawlfile wurde zurückgesetzt.")
    except Exception as e:
        log(f"Fehler beim Zurücksetzen der Konfiguration: {e}")


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
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    if size > MIN_SIZE_BYTES:
                        size_mb = size / (1024 * 1024)
                        log(f"Gefunden: {file} ({size_mb:.2f} MB)")
                        yield file_path
                except OSError as e:
                    log(f"Fehler beim Zugriff auf {file_path}: {e}")

        config["last_path"] = root
        save_crawl_file(config)


def process_mkv(file_path):
    directory, filename = os.path.split(file_path)
    name, _ = os.path.splitext(filename)
    output_filename = f"{name}.mp4"
    output_path = os.path.join(directory, output_filename)

    command = [
        "docker",
        "run",
        "--rm",
        "--cpuset-cpus",
        "0,1",  # Nur einen CPU Core verwenden
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
    try:
        result = subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        log(f"Konvertierung abgeschlossen: {output_path}")

        # Überprüfen, ob das Ausgabefile existiert und größer als 0 Bytes ist
        if not os.path.exists(output_path):
            log(f"Ausgabedatei wurde nicht erstellt: {output_path}")
            return

        output_size = os.path.getsize(output_path)
        if output_size == 0:
            log(f"Ausgabedatei ist leer: {output_path}")
            os.remove(output_path)
            log(f"Leere Ausgabedatei gelöscht: {output_path}")
            return

        # Vergleiche Dateigrößen
        try:
            input_size = os.path.getsize(file_path)
            if output_size < input_size:
                os.remove(file_path)
                log(f"MKV-Datei Gelöscht: {file_path}")
            else:
                os.remove(output_path)
                log(f"MP4-Datei Gelöscht: {output_path}")
        except OSError as e:
            log(f"Fehler beim Vergleichen oder Löschen der Dateien: {e}")

    except subprocess.CalledProcessError as e:
        log(f"Fehler bei der Verarbeitung von {file_path}: {e}")


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
    config = load_crawl_file()

    if not os.path.exists(start_path):
        log(f"Startpfad existiert nicht: {start_path}")
        sys.exit(1)

    min_size_mb = MIN_SIZE_BYTES / (1024 * 1024)
    log("ShrinkBot 1.0 gestartet!")
    log(f"Nur MKV-Dateien größer als {min_size_mb:.2f} MB werden verarbeitet.")
    log(f"Durchsuche: {start_path}")

    try:
        for mkv_file in find_mkv_files(start_path, config):
            process_mkv(mkv_file)
    except KeyboardInterrupt:
        log("Vorgang unterbrochen. Fortschritt gespeichert.")
    except Exception as e:
        log(f"Ein Fehler ist aufgetreten: {e}")
    else:
        log("Durchsuchen abgeschlossen.")
        reset_crawl_file()


if __name__ == "__main__":
    main()
