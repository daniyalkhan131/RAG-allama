from ingestion.download import download_and_postprocess_playlist, download_and_postprocess_video, print_processing_summary


playlist_url = "https://youtube.com/playlist?list=PLTPwffe8uEJvL-_qhbJanghGSbmSlKohU&si=NJUhL5fbyx2luNCN"
dir = "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data"


# try:
#     download_and_postprocess_playlist(playlist_url, dir)
#     print_processing_summary()
    
# except KeyboardInterrupt:
#     print("\nProcessing interrupted by user")
#     print_processing_summary()
# except Exception as e:
#     print(f"An error occurred: {str(e)}")
#     print_processing_summary()


# for erroronous videos, so we are manually downloading and processing them again

video_urls= ['https://www.youtube.com/watch?v=elFbKpanL0Q',
 'https://www.youtube.com/watch?v=HZtQ_nrkEg4',
 'https://www.youtube.com/watch?v=2VYVTWrW24M',
 'https://www.youtube.com/watch?v=rypIit-0fUI',
 'https://www.youtube.com/watch?v=WpgOt3iYcBY']

for video_url in video_urls:
    try:
        download_and_postprocess_video(video_url, dir)
        print_processing_summary()
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        print_processing_summary()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print_processing_summary()