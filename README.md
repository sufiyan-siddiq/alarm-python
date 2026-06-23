# alarm.py

A small interactive alarm clock for the terminal. Launch it and a live clock
fills the screen; single keystrokes manage your alarms. No third-party
dependencies — just the Python standard library.

## Requirements

- Python 3.10+
- A terminal that understands ANSI escape codes (Windows Terminal, PowerShell,
  macOS Terminal, iTerm, and most Linux terminals all qualify).

## Run

```
python alarm.py
```

The clock appears immediately. Controls:

| Key | Action                          |
|-----|---------------------------------|
| `a` | add an alarm (time, label, repeat) |
| `t` | toggle an alarm on/off          |
| `d` | delete an alarm                 |
| `q` | quit                            |

When an alarm is due it flashes a banner and beeps; choose **(s)nooze** (5
minutes) or **(d)ismiss**.

## Repeat options

`once`, `daily`, `weekdays` (Mon–Fri), `weekends` (Sat–Sun). A `once` alarm
disables itself after it fires.

## Configuration

Edit `config.json` (same folder as `alarm.py`):

```json
{
  "alarms_path": "~/.alarm_clock/alarms.json",
  "clock_color": "cyan"
}
```

- **`alarms_path`** — where alarms are stored. `~` expands to your home folder.
- **`clock_color`** — the colour of the big clock. One of:

  `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`,
  `bright_red`, `bright_green`, `bright_yellow`, `bright_blue`,
  `bright_magenta`, `bright_cyan`.

  Any unrecognised value falls back to `cyan`.

Missing or invalid config falls back to the defaults above.

## Data

Alarms are stored as JSON, e.g.:

```json
{
  "alarms": [
    { "label": "Wake up", "time": "07:30", "repeat": "weekdays",
      "enabled": true, "snoozed_until": null, "last_triggered": null }
  ]
}
```

## Known limitation

Alarms only ring while `alarm.py` is running — it is a foreground clock, not a
background daemon. Firing alarms when the app is closed would mean OS-specific
scheduling (Task Scheduler / cron / launchd), which is deliberately out of
scope here.

## Build a standalone executable

You can bundle the app into a single executable with
[PyInstaller](https://pyinstaller.org) so it runs without a Python install:

```
pip install pyinstaller
pyinstaller --onefile --name alarm alarm.py
```

The result is `dist/alarm.exe` on Windows (or `dist/alarm` on macOS/Linux).
PyInstaller does not cross-compile, so build on the OS you want to target — run
the command on Windows to get a `.exe`.

### Running the executable

Launch it from a terminal (Windows Terminal or PowerShell) or by double-clicking:

```
alarm.exe
```

To change the storage path, clock colour, or snooze length, place a `config.json`
**next to the executable** — the app looks for it beside `alarm.exe`, just as it
looks beside `alarm.py` when run as a script. Without one, the built-in defaults
apply. (Your alarms themselves live at `alarms_path`, which defaults to your home
folder and is independent of where the executable sits.)

> The first launch of an unsigned executable may trigger a Windows SmartScreen
> notice ("More info" → "Run anyway") or an antivirus prompt. That is expected
> for PyInstaller builds and not specific to this app.