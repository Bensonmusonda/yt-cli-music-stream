import yt_dlp
import subprocess
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import time
import traceback

console = Console()

# --- Configuration ---
MAX_SEARCH_RESULTS = 10
STREAMING_MPV_PLAYER_ARGS = ["--no-video", "--force-window=no", "--no-input-terminal", "--really-quiet"]
DOWNLOAD_PATH = Path.home() / "Downloads" / "MusicStreamerCLI"

# Ensure download path exists
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)


# --- Core YouTube Functions ---
def search_youtube(query, max_results=MAX_SEARCH_RESULTS):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'default_search': f"ytsearch{max_results}",
    }
    videos = []
    with Progress(
        SpinnerColumn(spinner_name="dots12"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress_bar:
        search_task = progress_bar.add_task(description="[bold green]Searching YouTube...", total=None)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)
        except yt_dlp.utils.DownloadError as e:
            console.print(f"[bold red]❌ Error fetching results:[/bold red] {e}")
            return []
        except Exception as e:
            console.print(f"[bold red]❌ An unexpected error occurred during search:[/bold red] {e}")
            return []
        finally:
            progress_bar.update(search_task, completed=True)

    if search_results and 'entries' in search_results:
        for entry in search_results.get('entries', []):
            if entry and entry.get('title') and entry.get('id'):
                video_id = entry.get('id')
                video_url = entry.get('url')
                if not video_url or 'watch?v=' not in str(video_url): # Ensure it's a standard watch URL
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append((entry['title'], video_url, video_id))
    elif search_results and search_results.get('title') and search_results.get('id'):
        video_id = search_results.get('id')
        video_url = search_results.get('webpage_url') or f"https://www.youtube.com/watch?v={video_id}"
        videos.append((search_results['title'], video_url, video_id))

    if not videos:
        console.print(f"[orange3]No videos found for '[italic]{query}[/italic]'. Try a different search term.[/orange3]")
    return videos


def get_audio_url_for_streaming(video_url, video_title=""):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
    }
    with Progress(
        SpinnerColumn(spinner_name="earth"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress_bar:
        task_description = f"Fetching audio stream for: [cyan]{video_title[:40]}{'...' if len(video_title) > 40 else ''}[/cyan]"
        fetch_task = progress_bar.add_task(task_description, total=None)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get('url')
        except Exception as e:
            console.print(f"[bold red]❌ Error extracting audio URL for streaming:[/bold red] {e}")
            return None
        finally:
            progress_bar.update(fetch_task, completed=True)


def play_song_with_mpv(audio_url, title=""):
    if not audio_url:
        console.print("[red]❌ No audio URL found. Cannot play song.[/red]")
        time.sleep(2)
        return

    mpv_title_arg = f"--force-media-title={title.replace('"', '')}"
    command = ["mpv"] + STREAMING_MPV_PLAYER_ARGS + [mpv_title_arg, audio_url]

    console.rule(f"[bold green]🎵 Now Streaming: [cyan]{title}[/cyan] 🎵[/bold green]", style="green")
    console.print(Align.center(f"[italic grey70](MPV player is now active headless.)[/italic grey70]"))
    # Corrected Text.assemble usage here:
    console.print(Align.center(Text.assemble(
        "Press ",
        ("Ctrl+C", "bold red"),
        " in this terminal to stop playback and return."
    )), "\n")

    process = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process.wait()
    except FileNotFoundError:
        console.print("[bold red]❌ MPV player not found. Please ensure MPV is installed and in your system's PATH.[/bold red]")
        time.sleep(3)
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️ Playback interruption signal received...[/yellow]")
        if process and process.poll() is None:
            console.print("[yellow]Stopping MPV...[/yellow]")
            process.terminate()
            try:
                process.wait(timeout=3)
                console.print("[green]MPV terminated gracefully.[/green]")
            except subprocess.TimeoutExpired:
                console.print("[orange3]MPV did not terminate gracefully, forcing kill...[/orange3]")
                process.kill()
                process.wait()
                console.print("[green]MPV killed.[/green]")
        else:
            console.print("[grey50]MPV process was not active or already stopped.[/grey50]")
        time.sleep(0.5)
    except Exception as e:
        console.print(f"[bold red]❌ An unexpected error occurred during playback:[/bold red] {e}")
        if process and process.poll() is None: process.kill()
        time.sleep(2)
    finally:
        if process and process.returncode is not None and process.returncode not in [0, -9, -15, 130]: # 130 for SIGINT
             console.print(f"[yellow]MPV exited with code: {process.returncode}[/yellow]")
        console.print("\n[green]Returning to menu...[/green]")
        time.sleep(1)


def download_media(video_url, video_title, video_id, download_type='audio', download_path=DOWNLOAD_PATH):
    console.print(f"\n[cyan]Preparing to download {download_type}:[/cyan] [italic]{video_title}[/italic]")

    safe_title = "".join(c if c.isalnum() or c in " .-_()" else "_" for c in video_title)
    safe_title = safe_title[:100]
    filename_base = f"{safe_title}_{video_id}"

    progress_hook_active = False
    download_progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(), DownloadColumn(), TransferSpeedColumn(), TimeRemainingColumn(),
        SpinnerColumn(spinner_name="line", finished_text="✅"),
        console=console, transient=False
    )

    def ydl_progress_hook(d):
        nonlocal progress_hook_active
        if not download_progress.tasks: return
        task_id = download_progress.tasks[0].id

        if not progress_hook_active and d['status'] in ['downloading', 'finished']:
            if download_progress.tasks[task_id].completed == 0:
                 download_progress.start_task(task_id)
            progress_hook_active = True

        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            filename_from_hook = d.get('filename') or d.get('info_dict', {}).get('_filename')
            display_name = Path(filename_from_hook).name if filename_from_hook else "file"
            if total_bytes:
                download_progress.update(task_id, total=total_bytes, completed=downloaded_bytes, description=f"Downloading [cyan]{display_name}[/cyan]")
            else:
                download_progress.update(task_id, description=f"Downloading [cyan]{display_name}[/cyan] (size unknown)")
        elif d['status'] == 'finished':
            final_filename = d.get('filename') or d.get('info_dict', {}).get('_filename')
            display_name = Path(final_filename).name if final_filename else filename_base
            total = download_progress.tasks[0].total or downloaded_bytes # Use downloaded if total was never set
            download_progress.update(task_id, completed=total, total=total, description=f"[green]Finished [cyan]{display_name}[/cyan]")
        elif d['status'] == 'error':
            download_progress.update(task_id, description=f"[red]Error during {d.get('fragment_index', 'download') if d.get('fragment_count') else 'download'}[/red]")

    ydl_opts_base = {
        'progress_hooks': [ydl_progress_hook], 'noplaylist': True, 'noprogress': True,
        'quiet': True, 'outtmpl': str(download_path / f'{filename_base}.%(ext)s'),
        'ignoreerrors': True, 'verbose': False, 'no_warnings': True,
    }

    if download_type == 'audio':
        ydl_opts = {**ydl_opts_base, 'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                                     {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}]}
    elif download_type == 'video':
        ydl_opts = {**ydl_opts_base, 'format': 'bestvideo+bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
                                      {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}]}
    else:
        console.print("[red]Invalid download type specified.[/red]"); return

    with download_progress:
        task = download_progress.add_task(f"Preparing {download_type} download of '{video_title[:30]}...' ", total=1)
        download_progress.stop_task(task)
        final_filepath_guess = None
        try:
            expected_ext = 'mp3' if download_type == 'audio' else 'mp4'
            final_filepath_guess = download_path / f'{filename_base}.{expected_ext}'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            actual_files = list(download_path.glob(f"{filename_base}.*"))
            if actual_files: final_filepath_guess = actual_files[0]
            if progress_hook_active and not download_progress.tasks[task].finished:
                 download_progress.update(task, completed=download_progress.tasks[task].total or 1,
                                         description=f"[green]Completed: {Path(final_filepath_guess).name if final_filepath_guess else filename_base}[/green]")
            console.print(f"\n[bold green]✅ Download complete![/bold green] Saved to: [italic underline]{final_filepath_guess or download_path}[/italic underline]")
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).split('\n')[-1]
            console.print(f"\n[bold red]❌ Download Error:[/bold red] {error_msg}")
            if not progress_hook_active or not download_progress.tasks[task].finished :
                 download_progress.update(task, description="[red]Download failed[/red]", completed=download_progress.tasks[task].total or 1)
        except Exception as e:
            console.print(f"\n[bold red]❌ An unexpected error occurred during download:[/bold red] {e}")
            if not progress_hook_active or not download_progress.tasks[task].finished :
                download_progress.update(task, description="[red]Download failed unexpectedly[/red]", completed=download_progress.tasks[task].total or 1)
        finally:
            if download_progress.tasks and not download_progress.tasks[task].finished:
                download_progress.update(task, completed=download_progress.tasks[task].total or 1)
            console.print(Panel(f"Find your downloads in: {download_path}", title="[b]Download Location[/b]", border_style="blue", expand=False))
    time.sleep(2)


