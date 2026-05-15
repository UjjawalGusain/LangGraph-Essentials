import streamlit as st
from langgraph_backend import chatbot
from langchain.messages import HumanMessage
import uuid

# *****************************UTILITY FUNCTIONS******************************************
def generate_thread_id():
    new_thread_id = uuid.uuid4()
    return new_thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_conversation(thread_id):
    st.session_state['thread_id'] = thread_id
    updated_config = { 'configurable': {'thread_id': thread_id} }
    response = chatbot.get_state(config=updated_config).values

    conversation_message = []
    for message in response["messages"]:
        conversation_message.append({"role": "user" if type(message) is HumanMessage else "assistant", "content": message.content})

    st.session_state["message_history"] = conversation_message


# ****************************************************************************************



# *******************************SESSION SETUP********************************************
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = []

add_thread(st.session_state["thread_id"])

for message in st.session_state["message_history"]:
    with st.chat_message(message['role']):
        st.text(message['content'])



# ******************************SIDEBAR SETUP**********************************************

st.sidebar.title("Langgraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads']:
    if st.sidebar.button(str(thread_id)):
        load_conversation(thread_id)


# *****************************************************************************************


config = { 'configurable': {'thread_id': st.session_state["thread_id"]} }
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

