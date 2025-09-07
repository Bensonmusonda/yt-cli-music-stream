import yt_dlp
import subprocess
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def search_youtube(query, max_results=5):
    """Search YouTube and return a list of video titles and URLs."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            with console.status("[bold green]Searching YouTube..."):
                search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        except Exception as e:
            console.print(f"[bold red]❌ Error fetching results:[/bold red] {e}")
            return []

    videos = search_results.get('entries', [])
    return [(video['title'], video['url']) for video in videos if video]

def get_audio_url(video_url):
    """Extract the best audio URL using yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            with console.status("[cyan]Fetching audio stream..."):
                info = ydl.extract_info(video_url, download=False)
                return info['url']
        except Exception as e:
            console.print(f"[bold red]❌ Error extracting audio URL:[/bold red] {e}")
            return None

def play_song(audio_url):
    """Play the song using MPV."""
    if not audio_url:
        console.print("[red]❌ No audio URL found. Cannot play song.[/red]")
        return

    console.print("[green]🎵 Streaming audio with MPV...[/green]")
    subprocess.run(["mpv", audio_url], check=True)

def main():
    query = Prompt.ask("[bold yellow]Enter song name[/bold yellow]")

    results = search_youtube(query)
    if not results:
        console.print("[red]❌ No results found. Try a different search term.[/red]")
        return

    table = Table(title="Search Results", header_style="bold magenta")
    table.add_column("No.", justify="right")
    table.add_column("Title", style="cyan")

    for i, (title, _) in enumerate(results, start=1):
        table.add_row(str(i), title)

    console.print(table)

    choice = Prompt.ask("[bold green]Enter the number of the song to play[/bold green]")
    try:
        choice_index = int(choice) - 1
        if 0 <= choice_index < len(results):
            selected_title, selected_url = results[choice_index]
            console.print(f"\n[bold blue]🎵 Playing:[/bold blue] {selected_title}")
            audio_url = get_audio_url(selected_url)
            play_song(audio_url)
        else:
            console.print("[red]❌ Invalid selection.[/red]")
    except ValueError:
        console.print("[red]❌ Please enter a valid number.[/red]")

if __name__ == "__main__":
    while True:
        main()
