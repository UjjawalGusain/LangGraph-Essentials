from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage

from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import MemorySaver

import os

import operator

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",   
    google_api_key=os.getenv('GEMINI_API_KEY')
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    # take user query
    messages = state['messages']

    # send to llm
    response = llm.invoke(messages).content
    structured_response = AIMessage(content=(response[0]['text']))

    # response
    return {'messages': [structured_response]}

checkpointer = MemorySaver()

graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)
