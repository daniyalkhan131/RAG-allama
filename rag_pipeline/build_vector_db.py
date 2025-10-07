import json
from model.speech_pipeline import SpeechPipeline
from indexing.chunking import VADVTimeGapChunker
import os
from indexing.embed import process_embedding_batches
from qdrant_client import QdrantClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv

load_dotenv('/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/.env')


with open("/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/meta_data/youtube_processing_log.json", 'r') as f:
    downloaded_audio_data= json.load(f)


speech_pipeline= SpeechPipeline(
    vad_repo_or_dir='snakers4/silero-vad', 
    vad_model_name='silero_vad', 
    asr_model_name= "ai4bharat/indicconformer_stt_hi_hybrid_rnnt_large"
)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
qdrant_client = QdrantClient(
    url=os.getenv('QDRANT_ENDPOINT'), 
    api_key=os.getenv('QDRANT_API_KEY'),
)
vector_store = QdrantVectorStore(
    client=qdrant_client,
    collection_name="allama-rag-dev",
    embedding=embeddings,
)

# meta_data= {}
for i in downloaded_audio_data:
    file_output_path= downloaded_audio_data[i]['final_output_path']
    if file_output_path and downloaded_audio_data[i]['status']== 'completed':
        transcribed_vad_segments= speech_pipeline.process_audio_file(
            filepath= file_output_path,
            decoder= "ctc",
            language_id= "hi",
            vad_threshold= 0.3,
            min_speech_duration_ms= 500,
        )

        output_file= file_output_path.replace('.mp3', '.json').replace("audios", "transcriptions")
        with open(output_file, 'w') as f:
            json.dump(transcribed_vad_segments, f, ensure_ascii= False, indent= 4)
            
        # meta_data[i]= downloaded_audio_data[i]
        downloaded_audio_data[i]['speech_pipeline_status']= 'completed'
        downloaded_audio_data[i]['speech_pipeline_output']= transcribed_vad_segments
        downloaded_audio_data[i]['speech_pipeline_output_path']= output_file


        splitter= VADVTimeGapChunker(file_name= downloaded_audio_data[i]['filename'], gap_threshold= 0.85, max_tokens= 500)
        chunks = splitter.split_documents(downloaded_audio_data[i]['speech_pipeline_output'])
        downloaded_audio_data[i]['chunking_status']= 'completed'
        
        process_embedding_batches(chunks, vector_store.add_documents)
        
        downloaded_audio_data[i]['embedding_status']= 'completed'
        downloaded_audio_data[i]['num_chunks']= len(chunks)
        print(f"Completed processing for {downloaded_audio_data[i]['filename']} with {len(chunks)} chunks.")
        print(f"tokens: {[i['token_count'] for i in chunks]}")

with open("/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/meta_data/files_processed_metadata.json", 'w') as f:
    json.dump(downloaded_audio_data, f, ensure_ascii= False, indent= 4)