# --- UI Functions ---
def display_header():
    header_text = Text("🎧 YouTube Music Streamer & Downloader CLI 🎤", style="bold white on deep_sky_blue4", justify="center")
    console.print(Panel(header_text, expand=False, border_style="deep_sky_blue4"))

def display_main_menu():
    console.clear(); display_header()
    menu_panel = Panel(
        Text.assemble(
            ("1.", "bold cyan"), " Search and Stream Song\n",
            ("2.", "bold green"), " Search and Download Media\n",
            ("3.", "bold yellow"), " Settings (View Download Path)\n",
            ("0.", "bold red"),  " Exit"
        ), title="[b]Main Menu[/b]", border_style="bright_blue", padding=(1, 2), expand=False)
    console.print(Align.center(menu_panel))
    choice = Prompt.ask(Text("\nEnter your choice", style="bold yellow"), choices=["1", "2", "3", "0"], show_choices=False)
    return choice

def select_media_from_results(results, action_verb="process"):
    if not results:
        console.print("[red]No results to select from.[/red]"); time.sleep(1); return None
    table = Table(title=f"Search Results - Select media to {action_verb}",
                  header_style="bold magenta", show_lines=True, border_style="dim blue", min_width=60)
    table.add_column("No.", justify="right", style="bold yellow", width=5)
    table.add_column("Title", style="cyan", overflow="fold")
    for i, (title, _url, _id) in enumerate(results, start=1): table.add_row(str(i), title)
    console.print(table)
    console.print(f"[italic grey50]Found {len(results)} result(s).[/italic grey50]")
    try:
        song_choice_prompt = Text.assemble(
            Text(f"Enter number to {action_verb} (or ", style="bold green"),
            Text("0", style="bold yellow"), Text(" to return): ", style="bold green"))
        valid_choices = ["0"] + [str(i) for i in range(1, len(results) + 1)]
        choice_num = IntPrompt.ask(song_choice_prompt, choices=valid_choices, show_choices=False)
        if choice_num == 0: return None
        return results[choice_num - 1]
    except KeyboardInterrupt:
        console.print("\n[yellow]Selection cancelled.[/yellow]"); time.sleep(1); return None
    except Exception as e:
        console.print(f"\n[red]Error during selection: {e}[/red]"); time.sleep(1); return None

