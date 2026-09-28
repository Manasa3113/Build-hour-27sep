import os
import ssl

os.environ["HF_HUB_DISABLE_XET"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context

import streamlit as st
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from chains import build_rag_chain, CHROMA_DIR, COLLECTION_NAME, TOP_K
from memory import ConversationMemory
from config import GROQ_API_KEY, GROQ_MODEL

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@st.cache_resource
def get_retriever():
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )
    return vectorstore.as_retriever(search_kwargs={"k": TOP_K})


@st.cache_resource
def get_answer_fn(_retriever):
    llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0)
    return build_rag_chain(llm, _retriever)


def init_session():
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory()
    if "messages" not in st.session_state:
        st.session_state.messages = []


def clear_chat():
    st.session_state.memory.clear()
    st.session_state.messages = []


def main():
    st.set_page_config(page_title="Grow Bot — HDFC Mutual Fund FAQ", page_icon="🌱")
    st.title("Grow Bot — HDFC Mutual Fund FAQ")

    init_session()

    if st.button("Clear Chat", type="secondary"):
        clear_chat()
        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("source"):
                with st.expander("Sources"):
                    st.markdown(f"[View source]({msg['source']})")

    if prompt := st.chat_input("Ask about HDFC mutual fund schemes..."):
        st.session_state.memory.add_user_message(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        answer_fn = get_answer_fn(get_retriever())

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = answer_fn(prompt)

            st.markdown(result["answer"])
            if result.get("source"):
                with st.expander("Sources"):
                    st.markdown(f"[View source]({result['source']})")

        st.session_state.memory.add_assistant_message(result["answer"])
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "source": result.get("source", ""),
            }
        )


if __name__ == "__main__":
    main()
