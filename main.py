from gui import YouTubeApp
from player import *

# Full auto mode is what you asked for (Project mode)
# Set this to False for my intended use.
FULL_AUTO_MODE = False


if __name__ == "__main__":
    if FULL_AUTO_MODE:
        auto = YouTubeAutomation(fullscreen=True, showall=True, adblock= True)
        auto.full_auto("Floating Darkness Tatsh", 10)
    else:
        app = YouTubeApp()
        app.mainloop()


# Certified most useless main.py of all time