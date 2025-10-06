import torch
from typing import Dict, List


class VADService:
    def __init__(self, repo_or_dir='snakers4/silero-vad', model='silero_vad'):
        print("Initializing VADService...")
        try:
            self.model, self.utils = torch.hub.load(
                repo_or_dir= repo_or_dir,
                model= model,
                force_reload=False
            )
            print("VAD model loaded successfully.")
        except Exception as e:
            print(f"Error loading Silero VAD model: {e}")
            raise

    def detect_speech(
        self,
        waveform: torch.Tensor,
        threshold: float = 0.3,
        min_speech_duration_ms: int = 500,
    ) -> List[Dict[str, float]]:

        (get_speech_timestamps, *_) = self.utils
        
        return get_speech_timestamps(
            waveform.squeeze(0),
            self.model,
            threshold=threshold,
            min_speech_duration_ms=min_speech_duration_ms,
            return_seconds=True,
            max_speech_duration_s= 40,
            min_silence_duration_ms= 2000,
            window_size_samples= 512,
            speech_pad_ms= 200
        )
    
if __name__== '__main__':
    import torchaudio
    import json


    audio_path= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp/Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet_resampled.mp3"
    audio, sr= torchaudio.load(audio_path)
    
    # perform vad
    vad= VADService(repo_or_dir='snakers4/silero-vad', model='silero_vad')
    vad_segments= vad.detect_speech(waveform= audio, threshold= 0.3, min_speech_duration_ms= 500)

    # save
    output_file= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp/Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet_resampled.json"
    with open(output_file, "w") as f:
        json.dump(vad_segments, f, indent=4)