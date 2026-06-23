import json, os, sys, time, platform
from datetime import date, datetime, timedelta
from pathlib import Path

IS_WIN = platform.system() == "Windows"

RESET, BOLD, DIM = "\x1b[0m", "\x1b[1m", "\x1b[2m"
RED, GREEN, YELLOW, WHITE, BG_RED = "\x1b[31m", "\x1b[32m", "\x1b[33m", "\x1b[97m", "\x1b[41m"
CLEAR, HIDE, SHOW = "\x1b[2J\x1b[H", "\x1b[?25l", "\x1b[?25h"  # clear+home; hide/show cursor
COLORS = {"black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34,
          "magenta": 35, "cyan": 36, "white": 37, "bright_red": 91,
          "bright_green": 92, "bright_yellow": 93, "bright_blue": 94,
          "bright_magenta": 95, "bright_cyan": 96}

REPEAT_LABEL = {"once": "Once", "daily": "Daily", "weekdays": "Mon-Fri", "weekends": "Sat-Sun"}
REPEATS = tuple(REPEAT_LABEL)

# config lives next to the script - or next to the .exe when frozen by PyInstaller
_BASE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
_cfg = {"alarms_path": "~/.alarm_clock/alarms.json", "clock_color": "bright_cyan", "snooze_minutes": 5}
try:
    _cfg.update(json.loads((_BASE / "config.json").read_text("utf-8")))
except (FileNotFoundError, json.JSONDecodeError):
    pass

STORE = Path(os.path.expanduser(_cfg["alarms_path"]))
CLOCK = f"\x1b[{COLORS.get(_cfg['clock_color'], 96)}m"
SNOOZE = _cfg["snooze_minutes"]


def beep():
    if IS_WIN:
        import winsound; winsound.Beep(880, 250)
    else:
        sys.stdout.write("\a"); sys.stdout.flush()


def load():
    try:
        alarms = json.loads(STORE.read_text("utf-8")).get("alarms", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    for a in alarms:
        a.pop("id", None)
    return alarms


def save(alarms):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps({"alarms": alarms}, indent=2), "utf-8")


def parse_hhmm(raw):
    try:
        hh, mm = map(int, raw.split(":"))
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return f"{hh:02d}:{mm:02d}"
    except ValueError:
        pass
    return None


def is_due(a, now):
    if not a.get("enabled", True):
        return False
    if a.get("snoozed_until"):
        return now >= datetime.fromisoformat(a["snoozed_until"])
    if a.get("last_triggered") == now.strftime("%Y-%m-%d"):
        return False
    t = parse_hhmm(a.get("time", ""))
    if not t or t != now.strftime("%H:%M"):
        return False
    rep, wd = a.get("repeat", "daily"), now.weekday()
    if rep == "weekdays":
        return wd <= 4
    if rep == "weekends":
        return wd >= 5
    return True


FONT = {
    "0": ("███", "█ █", "█ █", "█ █", "███"), "1": ("  █", "  █", "  █", "  █", "  █"),
    "2": ("███", "  █", "███", "█  ", "███"), "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"), "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("███", "█  ", "███", "█ █", "███"), "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"), "9": ("███", "█ █", "███", "  █", "███"),
    ":": ("   ", " █ ", "   ", " █ ", "   "), " ": ("   ",) * 5,
}


def big(text):
    return ["  ".join(FONT[c][r] for c in text) for r in range(5)]


def out(s):
    sys.stdout.write(s); sys.stdout.flush()


def draw(now, alarms, colon_on):
    t = now.strftime("%H:%M:%S")
    if not colon_on:
        t = t.replace(":", " ")
    lines = ["\x1b[H\x1b[K\n"]
    for row in big(t):
        lines.append(f"\x1b[K   {CLOCK}{row}{RESET}\n")
    lines.append(f"\x1b[K\n\x1b[K   {DIM}{now:%A, %d %B %Y}{RESET}\n\x1b[K\n")
    if not alarms:
        lines.append(f"\x1b[K   {DIM}No alarms - press 'a' to add one.{RESET}\n")
    else:
        lines.append(f"\x1b[K   {BOLD}{'#':<3}{'TIME':<7}{'REPEAT':<9}{'STATUS':<18}LABEL{RESET}\n")
        for i, a in enumerate(alarms, 1):
            if not a.get("enabled", True):
                status, col = "off", DIM
            elif a.get("snoozed_until") and now < datetime.fromisoformat(a["snoozed_until"]):
                status, col = f"snoozed -> {datetime.fromisoformat(a['snoozed_until']):%H:%M}", YELLOW
            else:
                status, col = "active", GREEN
            lines.append(f"\x1b[K   {i:<3}{a['time']:<7}{REPEAT_LABEL.get(a.get('repeat'), '?'):<9}"
                         f"{col}{status:<18}{RESET}{a['label']}\n")
    lines.append(f"\x1b[K\n\x1b[K   {BOLD}[a]{RESET}dd  {BOLD}[t]{RESET}oggle  "
                 f"{BOLD}[d]{RESET}elete  {BOLD}[q]{RESET}uit\n\x1b[J")
    out("".join(lines))


