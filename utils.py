# Import required libraries
import os  # Used for environment variable access
import streamlit as st  # Streamlit for building UI
from datetime import datetime  # Used for logging timestamps
from streamlit.logger import get_logger  # Streamlit's built-in logger
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings  # For embedding model
from langchain_community.llms import HuggingFaceHub  # For accessing LLMs via Hugging Face API
from langchain_community.llms import HuggingFaceHub # For accessing LLMs via Hugging Face API
from dotenv import load_dotenv
load_dotenv()  # ✅ Load environment variables from .env


# Initialize logger for tracking interactions and errors
logger = get_logger("LangChain-Chatbot")

# ✅ API Key Handling (For Local & Deployed Environments)
hugging_face_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")  # Local Environment
hf_api_token = st.secrets.get("HUGGINGFACEHUB_API_TOKEN")  # Streamlit Deployment

# Check if API key is available
api_token = hugging_face_api_token or hf_api_token  # Use available token
if not api_token:
    st.error("❌ Missing Hugging Face API Token! Set `HUGGINGFACEHUB_API_TOKEN` in `.env` (local) or Streamlit Secrets (deployed).")
    st.stop()  # Stop execution if API token is missing

# ✅ Decorator to enable chat history
def enable_chat_history(func):
    """
    Decorator to handle chat history and UI interactions.
    Ensures chat messages persist across interactions.
    """
    current_page = func.__qualname__  # Get function name to track current chatbot session

    # Clear session state if model/chatbot is switched
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = current_page  # Store the current chatbot session
    if st.session_state["current_page"] != current_page:
        try:
            st.cache_resource.clear()  # Clear cached resources
            del st.session_state["current_page"]
            del st.session_state["messages"]
        except Exception:
            pass  # Ignore errors if session state keys do not exist

    # Initialize chat history if not already present
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    # Display chat history in the UI
    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])

    def execute(*args, **kwargs):
        func(*args, **kwargs)  # Execute the decorated function

    return execute


def display_msg(msg, author):
    """
    Displays a chat message in the UI and appends it to session history.

    Args:
        msg (str): The message content to display.
        author (str): The author of the message ("user" or "assistant").
    """
    st.session_state.messages.append({"role": author, "content": msg})  # Store message in session
    st.chat_message(author).write(msg)  # Display message in Streamlit UI


def configure_llm():
    """
    Configure LLM to run on Hugging Face Inference API (Cloud-Based).
    
    Returns:
        llm (LangChain LLM object): Configured model instance.
    """
    available_llms = {
        "Mistral": "mistralai/Mistral-7B-Instruct-v0.1",
        "Llama-2": "meta-llama/Llama-2-7b-chat-hf",
        "Falcon": "tiiuae/falcon-7b-instruct"
    }

    # Sidebar to select LLM
    llm_opt = st.sidebar.radio(label="Select LLM", options=list(available_llms.keys()), key="SELECTED_LLM")
    
    # Get model ID based on user selection
    model_id = available_llms[llm_opt]  

    # ✅ Use Hugging Face Inference API for cloud execution
    llm = HuggingFaceHub(
        repo_id=model_id,
        task="text-generation",  # Hugging Face Inference Task
        huggingfacehub_api_token=api_token,  # Your API Key
        model_kwargs={
            "temperature": 0.7,  # Adjust response randomness
            "max_length": 512,   # Max response length
            "top_p": 0.9,        # Nucleus sampling
        }
    )

    return llm  # Return configured LLM

def print_qa(cls, question, answer):
    """
    Logs the Q&A interaction for debugging and tracking.

    Args:
        cls (class): The calling class.
        question (str): User question.
        answer (str): Model response.
    """
    log_str = f"\nUsecase: {cls.__name__}\nQuestion: {question}\nAnswer: {answer}\n" + "-" * 50
    logger.info(log_str)  # Log the interaction using Streamlit's logger


@st.cache_resource  # Cache the embedding model to avoid reloading it every time
def configure_embedding_model():
    """
    Configures and caches the embedding model.

    Returns:
        embedding_model (FastEmbedEmbeddings): The loaded embedding model.
    """
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")  # Load and return the embedding model


def sync_st_session():
    """
    Ensures Streamlit session state values are properly synchronized.
    """
    for k, v in st.session_state.items():
        st.session_state[k] = v  # Sync all session state values
