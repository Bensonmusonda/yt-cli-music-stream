import subprocess

def play_youtube_audio(query):
    try:
        # Run yt-dlp to get the direct audio URL
        result = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "--get-url", f"ytsearch:{query}"],
            capture_output=True,
            text=True
        )

        # Extract URL from output
        audio_url = result.stdout.strip()

        if not audio_url:
            print("❌ No audio URL found. Try another search.")
            return

        print(f"🎵 Streaming: {query}")
        
        # Play using MPV (Ensure MPV is installed)
        subprocess.run(["mpv", audio_url])

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    search_query = input("Enter song name: ")
    play_youtube_audio(search_query)
