from typing import Annotated
from langchain_core.messages import convert_to_messages
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_openai import ChatOpenAI
import pymysql
import os

# We'll use `pretty_print_messages` helper to render the streamed agent outputs nicely
def execute_query(query: str):
    try: #credentials for aurora mysql database access are generated using AWS cli using aws get-sts get-credentials
        connection = pymysql.connect(
        host=os.environ['AURORA_HOST'], #aurora database host name
        user=os.environ['AURORA_USER'], #aurora database user name
        password=os.environ['AURORA_PASSWORD'], 
        database=os.environ['AURORA_DB'], #aurora database name
        port=3306
        )
        if("SELECT" in query):
            with connection:
                with connection.cursor() as cursor:
                    # Read a single record
                    sql = query
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    return result
        else:
            with connection:
                with connection.cursor() as cursor:
                    # Create a new record
                    sql = query
                    cursor.execute(sql) 
                    return "inserted"   
    except Exception as e:
        print(e)
def generate_query(job_descr: str, prompt_act: str):
    text_parts = []
    gpt_model = ChatOpenAI(model="gpt-3.5-turbo")
    def pretty_print_message(message, indent=False):
        pretty_message = message#.pretty_repr(html=True)
        text_parts.append(pretty_message.content)

    def pretty_print_messages(update, last_message=True):
        is_subgraph = False
        if isinstance(update, tuple):
            ns, update = update
            # skip parent graph updates in the printouts
            if len(ns) == 0:
                return

            graph_id = ns[-1].split(":")[0]
            #print(f"Update from subgraph {graph_id}:")
            #print("\n")
            is_subgraph = True

        for node_name, node_update in update.items():
            update_label = f"Update from node {node_name}:"
            if is_subgraph:
                update_label = "\t" + update_label

            #print(update_label)
            #print("\n")

            messages = convert_to_messages(node_update["messages"])
            if last_message:
                messages = messages[-1:]

            for m in messages:
                pretty_print_message(m, indent=is_subgraph)


    def create_handoff_tool(*, agent_name: str, description: str | None = None):
        name = f"transfer_to_{agent_name}"
        description = description or f"Transfer to {agent_name}"

        @tool(name, description=description)
        def handoff_tool(
            state: Annotated[MessagesState, InjectedState], 
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            tool_message = {
                "role": "tool",
                "content": f"Successfully transferred to {agent_name}",
                "name": name,
                "tool_call_id": tool_call_id,
            }
            return Command(  
                goto=agent_name,  
                update={"messages": state["messages"] + [tool_message]},  
                graph=Command.PARENT,  
            )
        return handoff_tool

    # Handoffs
    transfer_to_hotel_assistant = create_handoff_tool(
        agent_name="hotel_assistant",
        description="Transfer user to the skill evaluating assistant.",
    )
    transfer_to_flight_assistant = create_handoff_tool(
        agent_name="flight_assistant",
        description="Transfer user to the skill finding assistant.",
    )

    # Simple agent tools
    def make_query(person_name: str):
        """find the skills section"""
        return f""

    def exec_query(person_name: str):
        """rate a string of skills to the skills of a marketer and scoring it from 1 to 10"""
        return f""

    # Define agents
    query_maker = create_react_agent(
        model=gpt_model,
        tools=[make_query, transfer_to_hotel_assistant],
        prompt=
    f"Create a sql query that satisfies the following conditions: {prompt_act}, and print the query itself, not the data. Return the query without any additional text.",
        name="query_maker"
    )
    query_exec = create_react_agent(
        model=gpt_model,
        tools=[exec_query, transfer_to_flight_assistant],
        prompt=f"return the provided sql query",
        name="query_exec"
    )

    # Define multi-agent graph
    multi_agent_graph = (
        StateGraph(MessagesState)
        .add_node(query_maker)
        .add_node(query_exec)
        .add_edge(START, "query_maker")
        .compile()
    )
    content = prompt_act
    # Run the multi-agent graph
    for chunk in multi_agent_graph.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        },
        subgraphs=True
    ):
        pretty_print_messages(chunk)
    return "".join(text_parts)
#print(execute_query(generate_query("", "Get the first five rows of table1")))