import yt_dlp
import subprocess
import os

def search_youtube(query, max_results=5):
    """Search YouTube and return a list of video titles and URLs."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("🔍 Searching YouTube...")
            search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            print("✅ Search complete!")
        except Exception as e:
            print(f"❌ Error fetching results: {e}")
            return []

    videos = search_results.get('entries', [])
    return [(video['title'], video['url']) for video in videos if video]


def download_media(video_url, title, download_type="audio"):
    """Download video or audio using yt-dlp."""
    if download_type == "audio":
        print(f"⬇️ Downloading audio: {title}")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{sanitize_filename(title)}.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False
        }
    else:
        print(f"⬇️ Downloading video: {title}")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{sanitize_filename(title)}.mp4',
            'quiet': False,
            'merge_output_format': 'mp4'
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([video_url])
            print("✅ Download complete!")
        except Exception as e:
            print(f"❌ Download failed: {e}")


def sanitize_filename(name):
    """Remove invalid characters for filenames."""
    return "".join(c for c in name if c.isalnum() or c in ' -_').rstrip()


def get_audio_url(video_url):
    """Extract the best audio URL using yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info['url']
        except Exception as e:
            print(f"❌ Error extracting audio URL: {e}")
            return None


def play_song(audio_url):
    """Play the song using MPV."""
    if not audio_url:
        print("❌ No audio URL found.")
        return
    print("🎧 Streaming audio...")
    subprocess.run(["mpv", audio_url], check=True)


def main():
    query = input("🎼 Enter song or video name: ").strip()
    if not query:
        print("⚠️ No query provided.")
        return

    results = search_youtube(query)

    if not results:
        print("❌ No results found.")
        return

    print("\n🎬 Search Results:")
    for index, (title, _) in enumerate(results):
        print(f"{index + 1}. {title}")

    try:
        choice_index = int(input("\n➡️ Choose a number: ")) - 1
        if not (0 <= choice_index < len(results)):
            raise ValueError("Invalid selection.")
    except ValueError:
        print("❌ Invalid input.")
        return

    selected_title, selected_url = results[choice_index]
    print(f"\n🎯 Selected: {selected_title}")

    print("\n📥 Choose what to do:")
    print("1. Stream Audio")
    print("2. Download Audio (MP3)")
    print("3. Download Video (MP4)")

    action = input("➡️ Your choice: ").strip()

    if action == "1":
        audio_url = get_audio_url(selected_url)
        play_song(audio_url)
    elif action == "2":
        download_media(selected_url, selected_title, download_type="audio")
    elif action == "3":
        download_media(selected_url, selected_title, download_type="video")
    else:
        print("❌ Invalid option.")


if __name__ == "__main__":
    while True:
        main()
        again = input("\n🔁 Do another search? (y/n): ").strip().lower()
        if again != 'y':
            print("👋 Exiting...")
            break
