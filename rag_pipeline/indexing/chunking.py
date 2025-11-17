from langchain_text_splitters import TextSplitter
from typing import List, Dict, Tuple
from langchain_core.documents import Document

class VADVTimeGapChunker(TextSplitter):
    def __init__(self, file_name, url, gap_threshold: float = 0.85, max_tokens: int = 300, **kwargs):
        super().__init__(**kwargs)
        self.gap_threshold = gap_threshold
        self.max_tokens = max_tokens
        # self.encoding = tiktoken.get_encoding(encoding_name)
        self.file_name= file_name
        self.url= url

    # def count_tokens(self, text: str) -> int:
    #     return len(self.encoding.encode(text))

    def split_documents(self, vad_segments: List[Dict]) -> List[Document]:
        paragraphs = []
        current_paragraph = []
        paragraph_start = None
        current_tokens = 0

        for i in range(len(vad_segments)):
            text = vad_segments[i]["transcription"]
            # tokens = self.count_tokens(text)
            tokens= vad_segments[i]["token_count"]
            # file_name= vad_segments[i]["filename"]

            if not current_paragraph:
                paragraph_start = vad_segments[i]["start"]
                current_paragraph.append(text)
                current_tokens = tokens
            else:
                gap = vad_segments[i]["start"] - vad_segments[i - 1]["end"]
                if gap > self.gap_threshold and current_tokens + tokens > self.max_tokens:
                    # finalize current paragraph
                    paragraphs.append(Document(
                        page_content=" ".join(current_paragraph),
                        metadata={"start": paragraph_start,
                                  "end": vad_segments[i - 1]["end"],
                                  "token_count": current_tokens + tokens,
                                  "file_name": self.file_name.split('.')[0],
                                  "url": self.url}
                    ))
                    # start new paragraph
                    current_paragraph = [text]
                    paragraph_start = vad_segments[i]["start"]
                    current_tokens = tokens
                else:
                    current_paragraph.append(text)
                    current_tokens += tokens

        # Handle any leftover
        if current_paragraph:
            paragraphs.append(Document(
                page_content=" ".join(current_paragraph),
                metadata={"start": paragraph_start,
                          "end": vad_segments[-1]["end"],
                          "token_count": current_tokens + tokens,
                          "file_name": self.file_name.split('.')[0],
                          "url": self.url}
            ))

        return paragraphs

    def split_text(self, text: str) -> List[str]:
        """Dummy method to fulfill abstract requirement."""
        return [text]


if __name__== '__main__':
    import json
    import os

    data_dir= "/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/data/processed_data"
    file_dir= os.path.join(data_dir, 'transcriptions')
    file_name= "Dars-e-Quran┇Surah Al-Ahzaab 56-58┇The real meaning of ‘Salat’ on the Prophet.json"
    file_path= os.path.join(file_dir, file_name)

    with open(file_path, 'r') as f:
        vad_segments= json.load(f) 

    splitter= VADVTimeGapChunker(gap_threshold= 0.85, max_tokens= 500)
    chunks = splitter.split_documents(vad_segments)