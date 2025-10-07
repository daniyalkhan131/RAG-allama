from ingestion.download import download_and_postprocess_playlist, print_processing_summary


playlist_url = "https://youtube.com/playlist?list=PLTPwffe8uEJsyGgifsOPQHyyZLPD9Tde9&si=ykgu3Jri59Nq4mNT"
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
