# import yt_dlp
# import os
# import subprocess
# import time
# import re 


# def get_video_urls_from_playlist(playlist_url: str):
#     video_urls = []

#     ydl_opts = {
#         'quiet': True,
#         'extract_flat': True,
#         'skip_download': True,
#     }
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info_dict = ydl.extract_info(playlist_url, download=False)
#         if 'entries' in info_dict:
#             for video in info_dict['entries']:
#                 video_urls.append(video['url'])
#     return video_urls

# # def download_youtube_video(url, dir):
# #     """
# #     url like like  https://www.youtube.com/watch?v=6UJ1zaWSxXA
# #     """

# #     ydl_opts = {
# #         'format': 'bestaudio/best',
# #         'outtmpl': f'{dir}/%(title)s.%(ext)s',
# #         'postprocessors': [{
# #             'key': 'FFmpegExtractAudio',
# #             'preferredcodec': 'mp3',
# #             'preferredquality': '192',
# #         }],
# #         'quiet': False,
# #     }
# #     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
# #         # ydl.download(url)
# #         info = ydl.extract_info(url, download=True)
# #         title = info.get('title', None)
# #         downloaded_path = os.path.join(dir, f"{title}.mp3")
# #     return downloaded_path

# def sanitize_filename(filename: str) -> str:
#     return re.sub(r'[<>:"/\\|?*]', '', filename)

# def download_youtube_video(url, dir):
#     with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
#         info = ydl.extract_info(url, download=False)
#         title = info.get('title', 'unknown_title')
#         sanitized_title = sanitize_filename(title)

#     output_path = os.path.join(dir, f"{sanitized_title}.%(ext)s")
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'outtmpl': output_path,
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'quiet': False,
#     }
    
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         ydl.download([url])
#     return os.path.join(dir, f"{sanitized_title}.mp3")

# def ffmpeg_resample(input_path: str, output_path: str):
#     cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path]
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


# def postprocess_audio(audio_path):
#     # audio, sr= torchaudio.load(audio_path)
#     # mono_audio = audio.mean(dim=0).unsqueeze(0)
#     # resampler = T.Resample(orig_freq= sr, new_freq=16000)
#     # resampled_audio = resampler(mono_audio)
#     # print(resampled_audio.shape)
#     # torchaudio.save(audio_path, resampled_audio, 16000)

#     output_path= audio_path.replace('.mp3', '_resampled.mp3')
#     ffmpeg_resample(audio_path, output_path)
#     #deleting input audio
#     os.remove(audio_path)

# def download_and_postprocess_video(video_url: str, dir: str):
#     local_audio_path= download_youtube_video(video_url, dir)
#     if not local_audio_path:
#         print(f"Skipping processing as already processed")
#         return
#     postprocess_audio(local_audio_path)

# def download_and_postprocess_playlist(playlist_url: str, dir: str):
#     start = time.time()
#     video_urls= get_video_urls_from_playlist(playlist_url)
#     for url in video_urls:
#         download_and_postprocess_video(url, dir)
#     end = time.time()
#     print(f"***********Playlist Download Finished in {end - start:.2f} seconds************")




# if __name__== '__main__':
#     playlist_url = "https://youtube.com/playlist?list=PLTPwffe8uEJvzs16CXOT0yLjkYyZraGLN&si=07m0hDNs-49FhjOF"
#     # urls = get_video_urls_from_playlist(playlist_url)
#     # for i, link in enumerate(urls, 1):
#     #     print(f"{i}: {link}")
#     # url= urls[0]
#     # url= "https://youtu.be/IU-RY9-alYg?si=FtIA5pgvdCFWQCaN"
#     dir= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp"
#     # postprocess_audio(local_audio_path)

#     download_and_postprocess_playlist(playlist_url, dir)
    

import yt_dlp
import os
import subprocess
import time
import re
import json
import hashlib
from typing import Dict, Any, List


# JSON file to store processing records
# PROCESSING_LOG_FILE = "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/meta_data/youtube_processing_log.json"
PROCESSING_LOG_FILE= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/meta_data/processed_files_logs_2.json"


def generate_url_id(url: str) -> str:
    """Generate a unique ID for a YouTube URL"""
    return hashlib.md5(url.encode()).hexdigest()


