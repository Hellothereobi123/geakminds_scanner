from typing import Annotated
from langchain_core.messages import convert_to_messages
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_openai import ChatOpenAI

# We'll use `pretty_print_messages` helper to render the streamed agent outputs nicely
def provide_feedback(job_descr: str, prompt: str):
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
    def find_skills(person_name: str):
        """find the skills section"""
        return f""

    def eval_skills(person_name: str):
        """rate a string of skills to the skills of a marketer and scoring it from 1 to 10"""
        return f""

    # Define agents
    flight_assistant = create_react_agent(
        model=gpt_model,
        tools=[find_skills, transfer_to_hotel_assistant],
        prompt="""
    You are an assistant that only locates the skills section from a resume. 
    After you locate the skills section, you must call the tool `transfer_to_hotel_assistant` 
    so the hotel assistant can evaluate the skills.
    """,
        name="flight_assistant"
    )
    hotel_assistant = create_react_agent(
        model=gpt_model,
        tools=[eval_skills, transfer_to_flight_assistant],
        prompt=f"You are an assistant comparing a string of skills to the skills of the following: {job_descr} and giving an overall score from 1 to 10. Be really harsh when grading.",
        name="hotel_assistant"
    )

    # Define multi-agent graph
    multi_agent_graph = (
        StateGraph(MessagesState)
        .add_node(flight_assistant)
        .add_node(hotel_assistant)
        .add_edge(START, "flight_assistant")
        .compile()
    )
    content = prompt
    """
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
new_content ="""
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
job_descr = """
Marketer duties and responsibilities
A Marketer works with other members of a sales or marketing team to plan, execute and monitor a successful marketing campaign. Their duties and responsibilities often include:

Collaborating with sales, marketing, advertising, product design and product development team members to planning promotional marketing campaigns
Creating editorial and content creation calendars for various media platforms and outlets
Assisting with the design, negotiation and placement of billboards, traditional media ads on TV and radio, social media ads and email blasts
Producing a brand style guide that best captures the company or client’s voice and mission
Helping team leads set, allocate and monitor the budget of each project
Meeting with clients to discuss brand guidelines, goals, budget and timelines
Conducting market research to determine a target audience’s needs, wants, habits, interests and other relevant factors used in creating targeted marketing campaigns
Researching previous successful campaigns to understand what worked, what didn’t and what can be improved
Reviewing the progress and success of a campaign, making adjustments or pitching ideas for new campaigns as necessary
"""
#print(make_it_happen(job_descr, new_content))