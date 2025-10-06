

import os
import re
import csv
import json
import time
import subprocess
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")


@dataclass
class ProcessingRecord:
    """Data class for tracking video processing status"""
    video_url: str
    video_id: str
    title: str
    status: str  # 'pending', 'downloaded', 'resampled', 'failed', 'skipped'
    audio_path: Optional[str]
    error_message: Optional[str]
    timestamp: str
    duration: Optional[float] = None


class YouTubeAudioProcessor:
    """Professional YouTube audio downloader with comprehensive status tracking"""
    
    def __init__(self, output_dir: str, log_file: str = "processing_log.csv", 
                 target_sample_rate: int = 16000):
        self.output_dir = Path(output_dir)
        self.log_file = Path(log_file)
        self.target_sample_rate = target_sample_rate
        self.status_db: Dict[str, ProcessingRecord] = {}
        
        # Setup directories and logging
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_status_db()
        
        # yt-dlp configuration for SABR workaround
        self.ydl_base_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192',
            # Try to use tv_simply client to bypass SABR issues
            'extractor_args': {
                'youtube': {
                    'player_client': ['default', 'tv_simply']
                }
            }
        }

    def _setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'downloader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_status_db(self):
        """Load existing processing status from CSV file"""
        if not self.log_file.exists():
            self._create_csv_header()
            return
            
        try:
            with open(self.log_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = ProcessingRecord(
                        video_url=row['video_url'],
                        video_id=row['video_id'],
                        title=row['title'],
                        status=row['status'],
                        audio_path=row['audio_path'] if row['audio_path'] else None,
                        error_message=row['error_message'] if row['error_message'] else None,
                        timestamp=row['timestamp'],
                        duration=float(row['duration']) if row['duration'] else None
                    )
                    self.status_db[record.video_url] = record
        except Exception as e:
            self.logger.error(f"Error loading status database: {e}")

    def _create_csv_header(self):
        """Create CSV file with proper headers"""
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'video_url', 'video_id', 'title', 'status', 'audio_path', 
                'error_message', 'timestamp', 'duration'
            ])

    def _update_status(self, record: ProcessingRecord):
        """Update status in both memory and CSV file"""
        self.status_db[record.video_url] = record
        
        # Append to CSV file
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                record.video_url, record.video_id, record.title, record.status,
                record.audio_path or '', record.error_message or '',
                record.timestamp, record.duration or ''
            ])

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*\n\r\t]', '', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()
        filename = re.sub(r'\.+$', '', filename)
        
        # Ensure filename isn't empty and isn't too long
        if not filename:
            filename = f"unknown_title_{int(time.time())}"
        # if len(filename) > 200:
        #     filename = filename[:200]
            
        return filename

    def get_video_metadata(self, url: str) -> Optional[Dict]:
        """Extract video metadata without downloading"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {url}: {e}")
            return None

    def get_playlist_videos(self, playlist_url: str) -> List[Dict]:
        """Extract video information from playlist"""
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'skip_download': True,
                'extractor_args': self.ydl_base_opts['extractor_args']
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(playlist_url, download=False)
                
                videos = []
                if 'entries' in info_dict:
                    for entry in info_dict['entries']:
                        if entry and 'url' in entry:
                            videos.append({
                                'url': entry['url'],
                                'id': entry.get('id', ''),
                                'title': entry.get('title', 'Unknown Title')
                            })
                
                self.logger.info(f"Found {len(videos)} videos in playlist")
                return videos
                
        except Exception as e:
            self.logger.error(f"Failed to extract playlist: {e}")
            return []

    def download_audio(self, video_url: str, video_id: str, title: str) -> Optional[str]:
        """Download audio from YouTube video"""
        start_time = time.time()
        sanitized_title = self.sanitize_filename(title)
        
        # Check if already processed successfully
        if video_url in self.status_db:
            record = self.status_db[video_url]
            if record.status == 'resampled' and record.audio_path and Path(record.audio_path).exists():
                self.logger.info(f"Skipping {title} - already processed successfully")
                return record.audio_path
            elif record.status == 'failed':
                self.logger.info(f"Skipping {title} - previously failed")
                return None

        try:
            # Set up download options
            output_template = str(self.output_dir / f"{sanitized_title}.%(ext)s")
            ydl_opts = {
                **self.ydl_base_opts,
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }

            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Find the downloaded MP3 file
            mp3_path = self.output_dir / f"{sanitized_title}.mp3"
            if not mp3_path.exists():
                # Sometimes the filename might be slightly different
                possible_files = list(self.output_dir.glob(f"{sanitized_title}*.mp3"))
                if possible_files:
                    mp3_path = possible_files[0]
                else:
                    raise FileNotFoundError("Downloaded MP3 file not found")

            # Update status as downloaded
            duration = time.time() - start_time
            record = ProcessingRecord(
                video_url= video_url,
                video_id= video_id,
                title=title,
                status= 'downloaded',
                audio_path= str(mp3_path),
                error_message= None,
                timestamp= datetime.now().isoformat(),
                duration= duration
            )
            self._update_status(record)
            
            self.logger.info(f"Downloaded: {title} ({duration:.2f}s)")
            return str(mp3_path)

        except Exception as e:
            # Log failure
            record = ProcessingRecord(
                video_url=video_url,
                video_id=video_id,
                title=title,
                status='failed',
                audio_path=None,
                error_message=str(e),
                timestamp=datetime.now().isoformat(),
                duration=time.time() - start_time
            )
            self._update_status(record)
            
            self.logger.error(f"Download failed for {title}: {e}")
            return None

    def resample_audio(self, input_path: str, target_sample_rate: int = None) -> Optional[str]:
        """Resample audio to target sample rate using ffmpeg"""
        if target_sample_rate is None:
            target_sample_rate = self.target_sample_rate
            
        input_path = Path(input_path)
        output_path = input_path.parent / f"{input_path.stem}_resampled{input_path.suffix}"
        
        try:
            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-ac", "1",  # Convert to mono
                "-ar", str(target_sample_rate),  # Set sample rate
                "-q:a", "2",  # High quality
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE, 
                text=True, 
                check=True
            )
            
            # Remove original file after successful resampling
            input_path.unlink()
            
            self.logger.info(f"Resampled: {input_path.name} -> {output_path.name}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg resampling failed: {e.stderr}")
            return None
        except Exception as e:
            self.logger.error(f"Resampling error: {e}")
            return None

    def process_video(self, video_info: Dict) -> bool:
        """Process a single video (download + resample)"""
        video_url = video_info['url']
        video_id = video_info.get('id', '')
        title = video_info.get('title', 'Unknown Title')
        
        start_time = time.time()
        
        try:
            # Step 1: Download audio
            audio_path = self.download_audio(video_url, video_id, title)
            if not audio_path:
                return False

            # Step 2: Resample audio
            resampled_path = self.resample_audio(audio_path)
            if not resampled_path:
                # Update status as resample failed
                record = ProcessingRecord(
                    video_url=video_url,
                    video_id=video_id,
                    title=title,
                    status='resample_failed',
                    audio_path=audio_path,
                    error_message="Resampling failed",
                    timestamp=datetime.now().isoformat(),
                    duration=time.time() - start_time
                )
                self._update_status(record)
                return False

            # Step 3: Update final success status
            record = ProcessingRecord(
                video_url=video_url,
                video_id=video_id,
                title=title,
                status='resampled',
                audio_path=resampled_path,
                error_message=None,
                timestamp=datetime.now().isoformat(),
                duration=time.time() - start_time
            )
            self._update_status(record)
            
            self.logger.info(f"Successfully processed: {title}")
            return True

        except Exception as e:
            # Log unexpected error
            record = ProcessingRecord(
                video_url=video_url,
                video_id=video_id,
                title=title,
                status='error',
                audio_path=None,
                error_message=str(e),
                timestamp=datetime.now().isoformat(),
                duration=time.time() - start_time
            )
            self._update_status(record)
            
            self.logger.error(f"Unexpected error processing {title}: {e}")
            return False

    def process_playlist(self, playlist_url: str) -> Dict[str, int]:
        """Process entire playlist with progress tracking"""
        start_time = time.time()
        
        self.logger.info(f"Starting playlist processing: {playlist_url}")
        
        # Get all videos from playlist
        videos = self.get_playlist_videos(playlist_url)
        if not videos:
            self.logger.error("No videos found in playlist")
            return {'total': 0, 'successful': 0, 'failed': 0, 'skipped': 0}

        # Process each video
        stats = {'total': len(videos), 'successful': 0, 'failed': 0, 'skipped': 0}
        
        for i, video_info in enumerate(videos, 1):
            self.logger.info(f"Processing {i}/{len(videos)}: {video_info.get('title', 'Unknown')}")
            
            # Check if already processed
            if video_info['url'] in self.status_db:
                record = self.status_db[video_info['url']]
                if record.status == 'resampled':
                    stats['skipped'] += 1
                    continue
            
            # Process the video
            success = self.process_video(video_info)
            if success:
                stats['successful'] += 1
            else:
                stats['failed'] += 1
            
            # Add small delay to be respectful to servers
            time.sleep(1)

        total_time = time.time() - start_time
        self.logger.info(f"Playlist processing completed in {total_time:.2f}s")
        self.logger.info(f"Results: {stats['successful']} successful, {stats['failed']} failed, {stats['skipped']} skipped")
        
        return stats

    def get_processing_summary(self) -> Dict:
        """Generate summary of processing status"""
        status_counts = {}
        for record in self.status_db.values():
            status_counts[record.status] = status_counts.get(record.status, 0) + 1
            
        return {
            'total_videos': len(self.status_db),
            'status_breakdown': status_counts,
            'log_file': str(self.log_file),
            'output_directory': str(self.output_dir)
        }


def main():
    """Main execution function"""
    # Configuration
    PLAYLIST_URL = "https://youtube.com/playlist?list=PLTPwffe8uEJvzs16CXOT0yLjkYyZraGLN&si=07m0hDNs-49FhjOF"
    OUTPUT_DIR = "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp"
    LOG_FILE = "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/meta_data/youtube_audio_processing.csv"
    
    # Initialize processor
    processor = YouTubeAudioProcessor(
        output_dir=OUTPUT_DIR,
        log_file=LOG_FILE,
        target_sample_rate=16000
    )
    
    try:
        # Process the playlist
        results = processor.process_playlist(PLAYLIST_URL)
        
        # Print summary
        print("\n" + "="*50)
        print("PROCESSING COMPLETE")
        print("="*50)
        print(f"Total videos: {results['total']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")
        
        # Print detailed summary
        summary = processor.get_processing_summary()
        print(f"\nOverall Summary:")
        print(f"Total processed videos: {summary['total_videos']}")
        print(f"Status breakdown: {summary['status_breakdown']}")
        print(f"Log file: {summary['log_file']}")
        print(f"Output directory: {summary['output_directory']}")
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()