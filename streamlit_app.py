import streamlit as st
from langchain_openai.chat_models import ChatOpenAI
import docx2txt
import pdfplumber

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