def handle_search_and_stream():
    console.clear(); display_header()
    console.print(Panel(Text("🎵 Search and Stream 🎵", justify="center", style="bold blue_violet"), border_style="blue_violet", expand=False))
    query = Prompt.ask("\n[bold yellow]Enter song name or YouTube URL to stream[/bold yellow]")
    if not query.strip(): console.print("[orange3]Search query cannot be empty.[/orange3]"); time.sleep(2); return
    results = search_youtube(query)
    if not results: time.sleep(2); return
    selected_media = select_media_from_results(results, action_verb="stream")
    if selected_media:
        selected_title, selected_url, _ = selected_media
        console.print(f"\n[bold blue]▶️ Selected for streaming:[/bold blue] [italic]{selected_title}[/italic]")
        audio_url = get_audio_url_for_streaming(selected_url, selected_title)
        if audio_url: play_song_with_mpv(audio_url, selected_title)
        else: console.print("[red]❌ Could not retrieve audio for streaming.[/red]"); time.sleep(3)

def handle_search_and_download():
    console.clear(); display_header()
    console.print(Panel(Text("💾 Search and Download 💾", justify="center", style="bold dark_green"), border_style="dark_green", expand=False))
    query = Prompt.ask("\n[bold yellow]Enter song/video name or YouTube URL to download[/bold yellow]")
    if not query.strip(): console.print("[orange3]Search query cannot be empty.[/orange3]"); time.sleep(2); return
    results = search_youtube(query)
    if not results: time.sleep(2); return
    selected_media = select_media_from_results(results, action_verb="download")
    if selected_media:
        selected_title, selected_url, selected_id = selected_media
        console.print(f"\n[bold green]🔽 Selected for download:[/bold green] [italic]{selected_title}[/italic]")
        console.print("\nChoose download type:")
        download_type_choice = Prompt.ask(
            Text.assemble("  (", ("A", "bold cyan"), ")udio (MP3) or (", ("V", "bold magenta"), ")ideo (MP4)? "),
            choices=["a", "v"], default="a").lower()
        download_type = 'audio' if download_type_choice == 'a' else 'video'
        custom_path_str = Prompt.ask(
            f"[cyan]Enter download path or press Enter for default[/cyan] ([italic yellow]{DOWNLOAD_PATH}[/italic yellow])")
        current_download_path = Path(custom_path_str).expanduser() if custom_path_str.strip() else DOWNLOAD_PATH
        try: current_download_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            console.print(f"[red]Error creating path {current_download_path}: {e}. Using default: {DOWNLOAD_PATH}[/red]")
            current_download_path = DOWNLOAD_PATH
        download_media(selected_url, selected_title, selected_id, download_type, current_download_path)

