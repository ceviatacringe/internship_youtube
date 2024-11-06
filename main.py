import requests
from log import logger
from player import YouTubeAutomation
import time

# Function to check YouTube connectivity
def check_youtube_accessibility():
    try:
        requests.get("https://www.youtube.com", timeout=3).raise_for_status()
        logger.info("YouTube is accessible.")
        return True
    except requests.RequestException:
        logger.info("YouTube is inaccessible, probably no internet connection.")
        return False

# Only run the automation if YouTube is accessible
if __name__ == "__main__":
    if check_youtube_accessibility():
        automation = YouTubeAutomation()
        automation.run()
        automation.start_video("https://www.youtube.com/watch?v=zZZ-FZ03Sxk")
        time.sleep(5)
        automation.clean_up()
    else:
        logger.info("Exiting program due to lack of connectivity.")
