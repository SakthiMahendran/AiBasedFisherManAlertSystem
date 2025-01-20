from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from PyPDF2 import PdfReader
from docx import Document
import os
import tempfile

class AIHandler:
    """
    Handles AI operations, including document content extraction, embedding generation,
    and querying an AI model with memory support.
    """

    def __init__(self, model_name: str = "llama3-70b-8192", temperature: float = 0.7, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.chat_model = ChatGroq(
            model=model_name,
            temperature=temperature,
            api_key="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"
        )
        self.memory = ConversationBufferMemory()
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model)
        self.embedding_store = None  # To manage vector database
        self.token_limit = 3100  # Context window limit

    def extract_content(self, file, mime_type: str) -> str:
        content = ""
        try:
            if mime_type == "application/pdf":
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                    temp_pdf.write(file.read())
                    temp_pdf_path = temp_pdf.name
                reader = PdfReader(temp_pdf_path)
                content = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
                os.remove(temp_pdf_path)

            elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                suffix = ".doc" if mime_type == "application/msword" else ".docx"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_doc:
                    temp_doc.write(file.read())
                    temp_doc_path = temp_doc.name
                doc = Document(temp_doc_path)
                content = "\n".join(paragraph.text for paragraph in doc.paragraphs)
                os.remove(temp_doc_path)

            elif mime_type == "text/plain":
                content = file.read().decode("utf-8")

            else:
                raise ValueError(f"Unsupported MIME type: {mime_type}")

        except Exception as e:
            raise RuntimeError(f"Failed to extract content from file: {str(e)}")

        return content.strip()

    def generate_embeddings(self, content: str):
        if not content.strip():
            raise ValueError("Content is empty or whitespace-only.")
        try:
            # Chunk large content into sections of 200 words for better embeddings
            lines = content.split("\n")
            chunks = [" ".join(lines[i:i+200]) for i in range(0, len(lines), 200)]
            self.embedding_store = FAISS.from_texts(chunks, self.embedding_model)
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")

    def query_ai(self, query: str) -> str:
        if not self.embedding_store:
            return "I could not find any context in the provided documents. Here is general advice: consult a healthcare provider for specific medical recommendations."
        try:
            # Retrieve top 3 most similar documents
            similar_docs = self.embedding_store.similarity_search(query, k=8)
            if not similar_docs:
                return "I could not find any context in the provided documents. Here is general advice: consult a healthcare provider for specific medical recommendations."

            # Combine content from top 3 documents
            relevant_content = "\n".join(doc.page_content for doc in similar_docs)

            # Trim if exceeds token limit
            if len(relevant_content.split()) > self.token_limit:
                relevant_content = " ".join(relevant_content.split()[:self.token_limit])

            # Add user message to memory
            self.memory.chat_memory.add_user_message(query)

            # Prompt engineering with relevant content
            prompt = (
                f"You are a caring AI healthcare assistant called MedicAI. "
                f"Your job is to help users by providing accurate, empathetic, and actionable "
                f"responses to their questions. Based on the following document content:\n\n"
                f"{relevant_content}\n\nAnswer the user's question:\n{query}"
            )

            # Generate AI response
            response = self.chat_model.invoke(self.memory.chat_memory.messages + [{"role": "user", "content": prompt}])

            # Add AI response to memory
            self.memory.chat_memory.add_ai_message(response.content)
            return response.content

        except Exception as e:
            return f"An error occurred while querying: {str(e)}"


if __name__ == "__main__":
    ai_handler = AIHandler()

    # Simulate file upload
    with open("sample_report.pdf", "rb") as file:
        content = ai_handler.extract_content(file, "application/pdf")

    print("Extracted Content:")
    print(content)

    print("\nGenerating embeddings...")
    ai_handler.generate_embeddings(content)

    user_query = "What precautions should John take based on his medical history?"
    print("\nQuerying AI...")
    response = ai_handler.query_ai(user_query)

    print("\nAI Response:")
    print(response)
