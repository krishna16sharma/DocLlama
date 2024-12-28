import os
import tempfile
import streamlit as st
from streamlit_chat import message
from rag import DocLlama

st.set_page_config(page_title="DocLLama", page_icon="images/DocLlama.png")

# Custom avatars
USER_AVATAR = "images/user.svg" 
ASSISTANT_AVATAR = "images/DocLlama.png"

st.markdown(
    """
<style>
    [class*="docllama-assistant"] .stChatMessage {
        flex-direction: row-reverse;
    }
</style>
""",
    unsafe_allow_html=True,
)

def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        avatar = USER_AVATAR if is_user else ASSISTANT_AVATAR
        with st.container(key=f"docllama-user-{i}" if is_user else f"docllama-assistant-{i}"):
            with st.chat_message("user" if is_user else "assistant", avatar=avatar):
                st.markdown(msg)
    st.session_state["thinking_spinner"] = st.empty()


def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
            agent_text = st.session_state["assistant"].ask(user_text)

        st.session_state["messages"].append((user_text, True))
        st.session_state["messages"].append((agent_text, False))


def read_and_save_file():
    st.session_state["assistant"].clear()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

    for file in st.session_state["file_uploader"]:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        with st.session_state["ingestion_spinner"], st.spinner(f"Ingesting {file.name}"):
            st.session_state["assistant"].ingest(file_path)
        os.remove(file_path)


def page():
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["assistant"] = DocLlama()

    st.header("DocLlama")
    st.write(
        """
        DocLlama is an AI-powered document assistant designed to help you interact with your PDFs.
        Upload a document, ask questions, and get answers based on the content of your file!
        """
    )

    st.subheader("Upload a document")
    st.file_uploader(
        "Upload document",
        type=["pdf"],
        key="file_uploader",
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()
    st.text_input("Message", key="user_input", on_change=process_input)

    st.markdown(f"""
    <footer style="position: fixed; bottom: 0; left: 0; right: 0; text-align: center; padding: 10px; background-color: #f1f1f1; font-size: 14px;">
        Made by Krishna Sharma S | &copy; 2024
    </footer>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    page()