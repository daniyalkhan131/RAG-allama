from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

class RAGService:
    def __init__(self, vector_store, llm_model, prompt_template_path="/Users/daniyalkhan/Documents/WORK-for-Compassion/projects/RAG-allama_audio/rag_service/prompt.txt"):
        self.retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        with open(prompt_template_path, 'r') as f:
            self.prompt_template= f.read()
        self.llm = llm_model
    
    def _format_docs(self, retrieved_docs):
        context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
        return context_text
    
    def workflow(self, question):
        
        parallel_chain = RunnableParallel({
            'context': self.retriever | RunnableLambda(self._format_docs),
            'question': RunnablePassthrough()
        })
        prompt = PromptTemplate(
            template= self.prompt_template,
            input_variables = ['context', 'question']
        )
        parser = StrOutputParser()
        config= {
            'run_name': 'v1-chain',
            'tags': ['retreival', 'question answer', 'llm generation'],
            'medadata': {'model': 'gemini-2.5-flash', 'temperature': 0}
        }
        chain = parallel_chain | prompt | self.llm | parser

        return chain.invoke(question, config= config)