def load_processing_log() -> Dict[str, Any]:
    """Load the processing log from JSON file"""
    if os.path.exists(PROCESSING_LOG_FILE):
        try:
            with open(PROCESSING_LOG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def save_processing_log(log: Dict[str, Any]) -> None:
    """Save the processing log to JSON file"""
    with open(PROCESSING_LOG_FILE, 'w') as f:
        json.dump(log, indent=2, fp=f)


def update_processing_status(url: str, status: str, step: str = None, error: str = None) -> None:
    """Update the processing status for a URL"""
    log = load_processing_log()
    url_id = generate_url_id(url)
    
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if url_id not in log:
        log[url_id] = {
            "url": url,
            "url_id": url_id,
            "status": "initiated",
            "steps_completed": [],
            "created_at": current_time,
            "last_updated": current_time,
            "error": None,
            "final_output_path": None
        }
    
    log[url_id]["status"] = status
    log[url_id]["last_updated"] = current_time
    
    if step:
        if step not in log[url_id]["steps_completed"]:
            log[url_id]["steps_completed"].append(step)
    
    if error:
        log[url_id]["error"] = error
    
    save_processing_log(log)


def is_url_processed(url: str) -> bool:
    """Check if a URL has already been fully processed"""
    log = load_processing_log()
    url_id = generate_url_id(url)
    
    if url_id in log:
        return log[url_id]["status"] == "completed"
    return False


def get_processing_status(url: str) -> Dict[str, Any]:
    """Get the processing status for a URL"""
    log = load_processing_log()
    url_id = generate_url_id(url)
    return log.get(url_id, None)


def get_video_urls_from_playlist(playlist_url: str) -> List[str]:
    video_urls = []

    update_processing_status(playlist_url, "extracting_playlist", "playlist_extraction_started")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info_dict:
                for video in info_dict['entries']:
                    video_urls.append(video['url'])
        
        update_processing_status(playlist_url, "playlist_extracted", "playlist_extraction_completed")
        
    except Exception as e:
        update_processing_status(playlist_url, "failed", error=str(e))
        raise
    
    return video_urls


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', filename)


def download_youtube_video(url: str, dir: str) -> str:
    update_processing_status(url, "downloading", "download_started")
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown_title')
            sanitized_title = sanitize_filename(title)

        raw_audio_dir= os.path.join(dir, "raw_data")
        os.makedirs(raw_audio_dir, exist_ok=True)
        output_path = os.path.join(raw_audio_dir, f"{sanitized_title}.%(ext)s")
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
        
        final_path = os.path.join(raw_audio_dir, f"{sanitized_title}.mp3")
        update_processing_status(url, "downloaded", "download_completed")
        
        # Update the final output path in the log
        log = load_processing_log()
        url_id = generate_url_id(url)
        log[url_id]["final_output_path"] = final_path
        log[url_id]["filename"] = sanitized_title
        save_processing_log(log)
        
        return final_path
        
    except Exception as e:
        update_processing_status(url, "failed", error=f"Download failed: {str(e)}")
        raise


def ffmpeg_resample(input_path: str, output_path: str):
    cmd = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def postprocess_audio(audio_path: str, url: str):
    update_processing_status(url, "postprocessing", "postprocess_started")
    
    try:
        # output_path = audio_path.replace('.mp3', '_resampled.mp3')
        output_path= os.path.join("/".join(audio_path.split('/')[:-2]), "processed_data", "audios", audio_path.split('/')[-1])
        ffmpeg_resample(audio_path, output_path)
        
        # Delete original audio file
        os.remove(audio_path)
        
        # Update the final output path in the log
        log = load_processing_log()
        url_id = generate_url_id(url)
        log[url_id]["final_output_path"] = output_path
        save_processing_log(log)
        
        update_processing_status(url, "postprocessed", "postprocess_completed")
        
    except Exception as e:
        update_processing_status(url, "failed", error=f"Postprocessing failed: {str(e)}")
        raise


def download_and_postprocess_video(video_url: str, dir: str):
    # Check if URL has already been processed
    if is_url_processed(video_url):
        print(f"Skipping {video_url} - already processed")
        status = get_processing_status(video_url)
        if status and status.get("final_output_path"):
            print(f"Output file: {status['final_output_path']}")
        return
    
    try:
        update_processing_status(video_url, "initiated", "processing_started")
        
        local_audio_path = download_youtube_video(video_url, dir)
        if not local_audio_path:
            print(f"Skipping processing as download failed for {video_url}")
            return
        
        postprocess_audio(local_audio_path, video_url)
        update_processing_status(video_url, "completed", "all_steps_completed")
        print(f"Successfully processed: {video_url}")
        
    except Exception as e:
        update_processing_status(video_url, "failed", error=str(e))
        print(f"Failed to process {video_url}: {str(e)}")


def download_and_postprocess_playlist(playlist_url: str, dir: str):
    start = time.time()
    
    try:
        video_urls = get_video_urls_from_playlist(playlist_url)
        print(f"Found {len(video_urls)} videos in playlist")
        
        for i, url in enumerate(video_urls, 1):
            print(f"Processing video {i}/{len(video_urls)}: {url}")
            download_and_postprocess_video(url, dir)
        
        end = time.time()
        print(f"***********Playlist Download Finished in {end - start:.2f} seconds************")
        
        # Update playlist status
        update_processing_status(playlist_url, "completed", "playlist_processing_completed")
        
    except Exception as e:
        update_processing_status(playlist_url, "failed", error=str(e))
        print(f"Playlist processing failed: {str(e)}")
        raise


def print_processing_summary():
    """Print a summary of all processing records"""
    log = load_processing_log()
    if not log:
        print("No processing records found.")
        return
    
    print("\n" + "="*80)
    print("PROCESSING SUMMARY")
    print("="*80)
    
    for url_id, record in log.items():
        print(f"URL ID: {url_id}")
        print(f"URL: {record['url']}")
        print(f"Status: {record['status']}")
        print(f"Steps Completed: {', '.join(record['steps_completed'])}")
        print(f"Created: {record['created_at']}")
        print(f"Last Updated: {record['last_updated']}")
        if record.get('error'):
            print(f"Error: {record['error']}")
        if record.get('final_output_path'):
            print(f"Output: {record['final_output_path']}")
        print("-" * 80)


if __name__ == '__main__':
    playlist_url = "https://youtube.com/playlist?list=PLTPwffe8uEJvnUwiT1szDcdrL-DLZzdfn&si=hU92HmywhZxrMsmq"
    dir = "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data"
    
    
    try:
        download_and_postprocess_playlist(playlist_url, dir)
        print_processing_summary()
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        print_processing_summary()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print_processing_summary()
