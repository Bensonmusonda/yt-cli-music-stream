import yt_dlp
import subprocess

def search_youtube(query, max_results=5):
    """Search YouTube and return a list of video titles and URLs."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # Prevents automatic downloading
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

def get_audio_url(video_url):
    """Extract the best audio URL using yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',  # Extract only audio
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info['url']  # Return direct audio stream URL
        except Exception as e:
            print(f"❌ Error extracting audio URL: {e}")
            return None

def play_song(audio_url):
    """Play the song using MPV."""
    if not audio_url:
        print("❌ No audio URL found. Cannot play song.")
        return

    print(f"🎵 Streaming audio...")
    subprocess.run(["mpv", audio_url], check=True)

def main():
    query = input("Enter song name: ")

    print("\n🔍 Searching for:", query)
    results = search_youtube(query)

    if not results:
        print("❌ No results found. Try a different search term.")
        return

    print("\n🎶 Select a song:")
    for index, (title, url) in enumerate(results):
        print(f"{index + 1}. {title}")

    choice = input("\nEnter the number of the song you want to play: ")

    try:
        choice_index = int(choice) - 1
        if 0 <= choice_index < len(results):
            selected_title, selected_url = results[choice_index]
            print(f"\n🎵 Playing: {selected_title}")

            # Get the direct audio stream URL
            audio_url = get_audio_url(selected_url)

            # Play the song using MPV
            play_song(audio_url)
        else:
            print("❌ Invalid selection.")
    except ValueError:
        print("❌ Please enter a valid number.")

if __name__ == "__main__":
    while True:
        main()
