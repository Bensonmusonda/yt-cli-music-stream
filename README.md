### 🎧 YouTube Music Streamer & Downloader CLI

This is a command-line interface (CLI) application that allows you to search for YouTube videos and either stream their audio directly or download them as MP3 audio or MP4 video files.

### 🌟 Features

  * **Search**: Find videos and songs on YouTube using a simple text query.
  * **Stream Audio**: Stream the audio of a selected video using the `mpv` player without downloading it.
  * **Download**: Download the selected media as a high-quality MP3 audio or MP4 video file.
  * **Customizable Paths**: Choose a custom download location or use the default `~/Downloads/MusicStreamerCLI`.

### 🛠️ Prerequisites

Before running the application, you must have the following software installed on your system.

  * **Python 3.6+**: The script is written in Python.
  * **`yt-dlp`**: A command-line program for downloading videos from YouTube and other sites.
  * **`mpv`**: A free, open-source media player used for streaming the audio.
  * **`ffmpeg`**: A complete, cross-platform solution to record, convert, and stream audio and video. It is required for converting downloads to MP3 format and for embedding thumbnails.

-----

### ⚙️ Setup and Installation

Follow these steps to set up the application.

#### Step 1: Install Python Dependencies

Open your terminal or command prompt and run the following command to install the required Python libraries:

```bash
pip install yt-dlp rich
```

#### Step 2: Install `yt-dlp`, `mpv`, and `ffmpeg`

These are external command-line tools that your script depends on. You must install them and ensure they are in your system's PATH.

**Windows**

1.  **Download**: Get the executables from their official websites:
      * [yt-dlp](https://github.com/yt-dlp/yt-dlp/releases)
      * [mpv](https://mpv.io/installation/)
      * [ffmpeg](https://ffmpeg.org/download.html)
2.  **Add to PATH**: Place the downloaded executable files (e.g., `yt-dlp.exe`, `mpv.exe`, `ffmpeg.exe`) in a directory that is included in your system's PATH environment variable. A common location is `C:\Windows`.

**macOS**
Install using [Homebrew](https://brew.sh/):

```bash
brew install yt-dlp mpv ffmpeg
```

**Linux (Debian/Ubuntu)**
Install using the `apt` package manager:

```bash
sudo apt update
sudo apt install yt-dlp mpv ffmpeg
```

-----

### ▶️ How to Run

Once all prerequisites are installed, you can run the application directly from your terminal.

1.  Navigate to the directory where you saved the script.
2.  Run the following command:

<!-- end list -->

```bash
python yt-music-enhanced-iv.py
```

Replace `your_script_name.py` with the actual filename of your script.

You will be greeted with the main menu, from which you can choose to stream, download, or view settings.