import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.tutor_assistant.prompts.prompt import get_system_prompt
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

class TutorAssistant:
   
    def __init__(self):
        pass
    
    def load_file(self):
        self.base_path = 'app/tutor_assistant/output/book'
        # print("path",os.path.exists(self.base_path))
        for path in os.listdir(self.base_path):
            if path not in ['.DS_Store']:
                for grade_path in os.listdir(os.path.join(self.base_path, path)):
                    if grade_path not in ['.DS_Store']:
                        for subject_path in os.listdir(os.path.join(self.base_path, path, grade_path)):
                            if subject_path.endswith('.md'):
                                # print("markdown data",subject_path)
                                with open(os.path.join(self.base_path, path, grade_path, subject_path), 'r') as file:
                                    self.markdown_data = file.read()
                                    chunk_data = ChunkData()
                                    embedding_data=chunk_data.chunk_markdown_data(self.markdown_data,subject_path)
                                    embeddings = EmbeddingDocuments()
                                    embeddings.embed_documents(embedding_data)
                                    # print("file readed for ",subject_path)
                        


class ChunkData:
    def __init__(self):
        self.documents = []

    def chunk_markdown_data(self, markdown_data, grade):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_text(markdown_data)
        grade_value = grade.split('_')[2].split('.')[0]  

        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": f"chunk_{i}", "grade": grade_value }
            )
            self.documents.append(doc)  

        # print(f"Created {len(self.documents)} chunks for grade {grade_value}")
        return self.documents

class EmbeddingDocuments:

    def __init__(self):
        pass

    def embedding_model(self,embedding_model='sentence-transformers/all-MiniLM-L6-v2'):
        return HuggingFaceEmbeddings(model_name=embedding_model)
        # for subject, docs in all_docs.items():
    def embed_documents(self, documents):
        db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory="chroma_db/books"
        )
        db.persist()
        print("Chroma DB created successfully!")



class RetrivalChain:

    def __init__(self):
        self.embeddings = EmbeddingDocuments().embedding_model(
            embedding_model='sentence-transformers/all-MiniLM-L6-v2'
        )
        self.system_prompt = get_system_prompt()
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
        )
        self.retriever = None 
        # print("prompts__", self.system_prompt)

    def get_documents(self):
        # print("🔹 Using embedding model:", self.embeddings)
        vectorstore = Chroma(
            persist_directory="chroma_db/books",
            embedding_function=self.embeddings, 
        )
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": 3, "filter": {"grade": "8"}})  # This grade should be dynamically fetch from student database for now you can use db.py as temporary solution
        return self.retriever
     
    def summarize_results(self):
        if not self.retriever:
            raise ValueError("Please call get_documents(query) first to initialize the retriever.")

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        chain = create_retrieval_chain(self.retriever, question_answer_chain)
        return chain










    
    



    

