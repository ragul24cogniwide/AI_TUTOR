import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from app.tutor_assistant.prompts.prompt import get_system_prompt_maths,get_system_prompt_english
from langchain.chat_models import AzureChatOpenAI
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_API_TYPE = os.getenv("AZURE_OPENAI_API_TYPE")
OPENAI_API_BASE = os.getenv("AZURE_OPENAI_API_BASE")
OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# Set the OpenAI library configuration using the retrieved environment variables
openai.api_type = OPENAI_API_TYPE
openai.api_base = OPENAI_API_BASE
openai.api_version = OPENAI_API_VERSION
openai.api_key = OPENAI_API_KEY

# ───────────────────────────────────────────────
# Tutor Assistant Classes
# ───────────────────────────────────────────────

class TutorAssistant:
    def __init__(self):
        pass

    def load_file(self):
        self.base_path = 'app/tutor_assistant/output/book'
        for path in os.listdir(self.base_path):
            if path not in ['.DS_Store']:
                for grade_path in os.listdir(os.path.join(self.base_path, path)):
                    if grade_path not in ['.DS_Store']:
                        for subject_path in os.listdir(os.path.join(self.base_path, path, grade_path)):
                            if subject_path.endswith('.md'):
                                with open(os.path.join(self.base_path, path, grade_path, subject_path), 'r') as file:
                                    markdown_data = file.read()
                                    chunk_data = ChunkData()
                                    embedding_data = chunk_data.chunk_markdown_data(markdown_data, subject_path)
                                    embeddings = EmbeddingDocuments()
                                    embeddings.embed_documents(embedding_data)


class ChunkData:
    def __init__(self):
        self.documents = []

    def chunk_markdown_data(self, markdown_data, metadata_key):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_text(markdown_data)

        subject_value = metadata_key.split('_')[1]
        grade_value = metadata_key.split('_')[2].split('.')[0]

        print("subject:", subject_value)
        print("grade:", grade_value)

        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={"source": f"chunk_{i}", "grade": grade_value, "subject": subject_value}
            )
            # print(doc)
            self.documents.append(doc)

        return self.documents


class EmbeddingDocuments:
    def embedding_model(self, embedding_model='sentence-transformers/all-MiniLM-L6-v2'):
        return HuggingFaceEmbeddings(model_name=embedding_model)

    def embed_documents(self, documents):
        db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model(),
            persist_directory="chroma_db/books"
        )
        db.persist()
        print("✅ Chroma DB created successfully!")
# ───────────────────────────────────────────────
# Retrieval Chain with Memory
# ───────────────────────────────────────────────
class RetrievalChain:
    def __init__(self, subject: str):
        # Embeddings
        self.embeddings = EmbeddingDocuments().embedding_model(
            embedding_model='sentence-transformers/all-MiniLM-L6-v2'
        )

        # System prompt
        self.system_prompt = get_system_prompt_maths() if subject == "maths" else get_system_prompt_english()

        # LLM
        self.llm = AzureChatOpenAI(
            openai_api_version=OPENAI_API_VERSION,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            openai_api_type=OPENAI_API_TYPE,
            deployment_name="gpt-4o-mini",
            temperature=0,
            verbose=True,
        )

        # Memory for last 20 exchanges
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=3,
            return_messages=True
        )

        self.retriever = None
        self.subject = subject

    def get_documents(self):
        vectorstore = Chroma(
            persist_directory="chroma_db/books",
            embedding_function=self.embeddings,
        )
        self.retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 3,
                "filter": {
                    "$and": [
                        {"grade": "7"},
                        {"subject": self.subject}
                    ]
                }
            }
        )
        return self.retriever

    def build_conversational_chain(self):
        if not self.retriever:
            raise ValueError("Call get_documents() first.")

        # Use system prompt + human template including chat history & context
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "CHAT HISTORY:\n{chat_history} \n Human:\n{question}")
        ])

        # Build conversational retrieval chain with memory
        retrieval_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            return_source_documents=False,
            verbose=True,
            combine_docs_chain_kwargs={"prompt": prompt},
            rephrase_question=False,   
        )

        return retrieval_chain

    async def chat(self, user_input: str):
        if not self.retriever:
            self.get_documents()

        chain = self.build_conversational_chain()

        # Optional: print formatted history for debugging
     
        # Call chain (memory is automatically used)
        response = await chain.ainvoke({
            "question": user_input,
            "chat_history": self.memory.chat_memory.messages
        })

        # No need to manually add to memory — handled by chain
        return response["answer"]
    
# class RetrievalChain:
#     def __init__(self,subject: str):
#         self.embeddings = EmbeddingDocuments().embedding_model(
#             embedding_model='sentence-transformers/all-MiniLM-L6-v2'
#         )
#         self.system_prompt = get_system_prompt_maths() if subject == "maths" else get_system_prompt_english()
#         self.llm = AzureChatOpenAI(
#             openai_api_version=OPENAI_API_VERSION,
#             openai_api_key=OPENAI_API_KEY,
#             openai_api_base=OPENAI_API_BASE,
#             openai_api_type=OPENAI_API_TYPE,
#             deployment_name="gpt-4o-mini",
#             temperature=0,
#             verbose=True,
#         )

#         # 🧠 Maintain last 10 exchanges
#         self.memory = ConversationBufferWindowMemory(
#             memory_key="chat_history",
#             k=20,
#             return_messages=True
#         )

#         self.retriever = None
#         self.subject = subject

#     def get_documents(self):
#         print(f"Getting documents for subject: { self.subject}")
#         vectorstore = Chroma(
#             persist_directory="chroma_db/books",
#             embedding_function=self.embeddings,
#         )
#         self.retriever = vectorstore.as_retriever(
#             search_kwargs={"k": 3, "filter": {
#                     "$and": [
#                         {"grade": "7"},
#                         {"subject": self.subject}
#                     ]
#                 }}
#         )
#         return self.retriever
    

#     def get_important_topics(self, query: str):
#         print(f"Getting important topics for query: {query}")
#         return self.retriever.invoke(query)

#     def build_conversational_chain(self):
#         if not self.retriever:
#             raise ValueError("Call get_documents() first to initialize the retriever.")

#         # Custom prompt that correctly includes chat history + context
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", self.system_prompt),
#             ("human", "{input}")
#         ])

#         combine_docs_chain = create_stuff_documents_chain(
#             llm=self.llm,
#             prompt=prompt,
#         )

#         combine_docs_chain = combine_docs_chain.with_config({"verbose": True})

#         retrieval_chain = create_retrieval_chain(
#             retriever=self.retriever,
#             combine_docs_chain=combine_docs_chain,
#         )

#         retrieval_chain = retrieval_chain.with_config({"verbose": True})

#         return retrieval_chain

#     async def chat(self, user_input: str):
#         if not self.retriever:
#             self.get_documents()

#         retrieval_chain = self.build_conversational_chain()

#         # Format chat history into readable text for the prompt
#         formatted_history = "\n".join([
#             f"{m.type.capitalize()}: {m.content}" for m in self.memory.chat_memory.messages
#         ])

#         # ✅ Pass 'input', not 'question'
#         response = await retrieval_chain.ainvoke({
#             "input": user_input,
#             "chat_history": formatted_history,
#         })

#         # Store conversation in memory manually
#         self.memory.chat_memory.add_user_message(user_input)
#         self.memory.chat_memory.add_ai_message(response["answer"])

#         return response["answer"]
    
