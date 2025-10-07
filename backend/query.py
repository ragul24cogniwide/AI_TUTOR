# Import required modules
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq  # Groq LLM (use this if langchain-groq is installed)
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


math8_db = Chroma(
    persist_directory="chroma_db/math8",
    embedding_function=embeddings
)


retriever = math8_db.as_retriever()

# # Optional: Test retrieval
# print("Fetching relevant documents...")
# docs = retriever.get_relevant_documents(
#     "Which of these numbers are divisible by 9: 999, 909, 900, 90, 990?"
# )
# for i, doc in enumerate(docs, 1):
#     print(f"\nDocument {i}:")
#     print(doc.page_content[:300], "...")
#     print("Metadata:", doc.metadata)



llm = ChatGroq(
    model="groq/compound",  
    api_key="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",
    temperature=0.7
)

# Build RAG QA chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)



query = "Which of these numbers are divisible by 9: 999, 909, 900, 90, 990?"
result = qa.invoke({"query": query})

#  Print answer
print("\nAnswer:\n", result['result'])

# #  Print retrieved source documents
# for i, doc in enumerate(result['source_documents'], 1):
#     print(f"\nSource {i}:")
#     print(doc.page_content[:300], "...")
#     print(doc.metadata)
