import streamlit as st
from langchain_openai.chat_models import ChatOpenAI
import docx2txt
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

st.title("🦜🔗 Quickstart App")

openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

def get_document_content(uploaded_file):
    """
    Reads content from various document types.
    """
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
                return text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return docx2txt.process(uploaded_file)
        else:
            return "Unsupported file type."
    except Exception as e:
        return f"Error reading file: {e}"

def generate_response(input_text, doc_content=""):
    """
    Generates a response using the OpenAI model.
    If document content is provided, it is included in the prompt.
    """
    full_prompt = input_text
    if doc_content:
        full_prompt = f"{input_text}\n\nDocument Content:\n{doc_content}"
    
    model = ChatOpenAI(temperature=0.7, api_key=openai_api_key)
    st.info(model.invoke(full_prompt))

with st.form("my_form"):
    text = st.text_area(
        "Enter text:",
        "What are the three key pieces of advice for learning how to code?",
    )
    uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "docx"])
    
    submitted = st.form_submit_button("Submit")
    
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key!", icon="⚠")
    elif submitted and openai_api_key.startswith("sk-"):
        document_content = ""
        if uploaded_file is not None:
            document_content = get_document_content(uploaded_file)
        
        generate_response(text, document_content)

st.header("Chat with your Document")

uploaded_chat_file = st.file_uploader("Upload a document to chat with", type=["txt", "pdf", "docx"])

if uploaded_chat_file:
    if not openai_api_key.startswith("sk-"):
        st.warning("Please enter your OpenAI API key to process the document!", icon="⚠")
    else:
        if st.button("Process Document"):
            with st.spinner("Processing..."):
                doc_content = get_document_content(uploaded_chat_file)
                if "Error" in doc_content or "Unsupported" in doc_content:
                    st.error(doc_content)
                else:
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    texts = text_splitter.split_text(doc_content)
                    embeddings = OpenAIEmbeddings(api_key=openai_api_key)
                    st.session_state.vectorstore = FAISS.from_texts(texts, embedding=embeddings)
                    st.session_state.messages = []
                    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
                    st.success("Document processed! You can now chat.")

if "vectorstore" in st.session_state:
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the document"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Please enter your OpenAI API key to chat!", icon="⚠")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            llm = ChatOpenAI(temperature=0.7, api_key=openai_api_key)
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm,
                st.session_state.vectorstore.as_retriever(),
                memory=st.session_state.memory
            )

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = qa_chain({"question": prompt})
                    response = result["answer"]
                    st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
