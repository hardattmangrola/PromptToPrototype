# Healthcare RAG Assistant

## Project Overview

The Healthcare RAG Assistant is a sophisticated application designed to provide accurate, context-aware answers to medical queries. It leverages Retrieval-Augmented Generation (RAG) to ground its responses in verified medical documents provided by the user. The system ensures high reliability by strictly adhering to the context of uploaded documents and refusing to hallucinate information.

Users can upload medical PDFs, which the system processes and indexes. Subsequent queries are answered by retrieving relevant sections from these documents and using a Large Language Model (LLM) to synthesize a response. The application features a modern, responsive user interface that supports side-by-side document viewing and citation verification.

## Project Flow

1.  **Authentication**: Users register or log in to the platform. Role-based access control distinguishes between standard users and medical professionals.
2.  **Document Upload**: Users upload medical documents (PDF format) to the secure workspace.
3.  **Processing & Indexing**: The backend processes the PDFs, extracts text, and generates vector embeddings using Pinecone. These embeddings enable semantic search.
4.  **Querying**: Users ask medical questions via the chat interface.
5.  **Retrieval & Generation**: The system searches the vector database for relevant document chunks. It retrieves these chunks and sends them, along with the user's query, to the LLM.
6.  **Response & Citation**: The LLM generates an answer based solely on the provided context. The frontend displays the answer with clickable citations that open the specific page of the source PDF for verification.

## Key Features

### Backend
-   **FastAPI Framework**: High-performance, asynchronous API handling.
-   **Advanced RAG Pipeline**: Utilizes Vector Search (Pinecone) and LLMs (Groq/Google Gemini) for precise information retrieval.
-   **Document Processing**: robust PDF parsing and chunking for optimal context window usage.
-   **Secure Authentication**: JWT-based authentication with bcrypt hashing.
-   **Database Integration**: MongoDB for user data and metadata; Pinecone for vector embeddings.

### Frontend
-   **Modern User Interface**: Built with React, Vite, and Tailwind CSS for a clean, professional aesthetic.
-   **Split-Screen Workspace**: Integrated PDF viewer allows users to read source documents alongside the chat interface.
-   **Interactive Citations**: Direct links in chat responses navigate specific locations in the referenced documents.
-   **Incognito Mode**: Optional privacy mode where chat history is not persisted.
-   **Responsive Design**: Fully optimized for desktop and mobile devices.

## Technology Stack

-   **Frontend**: React, Vite, Tailwind CSS, Radix UI, Framer Motion, Zustand
-   **Backend**: Python, FastAPI, Motor (MongoDB), Pinecone Client, PyJWT, PyPDF
-   **AI/ML**: Groq API, Google Generative AI, Sentence Transformers

## Getting Started

### Prerequisites
-   Node.js (v18+)
-   Python (v3.10+)
-   MongoDB instance
-   Pinecone API Key
-   Groq or Google Gemini API Key

### Backend Setup
1.  Navigate to the backend directory.
2.  Create a virtual environment and activate it.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure environment variables (refer to `.env.example` if available).
5.  Start the server:
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend Setup
1.  Navigate to the frontend directory.
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```

## Usage

Access the application through your browser (typically `http://localhost:5173`). Log in to access the Clinical Workspace. Use the upload feature to add medical records or guidelines, then use the chat interface to query specific information contained within those documents.
