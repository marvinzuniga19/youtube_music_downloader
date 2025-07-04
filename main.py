import flet as ft
from yt_dlp import YoutubeDL
import os
import re
import threading
import shutil
from pathlib import Path

def main(page: ft.Page):
    # --- Configuración de la Página ---
    page.title = "Music Downloader from YouTube"
    page.window_width = 550
    page.window_height = 680
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1f262f"

    # --- Lógica de Negocio y Funciones de Ayuda ---

    def check_ffmpeg():
        if not shutil.which("ffmpeg"):
            ffmpeg_status.value = "FFmpeg no encontrado. La conversión puede fallar."
            ffmpeg_status.color = ft.Colors.ORANGE_300
        else:
            ffmpeg_status.value = "FFmpeg listo."
            ffmpeg_status.color = ft.Colors.GREEN_300
        page.update()

    def download_logic(url, selected_format, embed_thumbnail):
        download_path = "descargas"
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        try:
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': selected_format,
                'preferredquality': '192',
            }]
            if embed_thumbnail and selected_format in ['mp3', 'm4a']:
                postprocessors.append({'key': 'EmbedThumbnail'})

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'postprocessors': postprocessors,
                'progress_hooks': [progress_hook],
                'writethumbnail': embed_thumbnail,
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            success_message = f"¡Descarga completada en '{download_path}'!"
            update_ui_on_success(success_message)

        except Exception as ex:
            error_message = str(ex).split('ERROR:')[-1].strip()
            update_status(f"Error: {error_message}", ft.Colors.RED_400)
        finally:
            toggle_controls_activity(True)

    # --- Callbacks y Actualizadores de UI (Thread-Safe) ---
    def download_action(e):
        url = url_input.value
        if not url or not re.match(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|playlist\?list=|.+\?v=)?([^&=%\?]{11,})', url):
            update_status("Por favor, introduce una URL de YouTube válida.", ft.Colors.RED_400)
            return

        toggle_controls_activity(False)
        update_status("Iniciando descarga...", ft.Colors.BLUE_300)
        
        thread = threading.Thread(target=download_logic, args=(url, format_dropdown.value, embed_thumbnail_checkbox.value), daemon=True)
        thread.start()

    def progress_hook(d):
        status = d.get('status')
        if status == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                percentage = d.get('downloaded_bytes', 0) / total_bytes
                update_progress(percentage, f"{int(percentage * 100)}%")
        elif status == 'finished':
            update_status("Procesando archivo...", ft.Colors.BLUE_300)
            update_progress(None, "")

    def update_ui_on_success(message):
        status_text.value = message
        status_text.color = ft.Colors.GREEN_300
        url_input.value = ""
        page.update()

    def update_status(message, color):
        status_text.value = message
        status_text.color = color
        page.update()

    def update_progress(value, text):
        progress_bar.value = value
        progress_text.value = text
        progress_container.visible = True
        page.update()

    def toggle_controls_activity(is_active):
        url_input.disabled = not is_active
        download_button.disabled = not is_active
        format_dropdown.disabled = not is_active
        embed_thumbnail_checkbox.disabled = not is_active
        progress_container.visible = not is_active
        if is_active:
            progress_container.visible = False
        page.update()

    # --- Definición de Controles de la UI ---

    ffmpeg_status = ft.Text(size=11, weight=ft.FontWeight.W_500)
    url_input = ft.TextField(
        label="Pega la URL del video o playlist",
        border_radius=ft.border_radius.all(10),
        border_color=ft.Colors.WHITE24,
        focused_border_color=ft.Colors.BLUE_400,
    )

    format_dropdown = ft.Dropdown(
        label="Formato", value="mp3", width=140,
        border_radius=ft.border_radius.all(10),
        options=[ft.dropdown.Option("mp3"), ft.dropdown.Option("m4a"), ft.dropdown.Option("wav")]
    )
    embed_thumbnail_checkbox = ft.Checkbox(label="Incrustar portada", value=True)
    
    download_button = ft.ElevatedButton(
        text="Descargar", icon=ft.Icons.DOWNLOAD_ROUNDED,
        on_click=download_action,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600,
            padding=ft.padding.symmetric(vertical=15, horizontal=30)
        )
    )

    status_text = ft.Text(weight=ft.FontWeight.BOLD)
    progress_bar = ft.ProgressBar(width=400, value=0, bar_height=10, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.WHITE10)
    progress_text = ft.Text("0%")
    progress_container = ft.Row([progress_bar, progress_text], visible=False, alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    # --- Layout de la Página con Contenedor Principal ---

    main_container = ft.Container(
        width=480,
        padding=ft.padding.all(30),
        border_radius=ft.border_radius.all(15),
        bgcolor=ft.Colors.BLACK26,
        content=ft.Column(
            [
                ft.Text("Music Downloader from YouTube", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ffmpeg_status,
                ft.Divider(height=25),
                url_input,
                ft.Container(height=10),
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=ft.padding.all(15),
                        content=ft.Row(
                            [format_dropdown, embed_thumbnail_checkbox],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    )
                ),
                ft.Container(height=20),
                ft.Row([download_button], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                progress_container,
                status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )
    )

    page.add(main_container)

    # --- Inicialización ---
    check_ffmpeg()

ft.app(target=main)