def handle_settings():
    console.clear(); display_header()
    settings_panel = Panel(
        Text(f"🛠️ Application Info 🛠️\n\nDefault download path: [yellow link=file://{DOWNLOAD_PATH}]{DOWNLOAD_PATH}[/yellow]\n\n"
             "[italic dim]More settings will be configurable in future versions.[/italic dim]", justify="center"),
        title="[b]Current Settings[/b]", border_style="cyan", padding=(1,2))
    console.print(Align.center(settings_panel))
    Prompt.ask(Text("\nPress Enter to return to the main menu...", style="dim"))

# --- Main Application Loop ---
def app():
    try:
        while True:
            user_choice = display_main_menu()
            if user_choice == '1': handle_search_and_stream()
            elif user_choice == '2': handle_search_and_download()
            elif user_choice == '3': handle_settings()
            elif user_choice == '0':
                console.clear(); display_header()
                console.print(Align.center(Text("\n👋 Goodbye! Thanks for using the CLI! 👋\n", style="bold bright_magenta")))
                time.sleep(1.5); console.clear(); break
    except KeyboardInterrupt:
        console.print(Text("\n\n🚨 Application interrupted by user. Exiting...", style="bold red")); time.sleep(1)
    except Exception as e:
        console.print(f"\n[bold red]💥 UNEXPECTED APPLICATION ERROR:[/bold red] {e}")
        console.print("[italic]Please report this error if it persists.[/italic]")
        console.print("\n[dim white]Traceback:[/dim white]")
        console.print_exception(show_locals=False) # show_locals=True can be verbose
        time.sleep(5) # Give time to read the error
    finally:
        console.print("Exited.", style="dim")

if __name__ == "__main__":
    if not Path(DOWNLOAD_PATH).exists():
        try:
            Path(DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)
        except Exception as e: # Catch more general error for directory creation
            console.print(f"[red]Could not create default download directory {DOWNLOAD_PATH}: {e}[/red]")
    app()