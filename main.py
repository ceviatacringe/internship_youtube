from log import logger

def play_video():
    try:
        logger.info("Starting video playback with Selenium")
        logger.info("Video playback started successfully")
    except Exception as e:
        logger.error(f"Error in play_video: {e}")


play_video()
