from typing import Annotated

from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import convert_to_messages
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from supervisor import make_it_happen
from dotenv import load_dotenv
import os

load_dotenv()

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
try:
    print(os.environ["AZURE_SP_KEY"])

    #llm = init_chat_model("openai:gpt-4.1")

    llm = init_chat_model("openai:gpt-3.5-turbo")
    graph_builder = StateGraph(State)

    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}


    # The first argument is the unique node name
    # The second argument is the function or object that will be called whenever
    # the node is used.
    graph_builder.add_node("chatbot", chatbot)

    graph_builder.add_edge(START, "chatbot")

    graph = graph_builder.compile()
except Exception as e:
    print(e)
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print(value["messages"][-1].content)



while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        prompt = """Extract all email addresses from the following text. 
DARREN
JONES
WORK EXPERIENCE
Marketing Manager
Marketing
Varsity Tutors
B:8 May 2023 - current
9
Brooklyn NY
Manager
· Directed six full-time marketers and three paid contractors,
enhancing team productivity by implementing agile
marketing methodologies
@
CONTACT
· Spearheaded the launch of a campaign for a new educational
product, resulting in revenue of $5.4M in the first year
Djones@email.com
J (123) 456-7890
· Streamlined lead management within HubSpot CRM,
facilitating a 32% decrease in lead-to-customer conversion
time
9 Brooklyn, NY
in Linkedin
· Developed partnerships with higher education institutions in
the US, resulting in an incremental $7M increase in revenue
· Identified under-performing vendors, leading to a $451k
reduction in costs while exceeding revenue targets
EDUCATION
Marketing Analyst
B.S.
Edward Jones Financial
Marketing
BRE August 2019 - May 2023
New York NY
University of Pittsburgh
Ha September 2014 - April 2018
· Built a comprehensive paid acquisition strategy across
Google, Facebook, and industry newsletters, attracting new
Pittsburgh, PA
leads that generated $17M in 2020
· Steered a strong brand awareness campaign through
conferences and speaking engagements, leading to a 78%
SKILLS
· HubSpot, Salesforce
increase in inbound leads year-over-year
. Led the implementation of real-time reporting on marketing
spend to adjust bid strategy, aiding a 27% bump in ROI
· Microsoft Excel, Word,
Powerpoint
· Exceeded growth targets every quarter by 24%, leveraging
Google Analytics to identify four high-performing channels
· Paid Ads (Facebook, Google,
LinkedIn, Instagram)
Marketing Analyst Intern
· A/B testing, audience
segmentation
· Google Analytics
DeltaV Digital
BEI August 2018 - August 2019
Washington DC
· SEO
· Created an A/B testing plan for Facebook ad copy,
contributing to a 21% improvement in ROI
· Generated reports in Tableau for the executive team around
KPIs like marketing spend, new leads, revenue generated, and
ROI, saving 16 hours of manual reporting per week
· Conducted comprehensive market trend analyses using MS
Excel, identifying key patterns that drove a significant boost
in targeted marketing campaign effectiveness
· Supported content marketing initiatives, contributing to an
SEO-optimized blog series that increased website backlinks
by 44% and amplified online visibility"""
        stream_graph_updates(prompt)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break