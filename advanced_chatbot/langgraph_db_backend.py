from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

import os

import operator

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",   
    google_api_key=os.getenv('GEMINI_API_KEY')
)

############################# HELPER FUNCTIONS ##############################
def retreive_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    
    return (list(all_threads));

############################# TOOLS #########################################

search_tool = DuckDuckGoSearchRun(region="us-en")


@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform basic aritmetic operation on two numbers.
    Supported operations: add, sub, mul, div.
    """

    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by 0 not possible"}
            result = first_num / second_num
        else:
            return {"error": "Division by 0 is not allowed"}

        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    
    except Exception as e:
        return {"error": str(e)}
    

tools = [search_tool, calculator]

llm_with_tools = llm.bind_tools(tools)

############################ GRAPH NODES #####################################

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    # take user query
    messages = state['messages']

    # send to llm
    response = llm_with_tools.invoke(messages)
    # response
    return {'messages': [response]}

tool_node = ToolNode(tools)

############################# CHECKPOINTER ################################
conn = sqlite3.connect(database="advanced_chatbot/chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)


############################# GRAPH #####################################
graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")


chatbot = graph.compile(checkpointer=checkpointer)




# config = { 'configurable': {'thread_id': 1} }
# response = chatbot.invoke({'messages': [ HumanMessage(content = "What is my name?") ]}, config=config)
# print(response)