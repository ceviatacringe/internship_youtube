import os
import re
import sys
import time
import win32gui
import win32con
import threading
from log import logger
import pygetwindow as gw
from audio_measure import *
from selenium import webdriver
from record_screen import record_screen
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class YouTubeAutomation:
    def __init__(self, adblock=True, fullscreen=False, showall=False):
        self.unavailable = True # If the video is private/invalid url/deleted
        self.driver = None
        self.window = None
        self.showall = showall
        self.lastdownload = time.time()
        self.chrome_options = Options()
        self.lock = threading.Lock()
        self.adblock = adblock
        self.download_file_name = None
        self.fullscreen = fullscreen
        self.path = None
        self.firstlink = True # Keep browser hidden till first link is requested
        logger.info(f"Running Adblock: {self.adblock}, Fullscreen: {self.fullscreen}, Show everything: {self.showall}")

    def initialize_driver(self):
        """
        Preloads the driver for a smooother run and adds Ublock Origin.
        """
            # Determine current path
        if getattr(sys, 'frozen', False):
            # If the script is compiled
            self.path = os.path.dirname(sys.executable)
        else:
            # If running the script in Python
            self.path = os.path.dirname(os.path.abspath(__file__))
        self.download_folder = os.path.join(self.path, 'Downloads')
            # Make sure folder exists
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
            # Configure settings
        logger.info(f"Download folder: {self.download_folder}")
        self.chrome_options.add_argument("--start-minimized")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--enable-automation")
        #If you want to change the name, also changed the getWindowsWithTitle below
        self.chrome_options.add_argument("--window-name=AlexBrowser")      
        # Install pre-downloaded uBlock Origin extension crx
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_folder,  # Set the default download directory
            "download.prompt_for_download": False,  # Do not prompt for download
            "download.directory_upgrade": True,  # Auto upgrade directory if needed
            "safebrowsing.enabled": True  # Disable safe browsing
            })
        if self.adblock:
            try:
                logger.info("Loading Adblock...")
                crx_path = os.path.join(self.path, 'ublock.crx')
                logger.info(f"Assumed Ublock crx path: {crx_path}")
                self.chrome_options.add_extension(crx_path)
                self.adblock = True
                logger.info("Successfully loaded Adblock.")
            except Exception as e:
                logger.error(f"Error loading Adblock: {e}")
                logger.info(f"Switching to non-Adblock mode.")
        else:
            logger.info("Running non-Adblock mode.")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        self.driver.delete_all_cookies() # Clean up old caches from previous runs in case it didn't properly exit
        logger.info("Cleaned up cache.")
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
        
        # Start the popup monitor thread
        if not hasattr(self, "popup_monitor_thread"):
            self.popup_monitor_thread = threading.Thread(target=self.monitor_ads)
            self.popup_monitor_thread.daemon = True  # Ensures it doesn't block the program
            logger.info("Starting monitor thread")
            self.popup_monitor_thread.start()
        
        # Reveal the window if it's the first time opening a link
        if self.firstlink:
            self.show_window()
            self.firstlink = False
        self.check_available()
        # Fullscreen if need be
        if self.fullscreen:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys('f')
        # Sometimes the video doesn't start automatically, so we click the play button
        if not self.unavailable and not self.adblock:
            try:
                big_play_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ytp-large-play-button"))
                )
                big_play_button.click()
                logger.info("Clicked play button.")
            except:
                logger.info("Unable to find play button.")


    def youtube_search(self, keyword):
        # Start the popup monitor thread
        if not hasattr(self, "popup_monitor_thread") and not self.adblock:
            self.popup_monitor_thread = threading.Thread(target=self.monitor_ads)
            self.popup_monitor_thread.daemon = True  # Ensures it doesn't block the program
            logger.info("Starting monitor thread")
            self.popup_monitor_thread.start()
        if not self.driver.current_url.startswith("https://www.youtube"):
            self.driver.get("https://www.youtube.com/")
        try:
            # Find and click search bar
            time.sleep(1.5)
            search_bar = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "search_query"))
            )
            search_bar.click()
            logger.info("Clicked on the YouTube search bar.")
            time.sleep(0.3)
            # Clear previous text
            search_bar.send_keys(Keys.CONTROL + 'a')
            search_bar.send_keys(Keys.BACKSPACE)
            # Type the keyword and press Enter
            search_bar.send_keys(keyword + Keys.RETURN)
            logger.info(f"Typed '{keyword}' in the search bar and submitted.")

            # Wait for the video results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "video-title"))
            )
            logger.info("Video results are loaded.")
            # Explicit delay for slower machines (it bugs on bad hardware)
            time.sleep(0.8)
            # Find the first non-ad video
            videos = self.driver.find_elements(By.XPATH, "//a[@id='video-title']")
            for video in videos:
                aria_label = video.get_attribute("aria-label")
                if "Ad" not in (aria_label or ""):  # Skip sponsored content
                    video.click()
                    logger.info("Clicked on the first non-sponsored video.")
                    break
            else:
                logger.error("No non-sponsored video found.")
                
        except (NoSuchElementException, TimeoutException) as e:
            logger.error(f"An error occurred during search or video selection: {e}")
        # Reveal the window if it's the first time opening a link
        if self.firstlink:
            self.show_window()
            self.firstlink = False
        logger.info("Checking for fullscreen.")
        if self.fullscreen:
            logger.info("Fullscreening.")
            time.sleep(0.5)
            self.driver.find_element(By.TAG_NAME, 'body').send_keys('f')


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


    def monitor_ads(self):
        logger.info("Started popup monitor.")
        while True:
            time.sleep(0.3)
            with self.lock:
                if not self.adblock:
                    try:
                        # Check for "Skip" button for ads
                        skip_ad_button = WebDriverWait(self.driver, 0.5).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, "ytp-skip-ad-button"))
                        )
                        skip_ad_button.click()
                        logger.info("Clicked 'Skip Ad' button.")

                    except TimeoutException:
                        # No ad skip button found
                        pass


    def check_available(self):
        """
        Checks if the current video is private by searching for the specific element.
        """
        try:
            # Wait for the element to be visible
            element = WebDriverWait(self.driver, 7).until(
                EC.visibility_of_element_located((By.ID, 'channel-name'))
            )
            
            # Check if the element is displayed
            if element.is_displayed():
                self.unavailable = False
                logger.info("The video is displayed.")
            else:
                self.unavailable = True
                logger.info("The video is not displayed.")
        
        except TimeoutException:
            self.unavailable = True
            logger.info("Timeout reached while waiting for the element.")
        except Exception as e:
            # Catch other exceptions that might occur
            self.unavailable = True
            logger.info(f"An error occurred: {e}")


    def hide_window(self):
        """
        Completely hides the window.
        """
        if not self.showall:
            win32gui.ShowWindow(self.window._hWnd, win32con.SW_HIDE)
            logger.info("Fully hiding window.")

    def show_window(self):
        """
        Restores and maximizes the Chrome window, and brings it to the foreground.
        """
        if not self.showall:
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
        logger.info("Clearing local and session storage.")
        try:
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            logger.error(f"Failed. {e}")
        logger.info("Cleaning up cache files.")
        self.driver.delete_all_cookies()
        logger.info("Shutting down.")
        self.driver.quit()
        self.driver = None


    def get_latest_download(self, checktime) -> str:
        """
        Get the last downloaded file name (from the script's download folder),
        Loop check it until the download is complete, then return.
        """
        with self.lock:
            logger.info(f"Looking for latest file in: {self.download_folder}")
            print("This might take a while until the download is finished.")
            while True:
                # Get the list of files in the download folder
                # Exclude .crdownload (still downloading) and temp files
                files = [
                    os.path.join(self.download_folder, f)
                    for f in os.listdir(self.download_folder)
                    if os.path.isfile(os.path.join(self.download_folder, f)) and f.endswith('.mp4')
                ]

                if not files:  # If the list is empty, skip to the next iteration
                    logger.debug("No files found in Downloads folder.")
                    time.sleep(checktime) # Wait before checking again
                    continue

                # Find the latest file based on creation time
                latest_file = max(files, key=os.path.getctime)

                file_creation_time = os.path.getctime(latest_file)
                # Check if the file was downloaded this download function run
                if self.lastdownload - file_creation_time <= 0:
                    self.download_file_name = os.path.basename(latest_file)
                    return
                else:
                    time.sleep(checktime)  # Wait before checking again


    def download(self, link):
        """
        Download video to this script/exe's folder using a site convertor,
        Then put it up in online-video-cutter for editing.
        """
        self.lastdownload = time.time()
        self.hide_window()
        with self.lock:
            self.driver.get("https://cnvmp3.com/")
        # Find and click input bar
        try:
            search_bar = WebDriverWait(self.driver, 4).until(
                EC.element_to_be_clickable((By.ID, "video-url"))
            )
            search_bar.click()
            logger.info("Clicked input bar")
            logger.info("Typing URL.")
            search_bar.send_keys(link + Keys.RETURN)
        except TimeoutException:
            logger.error(f"Couldn't find search bar.")
            self.firstlink = True
            return
        # Wait for the download button to appear
        try:
            try:
                # Wait for the dropdown button to be clickable and click it
                quality_display = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "quality-select-display"))
                )
            # They really like changing class names on this site for some reason
            except (TimeoutError, NoSuchElementException):
                quality_display = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "format-select-list"))
                ) 
            quality_display.click()  # Open the dropdown
            logger.info("Clicked on dropdown")
            # Select the quality from the dropdown menu
            try: 
                mp4_option = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@class='quality-select-options' and text()='MP4']"))
                )
            except (TimeoutError, NoSuchElementException):
                mp4_option = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@class='format-select-options' and text()='MP4']"))
                )
            mp4_option.click()  # Select MP4
            logger.info("Selected MP4 format")
            convert_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "converter-button-container"))
            )
            convert_button.click()
            logger.info("Clicked convert")
        except Exception as e:
            logger.error(f"Failed: {e}")
        logger.info("Loading gif.")
        # Make and switch to new tab
        self.driver.switch_to.new_window('tab')
        self.driver.get("file://" + os.path.abspath("spinner.gif"))
        # fixme: find a way to defocus URL so it doesn't look hovered
        time.sleep(3)
        # Scan for download finish
        self.get_latest_download(0.2)
        self.driver.close() # Close gif tab and return
        self.driver.switch_to.window(self.driver.window_handles[0])
        logger.info("Opening editor.")
        self.show_window() 
        with self.lock:
            self.driver.get("https://online-video-cutter.com/")
        # Wait till ovc loads
        wait = WebDriverWait(self.driver, 10)
        upload_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.picker-dropdown__input[type="file"]')))
        # Send the video path to the input field
        video_path = os.path.join(self.download_folder,self.download_file_name)
        logger.info(f"Attempting to send {video_path} to the editor.")
        with self.lock:
            upload_input.send_keys(video_path)
        logger.info("Editor ready.")
        logger.info("Maximizing window.")
        self.driver.maximize_window()
        # Reset window hider in case the user starts opening links again.
        self.firstlink == True

    def record(self, recordtime,):
        if self.unavailable:
            logger.info("The video is unavailable, cancelling recording.")
        else:
            logger.info("Starting recording.")
            measure_audio(record_screen(recordtime))

    def full_auto(self, keyword, recordtime):
        """
        I didn't want to make this originally, but you insisted that you wanted
        the script to be fully automatic, so I added an option for that here.
        """
        self.initialize_driver()
        time.sleep(1)
        self.youtube_search(keyword)
        self.check_available()
        self.record(recordtime)
        self.clean_up()