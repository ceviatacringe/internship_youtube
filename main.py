from gui import YouTubeApp
from player import *
import socket
from log import logger
    
# Full auto mode is what you asked for (Project mode)
# Set this to False for my intended use.
FULL_AUTO_MODE = False

def check_youtube_connection() -> bool:
    try:
        socket.create_connection(("www.youtube.com", 443), timeout=5)
        return True
    except OSError:
        return False


if __name__ == "__main__":
    if check_youtube_connection():
        if FULL_AUTO_MODE:
            auto = YouTubeAutomation(fullscreen=True, showall=True, adblock= True)
            auto.full_auto("Floating Darkness Tatsh", 10)
        else:
            app = YouTubeApp()
            app.mainloop()
    else:
        logger.error("No youtube connection. Aborting.")
        input("Press enter to close...")


# Certified most useless main.py of all time