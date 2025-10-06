from typing import List, Dict
from langchain_core.documents import Document
import time
from tqdm import tqdm


MAX_TOKENS_PER_MIN = 30000
MAX_REQUESTS_PER_MIN = 100

def process_embedding_batches(documents: List[Document], embedding_fn):
    batch = []
    batch_token_count = 0
    request_count = 0
    start_time = time.time()

    for doc in tqdm(documents):
        tokens = doc.metadata.get("token_count", 0)
        
        # If adding this doc would exceed limits, flush batch first
        if (
            batch_token_count + tokens > MAX_TOKENS_PER_MIN or
            len(batch) + 1 > MAX_REQUESTS_PER_MIN
        ):
            # Respect rate limits
            elapsed = time.time() - start_time
            if elapsed < 60:
                time.sleep(60 - elapsed)
            # Send batch
            print(f"Sending batch of {len(batch)} docs with {batch_token_count} tokens.")
            print(batch)
            embedding_fn(batch)
            request_count += len(batch)
            batch = []
            batch_token_count = 0
            start_time = time.time()  # reset timer

        # Add current doc to batch
        batch.append(doc)
        batch_token_count += tokens

    # Send remaining batch
    if batch:
        elapsed = time.time() - start_time
        if elapsed < 60:
            time.sleep(60 - elapsed)
        print(f"Sending final batch of {len(batch)} docs with {batch_token_count} tokens.")
        print(batch)
        embedding_fn(batch)
        request_count += len(batch)

    print(f"Total requests sent: {request_count}")


if __name__ == "__main__":
    from qdrant_client import QdrantClient
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_qdrant import QdrantVectorStore
    from chunking import VADVTimeGapChunker
    import os
    import json

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    client = QdrantClient(path="/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/langchain_qdrant")
    # client.create_collection(
    #     collection_name="allama_rag_dev",
    #     vectors_config= models.VectorParams(size= 3072, distance= models.Distance.COSINE),
    # )
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="allama_rag_dev",
        embedding=embeddings,
    )

    data_dir= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/processed_data"
    file_dir= os.path.join(data_dir, 'transcriptions')
    file_name= "Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet.json"
    file_path= os.path.join(file_dir, file_name)
    with open(file_path, 'r') as f:
        vad_segments= json.load(f) 
    splitter= VADVTimeGapChunker(file_name= file_name, gap_threshold= 0.85, max_tokens= 500)
    chunks = splitter.split_documents(vad_segments)


    process_embedding_batches(chunks, vector_store.add_documents)
