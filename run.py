import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

class BotReloader(FileSystemEventHandler):
    def __init__(self, script):
        self.script = script
        self.process = None
        self.start_bot()

    def start_bot(self):
        if self.process:
            self.process.kill()
        print("🚀 Запускаю бота...")
        self.process = subprocess.Popen([sys.executable, self.script])

    def on_modified(self, event):
        if event.src_path.endswith(self.script):
            print("♻️ Зміни у коді виявлено, перезапускаю...")
            self.start_bot()

if __name__ == "__main__":
    script_name = "bot.py"  # твій бот
    event_handler = BotReloader(script_name)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()
    observer.join()
