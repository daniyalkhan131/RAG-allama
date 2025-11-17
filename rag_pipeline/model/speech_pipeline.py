from typing import Any
from model.transcribe import TranscriptionService
from model.vad import VADService
from typing import List, Dict, Literal
import torchaudio

SAMPLE_RATE= 16000

class SpeechPipeline:
    """
    An orchestrator class that combines VAD and ASR services to create a
    full speech-to-text pipeline for audio files.
    
    This class uses composition to leverage VADService and TranscriptionService.
    """

    def __init__(
            self,
            vad_repo_or_dir='snakers4/silero-vad', 
            vad_model_name='silero_vad', 
            asr_model_name: str = "ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large"):
        """
        Initializes the pipeline by creating instances of the VAD and Transcription services.
        """

        print("\n--- Initializing Full Speech Pipeline ---")
        self.vad_service = VADService(repo_or_dir=vad_repo_or_dir, model= vad_model_name)
        self.transcription_service = TranscriptionService(model_name=asr_model_name)

        # Get the read_audio utility from the VAD service for convenience
        # (_, _, self.read_audio, *_) = self.vad_service.utils
        # print("--- Speech Pipeline Initialized Successfully ---\n")

    def process_audio_file(
        self,
        filepath: str,
        decoder: Literal["ctc", "rnnt"] = "ctc",
        language_id: str = "hi",
        vad_threshold: float = 0.3,
        min_speech_duration_ms: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        Processes an entire audio file from VAD to final transcription.

        Args:
            filepath (str): Path to the audio file.
            decoder (Literal["ctc", "rnnt"]): ASR decoder to use.
            language_id (str): Language ID for transcription.
            vad_threshold (float): Confidence threshold for VAD.

        Returns:
            List[Dict[str, Any]]: A list of segments, each containing timestamps
                                  and its corresponding transcription.
        """

        # 1. Read resampled audio
        print(f"Processing audio file: {filepath}")
        waveform, sr= torchaudio.load(filepath)
        
        # 2. Get speech segments using the VAD service
        vad_segments = self.vad_service.detect_speech(waveform= waveform, threshold= vad_threshold, min_speech_duration_ms= min_speech_duration_ms)
        
        if not vad_segments:
            print("No speech detected in the audio file.")
            return []
            
        print(f"Found {len(vad_segments)} speech segments. Transcribing...")
        transcribed_results = []
        
        # 3. Transcribe each segment using the Transcription service
        for i, segment in enumerate(vad_segments):
            start_sample = int(segment['start'] * SAMPLE_RATE)
            end_sample = int(segment['end'] * SAMPLE_RATE)
            audio_segment = waveform[:, start_sample:end_sample]
            
            transcription, token_count = self.transcription_service.transcribe_segment(
                audio= audio_segment, decoder=decoder, language_id=language_id
            )
            
            segment['transcription'] = transcription
            segment['token_count']= token_count
            transcribed_results.append(segment)
            # print(f"  - Segment {i+1} [{segment['start']:.2f}s - {segment['end']:.2f}s]: {transcription}")

        print("Transcription complete.")
        return transcribed_results

if __name__ == "__main__":
    import json
    import os

    data_dir= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/processed_data"
    audio_dir= os.path.join(data_dir, 'audios')
    file_name= "Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet.mp3"
    file_path= os.path.join(audio_dir, file_name)

    speech_pipeline= SpeechPipeline(
        vad_repo_or_dir='snakers4/silero-vad', 
        vad_model_name='silero_vad', 
        asr_model_name= "ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large"
    )
    transcribed_vad_segments= speech_pipeline.process_audio_file(
        filepath= file_path,
        decoder= "ctc",
        language_id= "hi",
        vad_threshold= 0.3,
        min_speech_duration_ms= 500,
    )

    output_file_name= file_name.replace(".mp3", ".json")
    with open(output_file_name, "w") as f:
        json.dump(transcribed_vad_segments, f, indent=4)