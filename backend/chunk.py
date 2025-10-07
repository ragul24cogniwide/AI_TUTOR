import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import pickle
#  Base path
base_path = "output/book8"

# Text splitter configuration
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,      # adjust based on how large chunks you want
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""],
)

#  Storage
all_docs = {}

#  Loop over subjects (math8, english8, etc.)
for subject_folder in os.listdir(base_path):
    subject_path = os.path.join(base_path, subject_folder)
    
    if not os.path.isdir(subject_path):  
        continue  # skip non-folder
    
    subject_docs = []
    
    # Loop over .md files in this subject
    for root, _, files in os.walk(subject_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # Split into chunks
                chunks = text_splitter.split_text(text)
                
                # Wrap into Documents with metadata
                subject_docs.extend([
                    Document(page_content=chunk, metadata={
                        "book": subject_folder, 
                        "source": file_path
                    }) 
                    for chunk in chunks
                ])
    
    # Store subject-wise docs
    all_docs[subject_folder] = subject_docs
    print(f" {subject_folder}: {len(subject_docs)} chunks created")

    # Print summary of all subjects
total_chunks = 0
for subject, docs in all_docs.items():
    print(f"{subject}: {len(docs)} chunks")
    total_chunks += len(docs)

print(f"\n Total chunks across all subjects: {total_chunks}")

# Save all_docs to a pickle file
with open("all_docs.pkl", "wb") as f:
    pickle.dump(all_docs, f)

print("\n📂 All chunks saved to all_docs.pkl")


# Now all_docs["math8"] and all_docs["english8"] are separate
print(all_docs["math8"][0].page_content)

