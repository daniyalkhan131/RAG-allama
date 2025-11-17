from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from chain import RAGService

load_dotenv('/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/.env')
# os.environ['LANGCHAIN_PROJECT']= 'allama-rag'

embedding_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
llm_model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.5)
client = QdrantClient(path="/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/langchain_qdrant")
vector_store = QdrantVectorStore(
    client=client,
    collection_name="allama_rag_dev",
    embedding=embedding_model,
)

rag= RAGService(
    vector_store=vector_store,
    llm_model= llm_model
)

question= "How does Surah Maryam describe the birth of Prophet Isa (Jesus)"

print(rag.workflow(question))