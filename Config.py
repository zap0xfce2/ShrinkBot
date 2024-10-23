import json
import os
from Logger import log, setup_logging

CONFIG_FILE = "shrinkbot_config.json"
DEFAULT_MIN_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB
DEFAULT_TIME_FORMAT = "%d.%m.%Y %H:%M:%S"  # Deutsches Zeitformat
DEFAULT_LOG_FILE = "shrinkbot.log"  # Name der Logdatei


def load_config():
    """
    Lädt die Konfiguration aus der JSON-Datei.
    Falls die Datei nicht existiert oder beschädigt ist, wird eine Standardkonfiguration erstellt.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Stelle sicher, dass die erforderlichen Felder existieren
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
                if "settings" not in config:
                    config["settings"] = {
                        "min_size_bytes": DEFAULT_MIN_SIZE_BYTES,
                        "time_format": DEFAULT_TIME_FORMAT,
                        "log_file": DEFAULT_LOG_FILE,
                        "pause_times": [],
                    }
                else:
                    if "pause_times" not in config["settings"]:
                        config["settings"]["pause_times"] = []
                # Aktualisiere das Logging basierend auf den Einstellungen
                setup_logging(
                    config["settings"].get("time_format", DEFAULT_TIME_FORMAT),
                    config["settings"].get("log_file", DEFAULT_LOG_FILE),
                )
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
                "settings": {
                    "min_size_bytes": DEFAULT_MIN_SIZE_BYTES,
                    "time_format": DEFAULT_TIME_FORMAT,
                    "log_file": DEFAULT_LOG_FILE,
                    "pause_times": [],
                },
            }
    # Standardkonfiguration, wenn die Datei nicht existiert
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
        "settings": {
            "min_size_bytes": DEFAULT_MIN_SIZE_BYTES,
            "time_format": DEFAULT_TIME_FORMAT,
            "log_file": DEFAULT_LOG_FILE,
            "pause_times": [],
        },
    }


def save_config(config):
    """
    Speichert die aktuelle Konfiguration in die JSON-Datei.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log(f"Fehler beim Speichern der Konfiguration: {e}")


def reset_config(config):
    """
    Setzt den letzten Pfad zurück, behält aber Blacklist und Statistics bei.
    """
    try:
        config["last_path"] = None
        save_config(config)
    except Exception as e:
        log(f"Fehler beim Zurücksetzen des last_path in der Konfiguration: {e}")


def reset_statistics(config):
    """
    Setzt die Statistiken zurück.
    """
    try:
        config["statistics"] = {
            "total_input_mb": 0.0,
            "total_savings_mb": 0.0,
            "total_files_converted": 0,
            "total_conversion_time_seconds": 0.0,
            "per_directory_savings_mb": {},
        }
        save_config(config)
        log("Statistiken wurden zurückgesetzt.")
    except Exception as e:
        log(f"Fehler beim Zurücksetzen der Statistiken: {e}")


def reset_blacklist(config):
    """
    Setzt die Blacklist zurück.
    """
    try:
        config["blacklist"] = []
        save_config(config)
        log("Blacklist wurde zurückgesetzt.")
    except Exception as e:
        log(f"Fehler beim Zurücksetzen der Blacklist: {e}")
