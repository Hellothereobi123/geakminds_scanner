import mlflow
import openai
import os
import textstat
import pandas as pd
from mlflow.metrics import flesch_kincaid_grade_level
from mlflow.metrics.genai import faithfulness, relevance, answer_relevance
from dotenv import load_dotenv

# Step 1: Add dummy or real context for faithfulness/relevance metrics
def evaluate_stats(input: str, response: str):
    eval_data = pd.DataFrame(
        {
            "inputs": [
                input
            ],
            "ground_truth": [ """
                - Collaborating with sales, marketing, advertising, product design and product development team members to plan promotional marketing campaigns
                - Creating editorial and content creation calendars for various media platforms and outlets
                - Assisting with the design, negotiation and placement of billboards, traditional media ads on TV and radio, social media ads and email blasts
                - Producing a brand style guide that best captures the company or client’s voice and mission
                - Helping team leads set, allocate and monitor the budget of each project
                - Meeting with clients to discuss brand guidelines, goals, budget and timelines
                - Conducting market research to determine a target audience’s needs, wants, habits, interests and other relevant factors
                - Researching previous successful campaigns to understand what worked, what didn’t and what can be improved
                - Reviewing the progress and success of a campaign, making adjustments or pitching ideas for new campaigns as necessary
                """.strip()
            ],
            "retrieved_chunks": [  # <- context column required for faithfulness/relevance
                response
            ]
        }
    )

    load_dotenv()

    with mlflow.start_run() as run:
        system_prompt = "Answer the following question in two sentences"
        
        # Log the GPT-4 model via MLflow
        logged_model_info = mlflow.openai.log_model(
            model="gpt-4",
            task=openai.chat.completions,
            name="model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "{question}"},
            ],
        )

        # Step 2: Evaluate with context mapping
        results = mlflow.evaluate(
            logged_model_info.model_uri,
            eval_data,
            targets="ground_truth",
            model_type="question-answering",
            extra_metrics=[
                flesch_kincaid_grade_level(),
                faithfulness(),
                relevance(),
                answer_relevance()
            ],
            evaluator_config={
                "col_mapping": {
                    "context": "retrieved_chunks"  # Tell MLflow which column to treat as "context"
                }
            }
        )
        return str(results.metrics['relevance/v1/mean'])
print(evaluate_stats("Good characteristics of marketer", "Skilled in Collaboration, design, writing, and market research"))

