import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
import pygetwindow as gw
import win32gui
import win32con
import threading


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
            crx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ublock.crx')
            self.chrome_options.add_extension(crx_path)
            self.adblock = True
            print("Successfully loaded adblock.")
        except:
            #This should never really happen
            print("Failed to load adblock")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        self.driver.delete_all_cookies() # Clean up old caches from previous runs in case it didn't properly exit
        self.window = gw.getWindowsWithTitle("AlexBrowser")[0]
        self.hide_window() # Hide the window then reveal it later when a link is opened
        self.driver.get('https://www.youtube.com/')
        self.reject_cookies()

    def start_video(self, link):
        """
        Check if the video is available, then start playing it if it doesn't start automatically.
        """
        self.driver.get(link)
        self.show_window()
        self.check_available()
        # Sometimes the video doesn't start automatically, this clicks the play button
        # (Happens frequently with adblock disabled)
        if not self.unavailable:
            try:
                    big_play_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "ytp-large-play-button"))
                    )
                    big_play_button.click()
                    print("Clicked play button")
            except:
                    print("Play button not found") 

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
            print("Clicked the 'Reject all' button.")
        except NoSuchElementException:
            print("Button not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def monitor_popups(self):
        while True:
            time.sleep(0.1)
            if not self.unavailable:
                if not self.adblock:
                    try:
                        print("Looking for ad")
                        # Check for "Skip" button for ads
                        skip_ad_button = WebDriverWait(self.driver, 0.4).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, "ytp-skip-ad-button"))
                        )
                        skip_ad_button.click()
                        print("Clicked 'Skip Ad' button.")

                    except Exception:
                        # No ad skip button found
                        pass

                try:
                    # Check for "Are you still watching?" button
                    still_watching_button = WebDriverWait(self.driver, 0.2).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
                    )
                    still_watching_button.click()
                    print("Clicked 'Are you still watching?' confirmation.")

                except Exception:
                    pass

                try:
                    # Check for any potential error popups
                    error_popup = WebDriverWait(self.driver, 0.2).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'error')]"))
                    )
                    self.driver.refresh()  # Refresh page to attempt recovery
                    print("Error detected, refreshing page to recover.")

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
                print("The element is displayed.")
            else:
                self.unavailable = True
                print("The element is not displayed.")
        
        except TimeoutException:
            # Handle the exception if the element is not found within the given time
            self.unavailable = True
            print("Timeout reached while waiting for the element.")
            # Optionally, take a screenshot for debugging
            self.driver.save_screenshot('timeout_screenshot.png')
        except Exception as e:
            # Catch other exceptions that might occur
            self.unavailable = True
            print(f"An error occurred: {e}")


    def hide_window(self):
        """
        Completely hides the window.
        """
        win32gui.ShowWindow(self.window._hWnd, win32con.SW_HIDE)

    def show_window(self):
        """
        Restores and maximizes the Chrome window, and brings it to the foreground.
        """
        win32gui.ShowWindow(self.window._hWnd, win32con.SW_RESTORE)
        self.window.activate()
        self.driver.maximize_window()

    def clean_up(self):
        """
        Deletes all cookies and closes the browser session.
        """
        self.driver.delete_all_cookies()
        self.driver.quit()

    def run(self):
        """
        Executes the entire sequence of actions.
        """
        self.initialize_driver()
        print("READY")
        popup_monitor_thread = threading.Thread(target=self.monitor_popups)
        popup_monitor_thread.daemon = True
        popup_monitor_thread.start()
        self.start_video('https://www.youtube.com/watch?v=dfD85dGY03k&list=LL&index=4')

        time.sleep(500) # remove this later 
        self.clean_up()


if __name__ == "__main__":
    # Create an instance of the automation class and run the script
    automation = YouTubeAutomation()
    automation.run()
