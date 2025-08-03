import yt_dlp
import os
import subprocess
import time
import re 


def get_video_urls_from_playlist(playlist_url: str):
    video_urls = []

    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)
        if 'entries' in info_dict:
            for video in info_dict['entries']:
                video_urls.append(video['url'])
    return video_urls

# def download_youtube_video(url, dir):
#     """
#     url like like  https://www.youtube.com/watch?v=6UJ1zaWSxXA
#     """

#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'outtmpl': f'{dir}/%(title)s.%(ext)s',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'quiet': False,
#     }
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         # ydl.download(url)
#         info = ydl.extract_info(url, download=True)
#         title = info.get('title', None)
#         downloaded_path = os.path.join(dir, f"{title}.mp3")
#     return downloaded_path

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def download_youtube_video(url, dir):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'unknown_title')
        sanitized_title = sanitize_filename(title)

    output_path = os.path.join(dir, f"{sanitized_title}.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return os.path.join(dir, f"{sanitized_title}.mp3")

def ffmpeg_resample(input_path: str, output_path: str):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def postprocess_audio(audio_path):
    # audio, sr= torchaudio.load(audio_path)
    # mono_audio = audio.mean(dim=0).unsqueeze(0)
    # resampler = T.Resample(orig_freq= sr, new_freq=16000)
    # resampled_audio = resampler(mono_audio)
    # print(resampled_audio.shape)
    # torchaudio.save(audio_path, resampled_audio, 16000)

    output_path= audio_path.replace('.mp3', '_resampled.mp3')
    ffmpeg_resample(audio_path, output_path)
    #deleting input audio
    os.remove(audio_path)

def download_and_postprocess_video(video_url: str, dir: str):
    local_audio_path= download_youtube_video(video_url, dir)
    postprocess_audio(local_audio_path)

def download_and_postprocess_playlist(playlist_url: str, dir: str):
    start = time.time()
    video_urls= get_video_urls_from_playlist(playlist_url)
    for url in video_urls:
        download_and_postprocess_video(url, dir)
    end = time.time()
    print(f"***********Playlist Download Finished in {end - start:.2f} seconds************")




if __name__== '__main__':
    playlist_url = "https://youtube.com/playlist?list=PLTPwffe8uEJsAJTCkQcgWxy7FJuaRNT-t&si=hOuJKSST5ZIW5nem"
    # urls = get_video_urls_from_playlist(playlist_url)
    # for i, link in enumerate(urls, 1):
    #     print(f"{i}: {link}")
    # url= urls[0]
    dir= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp"
    # local_audio_path= download_youtube_video(url, dir)
    # print(local_audio_path)
    # postprocess_audio(local_audio_path)

    download_and_postprocess_playlist(playlist_url, dir)
    
