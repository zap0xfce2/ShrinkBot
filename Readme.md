# ShrinkBot

Ein Python-Skript, das durch eine Dateistruktur crawlt und mit ffmpeg MKV-Dateien in MP4-Dateien umwandelt.

## Benutzung über die Befehlszeile

Entweder mit `screen -S ShrinkBot -m python Main.py <Pfad>` oder direkt mit `python Main.py <Pfad>`

## Übergabeparameter

- `--reset-stats` setzt die Statistiken zurück
- `--reset-blacklist` setzt die Blacklist zurück

## Konfigurationsdatei

Hier ein Beispiel für eine Konfigurationsdatei. Wenn diese nicht vorhanden ist, wird eine mit Standardwerten angelegt.

```json
{
    "last_path": null,
    "blacklist": [
        "/path/to/my/file.mkv"
    ],
    "statistics": {
        "total_input_mb": 0,
        "total_savings_mb": 0,
        "total_files_converted": 0,
        "total_conversion_time_seconds": 0,
        "per_directory_savings_mb": {
            "/path/to/my/folder": 0
        }
    },
    "settings": {
        "min_size_bytes": 52428800,
        "time_format": "%d.%m.%Y %H:%M:%S",
        "log_file": "shrinkbot.log",
        "pause_times": [
            {
                "start": "18:00",
                "end": "22:00"
            },
            {
                "start": "03:30",
                "end": "06:00"
            }
        ]
    }
}
