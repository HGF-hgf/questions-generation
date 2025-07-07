import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


DATA_path = r"data"
DB_path = r"db"

chroma_client = chromadb.PersistentClient(path=DB_path)
collection = chroma_client.get_or_create_collection(name="test_pdf")

loader = PyPDFDirectoryLoader(DATA_path)
raw_documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 300,
    chunk_overlap = 100,
    length_function = len,
    is_separator_regex = False,
)

chunks = text_splitter.split_documents(raw_documents)

documents = []
metadata = []
ids = []

i = 0 
for chunk in chunks:
    documents.append(chunk.page_content)
    metadata.append(chunk.metadata)
    ids.append(str(i))
    i += 1


collection.upsert(
    documents=documents,
    metadatas=metadata,
    ids=ids,
)