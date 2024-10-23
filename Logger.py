import logging
import sys


def setup_logging(time_format, log_file):
    """
    Konfiguriert das Logging basierend auf den übergebenen Einstellungen.
    """
    logging.getLogger().handlers = []  # Entferne bestehende Handler
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt=time_format,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def log(message):
    """
    Loggt eine Nachricht mit dem INFO-Level.
    """
    logging.info(message)
