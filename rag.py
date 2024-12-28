from langchain_chroma import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain.vectorstores.utils import filter_complex_metadata


class DocLlama:

    def __init__(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
        self.embedding_model = FastEmbedEmbeddings()
        self.model = ChatOllama(model="mistral", use_gpu=False) #use=gpu=False to not use GPU
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        self.prompt = PromptTemplate.from_template(
            """
            <s> [INST] You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Do not invent answers. Keep the answer concise. [/INST] </s> 
                [INST] Question: {question} 
                Context: {context} 
                Answer: [/INST]
            """
        )

    def ingest(self, pdf_file_path: str):
        docs = PyPDFLoader(file_path=pdf_file_path).load()
        chunks = self.text_splitter.split_documents(docs)
        chunks = filter_complex_metadata(chunks)

        self.vector_store = Chroma.from_documents(documents=chunks, embedding=FastEmbedEmbeddings(), persist_directory="docllama_db")
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.5,
            },
        )

        self.chain = ({"context": self.retriever, "question": RunnablePassthrough()}
                      | self.prompt
                      | self.model
                      | StrOutputParser())

    def ask(self, query: str):
        if not self.vector_store or not self.chain:
            return "Please, upload a PDF document first."

        #For Debugging
        retriever_results = self.retriever.invoke(query)

        # Print the context to the console (for debugging purposes)
        print("Retrieved Context:")
        for result in retriever_results:
            print(result.page_content[:500])  # Accessing the content of each document (if using Document)
            print(result.metadata)  # Accessing metadata

        return self.chain.invoke(query)

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None