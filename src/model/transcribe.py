import torch
import nemo.collections.asr as nemo_asr
from typing import Dict, Any, Literal
import tiktoken

SAMPLE_RATE = 16000

class TranscriptionService:
    def __init__(self, model_name: str = "ai4bharat/indicconformer_stt_hi_hybrid_rnnt_large"):
        print(f"Initializing TranscriptionService with model: {model_name}...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        try:
            self.model = nemo_asr.models.ASRModel.from_pretrained(model_name)
            self.model.freeze()
            self.model = self.model.to(self.device)
            print("Model loaded and ready for inference.")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def transcribe_segment(
        self,
        audio: torch.Tensor,
        # vad_segment: Dict[str, Any],
        decoder: Literal["ctc", "rnnt"] = "ctc",
        language_id: str = "hi"
    ) -> Dict[str, Any]:
        
        if decoder not in ["ctc", "rnnt"]:
            raise ValueError("Decoder must be either 'ctc' or 'rnnt'.")

        # start_sample = int(vad_segment['start'] * SAMPLE_RATE)
        # end_sample = int(vad_segment['end'] * SAMPLE_RATE)
        # audio_segment = audio[:, start_sample:end_sample]


        segment_np = audio.cpu().numpy().squeeze(0)
        self.model.cur_decoder = decoder

        if decoder == 'ctc':
            transcription_result = self.model.transcribe(
                [segment_np], batch_size=1, logprobs=False, language_id=language_id
            )
        else:  # rnnt
            transcription_result = self.model.transcribe(
                [segment_np], batch_size=1, language_id=language_id
            )
        
        transcribed_text = transcription_result[0][0]
        token_count= self.count_tokens(transcribed_text)
        # vad_segment['transcription'] = transcribed_text
        
        return transcribed_text, token_count
    

    @staticmethod
    def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
        enc = tiktoken.encoding_for_model(model)
        tokens = enc.encode(text)
        return len(tokens)
    

if __name__ == "__main__":
    import json
    import torchaudio
    
    with open("/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp/Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet_resampled.json", 'r') as f:
        vad_segments= json.load(f)
    audio_path= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp/Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet_resampled.mp3"
    audio, sr= torchaudio.load(audio_path)

    transcription_model= TranscriptionService()
    
    for i in range(len(vad_segments)):
        start_sample = int(vad_segments[i]['start'] * SAMPLE_RATE)
        end_sample = int(vad_segments[i]['end'] * SAMPLE_RATE)
        audio_segment = audio[:, start_sample:end_sample]
        transcription, token_count= transcription_model.transcribe_segment(audio= audio_segment, decoder= 'ctc', language_id= 'hi')
        vad_segments[i]['transcription'] = transcription
        vad_segments[i]['token_count']= token_count

    # save
    output_file= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/temp/Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet_resampled_transcribed.json"
    with open(output_file, "w") as f:
        json.dump(vad_segments, f, indent=4)