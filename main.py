import time
import numpy as np

# Thumbnail Capturing Imports
import cv2
from vidgear.gears import CamGear

# Tkinter Based Imports
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

# Google/YouTube API Based Imports
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Ensure NumPy initializes properly
a = np.array(2)

# Global variable to track the application's status
active = False  # Track whether the thumbnail changing process inclusive of the wait time is active or not
after_id = None  # To store the ID for scheduling with `after()` rather than freeze the program with sleep()

# Simple function to display errors to user
def display_error(message):
    messagebox.showerror("Error", message)
    print(f"❌ {message}")

# Initialize The YouTube API
def initialize_api(credentials_path):
    try:
        # Grab the necessary scopes for API Initialization and store credentials from the user specified path
        scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        flow.run_local_server(host='localhost', port=8080)
        credentials = flow.credentials
        youtube = build('youtube', 'v3', credentials=credentials)
        print("✅ API successfully initialized!")
        return youtube

    except Exception as e:
        # Upon failure to return a successful build for the 'youtube' object, print error to console/dialog box
        display_error(f" Error with API startup: {e}")
        return None

# Download The Current YouTube Livestream Frame
def download_thumbnail(video_id):
    try:
        # Use CamGear To Capture Current Frame Of Livestream
        capture_stream = CamGear(
            source="https://youtu.be/" + video_id,  # YT URL
            stream_mode=True,
            logging=True
        ).start()
        time.sleep(1)
        thumbnail = capture_stream.read()

        # Verify Thumbnail Contains Data Then End CamGear
        if thumbnail is None:
            display_error("Error Capturing YouTube Livestream for Thumbnail")
        else:
            cv2.imwrite("thumbnail.png", thumbnail)
            print("✅ Thumbnail Successfully Saved!")
        capture_stream.stop()

    except Exception as e:
        display_error(f"Error Download Thumbnail: {e}")
        return None, None

# Change The YouTube Thumbnail given Video ID and Thumbnail Path
def change_thumbnail(youtube, video_id, thumbnail_path):
    try:
        thumbnail_path = 'thumbnail.png'
        request = youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path))
        response = request.execute()
        print("✅ Thumbnail updated successfully!")
        print(response)
    except Exception as e:
        display_error(f"Error changing thumbnail: {e}")

# Check Video Status (Livestream Privacy -- Mainly Used for Debugging Purposes)
def check_video_status(youtube, video_id):
    try:
        # API request to get video details
        request = youtube.videos().list(part="status", id=video_id)
        response = request.execute()

        # Check if video exists and retrieve its status
        if 'items' in response:
            video = response['items'][0]
            privacy_status = video['status']['privacyStatus']
            print(f"Video Privacy Status: {privacy_status}")
            if privacy_status == 'unlisted':
                print("The video is unlisted and accessible.")
                return True  # Video is unlisted, so we can change the thumbnail
            elif privacy_status == 'private':
                print("The video is private and inaccessible.")
                return False  # Video is private, don't change the thumbnail
            elif privacy_status == 'public':
                print("The video is public and accessible.")
                return True  # Video is public, so we can change the thumbnail
        else:
            display_error("Video not found. Check Video ID or Stream Visibility on YouTube.")
            return False
    except Exception as e:
        display_error(f"Error occurred while checking video status: {e}")
        return False

# Function To Update Thumbnail To Current Frame
def capture_and_update_thumbnail(video_id, youtube):
    print("Checking and updating video thumbnail...")
    if check_video_status(youtube, video_id):
        download_thumbnail(video_id)
        change_thumbnail(youtube, video_id, 'thumbnail.png')

# Function for Start button
def start():
# Status of Thumbnail Updating Process and ID Variable for Wait Time
    global active, after_id

    # Make sure user cannot spam the start button while already running
    if active:
        display_error("Thumbnail update process is already running.")
        return

    # Set active status to true and update Window accordingly
    active = True
    update_status("Active")  # Update the status to running

    # Get the User Specified Details From The Window
    video_id = VideoID.get()    # YouTube Video ID To Livestream
    credentials_path = Cred.get() # Json Credentials To Access YouTube API
    time_interval = int(Ti.get()) # Time Interval in Seconds

    # Initialize API Object (If Initialization Fails Reset Window To Default Settings)
    youtube = initialize_api(credentials_path)
    if youtube is None:
        active = False
        update_status("Inactive", "red")  # Update the status to stopped if API fails
        return

    # Define Thumbnail Updating Method Within Start Function (For After_ID and Avoidance of Global Variables... probably a better implementation idk)
    def update_thumbnail():
        capture_and_update_thumbnail(video_id, youtube)
        if active:
            print(f"⏳ Waiting {time_interval} seconds before next update...")
            global after_id
            after_id = root.after(time_interval * 1000, update_thumbnail)  # Schedule next check

    update_thumbnail()

# Function for Stop button
def stop():
# Status of Thumbnail Updating Process and ID Variable for Wait Time
    global active, after_id

# Reset Window To Default Settings
    if active:
        active = False
        if after_id:
            root.after_cancel(after_id)  # Cancel the scheduled update if it exists
        print("✅ Stopped thumbnail updating process.")
        update_status("Inactive", "red")  # Update the status to stopped

# Update Status Display (Pre-Specified To Green)
def update_status(status_text, color="green"):
    status_label.config(text=f"Status: {status_text}", foreground=color)  # Update the status label with color

# GUI/Window Setup
root = Tk() # Initialize Tkinter
root.title("YouTube Livestream Thumbnail Changer") # Set Window Title

# Display Main Window
mainframe = ttk.Frame(root, padding="3 3 15 15")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Video ID Label/Text Field
Label(mainframe, text="Video ID:").grid(column=1, row=1, sticky=(W))
VideoID = StringVar()
VideoID_entry = ttk.Entry(mainframe, width=30, textvariable=VideoID)
VideoID_entry.insert(0, "Video ID")
VideoID_entry.grid(column=2, row=1, sticky=(W, E))

# Credentials Label/Text Field
Label(mainframe, text="Credentials File:").grid(column=1, row=2, sticky=(W))
Cred = StringVar()
Cred_entry = ttk.Entry(mainframe, width=30, textvariable=Cred)
Cred_entry.grid(column=2, row=2, sticky=(W, E))

# Button to Browse For Credentials File
def browsefunc():
    filename = askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    Cred_entry.insert(0, filename)

ttk.Button(mainframe, text="Browse Files", command=browsefunc).grid(column=3, row=2)

# Time Interval Label/Text Field
Label(mainframe, text="Time Interval (Seconds):").grid(column=1, row=3, sticky=(W))
Ti = StringVar()
Ti_entry = ttk.Entry(mainframe, width=30, textvariable=Ti)
Ti_entry.insert(0, "180")  # Default to 180 seconds (3 minutes)
Ti_entry.grid(column=2, row=3, sticky=(W, E))

# Setup Start and Stop buttons
start_button  = ttk.Button(mainframe, text="Start", command=start).grid(column=3, row=4, sticky=E)
stop_button = ttk.Button(mainframe, text="Stop", command=stop).grid(column=1, row=4, sticky=W)

# Status Label at The Bottom Of The Window
status_label = ttk.Label(root, text="Status: Inactive", relief=SUNKEN, anchor=W, padding="5", foreground="red")
status_label.grid(row=1, column=0, sticky=(W, E))

# Disable resizing
root.resizable(False, False)

# Run Application
root.mainloop()