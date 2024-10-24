import os
import subprocess
from Logger import log
from Config import save_config
from Statistics import update_statistics
from Utils import format_number
import time as time_module  # Importiert für die Zeitmessung und Sleep


def find_mkv_files(start_path, config):
    """
    Durchsucht rekursiv das Startverzeichnis nach MKV-Dateien, die nicht auf der Blacklist stehen
    und größer als die minimale Größe sind.
    """
    settings = config.get("settings", {})
    min_size_bytes = settings.get("min_size_bytes", 500 * 1024 * 1024)
    started = False
    for root, _, files in os.walk(start_path):
        if config.get("last_path"):
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
                if file_path in config.get("blacklist", []):
                    log(
                        f"Überspringe {file_path} da die Datei auf der Blacklist steht."
                    )
                    continue
                try:
                    size = os.path.getsize(file_path)
                    if size > min_size_bytes:
                        size_mb = size / (1024 * 1024)
                        log(f"Gefunden: {file} ({format_number(size_mb)} MB)")
                        yield file_path
                except OSError as e:
                    log(f"Fehler beim Zugriff auf {file_path}: {e}")

        config["last_path"] = root
        save_config(config)


def process_mkv(file_path, config):
    """
    Konvertiert eine MKV-Datei zu MP4 mittels Docker-FFmpeg, vergleicht die Dateigrößen,
    löscht die Originaldatei bei Ersparnis oder löscht die konvertierte Datei und fügt sie zur Blacklist hinzu.
    Aktualisiert die Statistiken bei positiver Ersparnis.
    """
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
    start_time = time_module.time()  # Startzeit für die Konvertierung
    try:
        subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        end_time = time_module.time()  # Endzeit nach der Konvertierung
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
                log(f"Original MKV-Datei gelöscht: {file_path}")
            else:
                os.remove(output_path)
                log(f"Konvertierte MP4-Datei gelöscht: {output_path}")

                # Füge die Datei zur Blacklist hinzu
                if file_path not in config["blacklist"]:
                    config["blacklist"].append(file_path)
                    save_config(config)
                    log(
                        f"Die Konvertierung bringt keine Ersparnis. Blacklisteintrag erstellt."
                    )

            # Nur positive Ersparnisse loggen und in die Statistik aufnehmen
            if savings_mb > 0 and savings_percent > 0:
                # Logge die Ersparnis pro Datei
                log(
                    f"Ersparnis für {filename}: {format_number(savings_mb)} MB ({format_number(savings_percent)}%)"
                )

                # Aktualisiere die Statistik
                update_statistics(
                    config, directory, input_size_mb, savings_mb, conversion_time
                )

            return (
                (savings_mb, savings_percent, conversion_time)
                if savings_mb > 0
                else None
            )

        except OSError as e:
            log(f"Fehler beim Vergleichen oder Löschen der Dateien: {e}")
            return None

    except subprocess.CalledProcessError as e:
        log(f"Fehler bei der Verarbeitung von {file_path}: {e.stderr.decode('utf-8')}")
        return None