def fire(alarms, i):
    a = alarms[i]
    banner = f"   >> ALARM - {a['label']} ({a['time']}) <<"
    for n in range(6):
        out("\r\x1b[K" + (BG_RED + WHITE + BOLD if n % 2 == 0 else RED + BOLD) + banner + RESET)
        beep(); time.sleep(0.4)
    out("\n\n")
    while True:
        choice = input(f"   (s)nooze {SNOOZE}m / (d)ismiss: ").strip().lower()
        if choice in ("s", "snooze"):
            a["snoozed_until"] = (datetime.now() + timedelta(minutes=SNOOZE)).isoformat()
            a["last_triggered"] = None
            return save(alarms)
        if choice in ("", "d", "dismiss"):
            a["snoozed_until"] = None
            a["last_triggered"] = date.today().isoformat()
            if a.get("repeat") == "once":
                a["enabled"] = False
            return save(alarms)


def add_alarm():
    print(BOLD + "New alarm" + RESET)
    t = parse_hhmm(input("   Time (HH:MM): ").strip())
    if not t:
        print("   Invalid time - use HH:MM."); time.sleep(1); return
    label = input("   Label [Alarm]: ").strip() or "Alarm"
    rep = input(f"   Repeat {'/'.join(REPEATS)} [daily]: ").strip().lower() or "daily"
    alarms = load()
    alarms.append({"label": label, "time": t, "repeat": rep if rep in REPEATS else "daily",
                   "enabled": True, "snoozed_until": None, "last_triggered": None})
    save(alarms)


def pick(action):
    """Show the alarms numbered and return (alarms, index) or (None, None)."""
    alarms = load()
    if not alarms:
        print("   No alarms."); time.sleep(0.8); return None, None
    for i, a in enumerate(alarms, 1):
        print(f"   {i}  {a['time']}  {a['label']}")
    raw = input(f"   {action} #: ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(alarms):
        return alarms, int(raw) - 1
    return None, None


def toggle_alarm():
    alarms, i = pick("Toggle")
    if alarms:
        alarms[i]["enabled"] = not alarms[i].get("enabled", True)
        if not alarms[i]["enabled"]:
            alarms[i]["snoozed_until"] = None
        save(alarms)


def delete_alarm():
    alarms, i = pick("Delete")
    if alarms:
        del alarms[i]
        save(alarms)


if IS_WIN:
    import msvcrt

    def read_key():
        return msvcrt.getwch() if msvcrt.kbhit() else None

    def raw_on(): pass
    def raw_off(): pass
else:
    import termios, tty, select
    _fd, _saved = sys.stdin.fileno(), None

    def read_key():
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

    def raw_on():
        global _saved
        _saved = termios.tcgetattr(_fd)
        tty.setcbreak(_fd)

    def raw_off():
        if _saved is not None:
            termios.tcsetattr(_fd, termios.TCSADRAIN, _saved)


def modal(body):
    """Drop out of the live clock, run a prompt, then go back."""
    raw_off(); out(SHOW + CLEAR)
    try:
        body()
    finally:
        raw_on(); out(HIDE + CLEAR)


def run():
    if IS_WIN:
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    raw_on(); out(HIDE + CLEAR)
    actions = {"a": add_alarm, "t": toggle_alarm, "d": delete_alarm}
    try:
        while True:
            now, alarms = datetime.now(), load()
            due = next((i for i, a in enumerate(alarms) if is_due(a, now)), None)
            if due is not None:
                modal(lambda: fire(alarms, due)); continue
            draw(now, alarms, now.second % 2 == 0)
            key = (read_key() or "").lower()
            if key == "q":
                break
            if key in actions:
                modal(actions[key])
            time.sleep(0.2)
    finally:
        raw_off(); out(SHOW + CLEAR)


if __name__ == "__main__":
    run()