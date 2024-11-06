import customtkinter as ctk
import threading
import re
from player import YouTubeAutomation

class YouTubeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Youtube Opener")
        self.geometry("500x300")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        self.configure(bg="#1e2227")

        self.fullscreen_var = ctk.BooleanVar()
        self.adblock_var = ctk.BooleanVar()

        # "Load" button
        self.load_button = ctk.CTkButton(self, text="Load", command=self.load, font=("Segoe UI", 16), fg_color="#d063a7", hover_color="#e070b1", width=200)
        self.load_button.pack(pady=20)

        # Fullscreen and Adblock switches
        self.fullscreen_switch = ctk.CTkSwitch(self, text="Fullscreen", variable=self.fullscreen_var, font=("Segoe UI", 14), width=150, height=30)
        self.fullscreen_switch.pack(pady=10)

        self.adblock_switch = ctk.CTkSwitch(self, text="Adblock", variable=self.adblock_var, font=("Segoe UI", 14), width=150, height=30)
        self.adblock_switch.pack(pady=10)

        # Label for invalid URL message (hidden by default)
        self.invalid_url_label = ctk.CTkLabel(self, text="Invalid URL", font=("Segoe UI", 16), text_color="red", bg_color="#1e2227")
        self.invalid_url_label.pack_forget()

    def load(self):
        self.load_button.configure(state="disabled")
        self.fullscreen_switch.configure(state="disabled")
        self.adblock_switch.configure(state="disabled")
        self.display_loading_text()

        self.load_button.pack_forget()
        self.fullscreen_switch.pack_forget()
        self.adblock_switch.pack_forget()

        self.youtube_automation = None
        self.thread = threading.Thread(target=self.initialize_automation)
        self.thread.start()

    def initialize_automation(self):
        fullscreen = self.fullscreen_var.get()
        adblock = self.adblock_var.get()

        self.youtube_automation = YouTubeAutomation(adblock=adblock, fullscreen=fullscreen)
        self.youtube_automation.initialize_driver()

        self.after(0, self.show_video_input_screen)

    def display_loading_text(self):
        self.loading_label = ctk.CTkLabel(self, text="Loading...", font=("Segoe UI", 20, "bold"), text_color="white", width=500, height=100)
        self.loading_label.place(relx=0.5, rely=0.4, anchor="center")
        self.loading_label.configure(pady=20)

    def show_video_input_screen(self):
        self.loading_label.pack_forget()
        self.link_input_frame = ctk.CTkFrame(self, fg_color="#1e2227", width=400, height=200)
        self.link_input_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.url_label = ctk.CTkLabel(self.link_input_frame, text="Enter YouTube URL:", font=("Segoe UI", 16), text_color="white")
        self.url_label.pack(pady=10)

        self.url_entry = ctk.CTkEntry(self.link_input_frame, width=250, font=("Segoe UI", 14), placeholder_text="Paste YouTube URL here", border_width=2, fg_color="#2c2f37", text_color="white")
        self.url_entry.pack(pady=10)

        self.open_button = ctk.CTkButton(self.link_input_frame, text="Open", command=self.open_video, font=("Segoe UI", 16), fg_color="#d063a7", hover_color="#e070b1", width=200)
        self.open_button.pack(pady=20)

    def open_video(self):
        link = self.url_entry.get()
        # Validate the link (only YouTube URLs)
        if not self.is_valid_youtube_url(link):
            self.show_invalid_url_message()
            return

        # Hide invalid URL message if URL is valid
        self.invalid_url_label.pack_forget()

        # Call the start_video method with the valid link in a separate thread
        self.youtube_automation_thread = threading.Thread(target=self.youtube_automation.start_video, args=(link,))
        self.youtube_automation_thread.start()

    def show_invalid_url_message(self):
        # Show the "Invalid URL" message on the GUI
        self.invalid_url_label.pack(pady=10)

    def is_valid_youtube_url(self, url):
        youtube_pattern = r"^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.*$"
        return re.match(youtube_pattern, url) is not None


if __name__ == "__main__":
    app = YouTubeApp()
    app.mainloop()
