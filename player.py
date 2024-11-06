import os
import sys
import time
import win32gui
import win32con
import threading
from log import logger
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class YouTubeAutomation:
    def __init__(self):
        self.unavailable = True # If the video is private/invalid url/deleted
        self.driver = None
        self.window = None
        self.chrome_options = Options()
        self.adblock = False

    def initialize_driver(self):
        """
        Preloads the driver for a smooother run and adds Ublock Origin.
        """
        self.chrome_options.add_argument("--start-minimized")
        self.chrome_options.add_argument("--disable-gpu")
        #If you want to change the name, also changed the getWindowsWithTitle below
        self.chrome_options.add_argument("--window-name=AlexBrowser")      
        # Install pre-downloaded uBlock Origin extension crx
        try:
            logger.info("Loading Adblock...")
            if getattr(sys, 'frozen', False):
                # If the script is compiled
                base_path = os.path.dirname(sys.executable)
            else:
                # If running the script in Python
                base_path = os.path.dirname(os.path.abspath(__file__))
    
            crx_path = os.path.join(base_path, 'ublock.crx')
            logger.info(f"Assumed Ublock crx path: {crx_path}")

            self.chrome_options.add_extension(crx_path)
            self.adblock = True
            logger.info("Successfully loaded Adblock.")
        except Exception as e:
            logger.error(f"Error loading Adblock: {e}")
            logger.info(f"Switching to non-adblock mode.")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        self.driver.delete_all_cookies() # Clean up old caches from previous runs in case it didn't properly exit
        self.window = gw.getWindowsWithTitle("AlexBrowser")[0]
        self.hide_window() # Hide the window then reveal it later when a link is opened
        self.driver.get('https://www.youtube.com/')
        logger.info("Rejecting cookies.")
        self.reject_cookies()

    def start_video(self, link):
        """
        Check if the video is available, then start playing it if it doesn't start automatically.
        """
        self.driver.get(link)
        logger.info(f"Opening link: {link}")
        self.show_window()
        self.check_available()
        # Sometimes the video doesn't start automatically, this clicks the play button
        # (Happens frequently with adblock disabled)
        logger.info("Looking for play button.")
        if not self.unavailable:
            try:
                    big_play_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "ytp-large-play-button"))
                    )
                    big_play_button.click()
                    logger.info("Clicked play button.")
            except Exception as e:
                    logger.info(f"Unable to find button: {e}") 

    def reject_cookies(self):
        """
        Waits for the 'Reject all' button on YouTube to be clickable and clicks it.
        """
        try:
            # Wait for the 'Reject all' button to be clickable
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Reject all']]"))
            )
            button.click()
            logger.info("Clicked the 'Reject all' button (cookies).")
        except NoSuchElementException:
            logger.error("Reject cookies page/button not found.")
        except Exception as e:
            logger.info(f"Error in cookie reject: {e}")

    def monitor_popups(self):
        logger.info("Started popup monitor.")
        while True:
            time.sleep(0.1)
            if not self.unavailable:
                if not self.adblock:
                    try:
                        # Check for "Skip" button for ads
                        skip_ad_button = WebDriverWait(self.driver, 0.4).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, "ytp-skip-ad-button"))
                        )
                        skip_ad_button.click()
                        logger.info("Clicked 'Skip Ad' button.")

                    except Exception:
                        # No ad skip button found
                        pass

                try:
                    # Check for "Are you still watching?" button
                    still_watching_button = WebDriverWait(self.driver, 0.2).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
                    )
                    still_watching_button.click()
                    logger.info("Clicked 'Are you still watching?' confirmation.")

                except Exception:
                    pass

                try:
                    # Check for any potential error popups
                    error_popup = WebDriverWait(self.driver, 0.2).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'error')]"))
                    )
                    self.driver.refresh()  # Refresh page to attempt recovery
                    logger.info("Error detected, refreshing page to recover.")

                except Exception:
                    # No error popup found; continue loop
                    pass


    def check_available(self):
        """
        Checks if the current video is private by searching for the specific element.
        """
        try:
            # Wait for the element to be visible
            element = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, 'channel-name'))
            )
            
            # Check if the element is displayed
            if element.is_displayed():
                self.unavailable = False
                logger.info("The element is displayed.")
            else:
                self.unavailable = True
                logger.info("The element is not displayed.")
        
        except TimeoutException:
            # Handle the exception if the element is not found within the given time
            self.unavailable = True
            logger.info("Timeout reached while waiting for the element.")
            # Optionally, take a screenshot for debugging
            self.driver.save_screenshot('timeout_screenshot.png')
        except Exception as e:
            # Catch other exceptions that might occur
            self.unavailable = True
            logger.info(f"An error occurred: {e}")


    def hide_window(self):
        """
        Completely hides the window.
        """
        win32gui.ShowWindow(self.window._hWnd, win32con.SW_HIDE)
        logger.info("Fully hiding window.")

    def show_window(self):
        """
        Restores and maximizes the Chrome window, and brings it to the foreground.
        """
        try:
            win32gui.ShowWindow(self.window._hWnd, win32con.SW_RESTORE)
            logger.info("Attempting to reveal browser window.")

            try:
                self.window.activate()
                logger.info("Bringing browser window to foreground.")
            except Exception as e:
                logger.warning(f"Failed to activate window normally: {e}")

                # Attempt alternative method if activate() fails
                win32gui.SetForegroundWindow(self.window._hWnd)
                logger.info("Using alternative SetForegroundWindow method.")

            # Ensure the window is maximized
            self.driver.maximize_window()
            logger.info("Maximizing driver window through Selenium.")
        except Exception as e:
            logger.error(f"Error in show_window: {e}")


    def clean_up(self):
        """
        Deletes all cookies and closes the browser session.
        """
        logger.info("Cleaning up cache files.")
        self.driver.delete_all_cookies()
        logger.info("Shutting down.")
        self.driver.quit()

    def run(self):
        """
        Executes the entire sequence of actions.
        """
        logger.info("Starting up...")
        self.initialize_driver()
        logger.info("Driver loaded.")
        time.sleep(1)
        popup_monitor_thread = threading.Thread(target=self.monitor_popups)
        popup_monitor_thread.daemon = True
        logger.info("Starting monitor thread")
        popup_monitor_thread.start()
        self.start_video('https://www.youtube.com/watch?v=zZZ-FZ03Sxk')

        time.sleep(500) # remove this later 
        self.clean_up()


if __name__ == "__main__":
    # Create an instance of the automation class and run the script
    automation = YouTubeAutomation()
    automation.run()
