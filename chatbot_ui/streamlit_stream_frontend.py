import streamlit as st
from langgraph_backend import chatbot
from langchain.messages import HumanMessage

config = { 'configurable': {'thread_id': 1} }

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

for message in st.session_state["message_history"]:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input("Type here")

def stream_response():
    for message_chunk, metadata in chatbot.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="messages",
    ):
        content = message_chunk.content

        # Normal text response
        if isinstance(content, str) and content:
            yield content

        # Content can sometimes be a list of blocks
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text:
                        yield text

if user_input:
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.text(user_input)

    
    with st.chat_message("assistant"):
        
        ai_message = st.write_stream(stream_response)

    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})

