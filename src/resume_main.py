import os, uuid, io
from azure.ai.formrecognizer import DocumentAnalysisClient
import streamlit as st
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.search.documents import SearchClient
from dotenv import load_dotenv
from sqlagent.sqlagentMain import execute_query, generate_query, push_to_database
from Supervisor.feedback_agent import provide_feedback
#from completeness import evaluate_stats
import pandas as pd
import numpy as np
from azure.search.documents.indexes.models import (
    SearchableField,
    SimpleField,
    SearchFieldDataType,
    ScoringProfile,
    TextWeights,
    SearchIndex
)
# Download the blob to a local file
# Add 'DOWNLOAD' before the .txt extension so you can see both files in the data directory
load_dotenv("C:/Users/tharu/OneDrive/Documents/geakminds_scanner/util/.env")
account_url = os.environ.get("ACCOUNT_URL")
search_endpoint = os.environ.get("SEARCH_ENDPOINT")
search_api_key = os.environ.get("SEARCH_API_KEY")
index_name = os.environ.get("INDEX_NAME")



endpoint = os.environ.get("OPENAI_DOC_ENDPOINT")

required = []

helpful = []


search_credential = AzureKeyCredential(search_api_key)
search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=search_credential)
index_client = SearchIndexClient(endpoint=search_endpoint, credential=search_credential)
openai_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),  
    api_version="2024-10-21",
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="res1", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
    SearchableField(name="resumetext", type=SearchFieldDataType.String, analyzer_name="en.lucene")
]

scoring_profile = ScoringProfile(
    name="pythonScoring",
    text_weights=TextWeights(weights={
        "resumetext": 3,
        "res1": 3
    })
)

# Build the index
index = SearchIndex(
    name=index_name,
    fields=fields,
    scoring_profiles=[scoring_profile]
)

# Upload the index (this will replace if it exists)
index_client.create_or_update_index(index)

key = os.environ.get("OPENAI_DOC_API_KEY")

connect_str = os.environ.get("CONNECTION_STR")
blob_service_client = BlobServiceClient.from_connection_string(connect_str) #client for blob storage
    # Create the BlobServiceClient object
    # Create a unique name for the container
container_name = "bubble2" #name of container acccessed from blob storage
container_client = blob_service_client.get_container_client(container_name) #client for container

download_file_path = "bubble.pdf" 
resume_text = []
payload = []
count = 0 #tracking for id 
deployment_name='gpt-4o'#name of openai model used
substring = "SKILLS"#string from which the string splits

table_dict = {
    "score": [],
    "id": [],
    "file_name": [],
    "advice": [],
    "downloads": []
}

curr_description = "" #temporary string to store current description
container_client = blob_service_client.get_container_client(container= container_name) 
#print("\nDownloading blob to \n\t" + download_file_path)
doc_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))#client
tab1, tab2, tab3 = st.tabs(["Analysis", "Description", "Natural Language Query"])
uploaded_file = tab2.file_uploader("Upload a document", type=["pdf", "jpg", "png", "tiff"])
upload = tab2.button("upload resume")
txt = tab2.text_area(
    "Type a job description",
)
process_description = tab2.button("process")#button to process the description and turn it into keyword string.
newmark = tab2.markdown("")
reload = tab1.button("reload") #button to load the resume analysis
st.session_state.query_text = tab3.text_area(label="Enter a query")
new_button = tab3.button("Make Query")
table_name = tab3.text_input(label = "Enter a table name")
uploaded_file = tab3.file_uploader("Choose a file")
upload_csv = tab3.button("upload")
rowopp = tab3.checkbox("Check if you want to see rows returned by the query", value=False)

if "advice_list" not in st.session_state:
    st.session_state.advice_list = []
if "text_list" not in st.session_state:
    st.session_state.text_list = []
if "keyword_list" not in st.session_state:
    st.session_state.keyword_list = []
if "email_list" not in st.session_state:
    st.session_state.email_list = []
if "data_rendered" not in st.session_state:
    st.session_state.data_rendered = False
if "results" not in st.session_state:
    st.session_state.results = []
if "file_names" not in st.session_state:
    st.session_state.file_names = []
if "download_buttons" not in st.session_state:
    st.session_state.download_buttons = []
if "curr_description" not in st.session_state:
    st.session_state.curr_description = []
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "final_text" not in st.session_state:
    st.session_state.query_text = ""
if "database_name" not in st.session_state:
    st.session_state.database_name = ""
st.session_state.database_name = table_name
keywords = ""#'(skills:("python"^4 OR "numpy" OR "scipy" OR "pandas" OR "dask" OR "spacy" OR "nltk" OR "scikit-learn" OR "pytorch" OR "django" OR "flask" OR "pyramid" OR "sql" OR "nosql") AND experience:("machine learning"^3 OR "data pipelines" OR "code reviews" OR "cloud platforms" OR "aws" OR "azure" OR "google cloud" OR "open-source")) AND education:("computer science" OR "software engineering") AND softskills:("collaboration" OR "problem-solving" OR "communication")'
if 'keywords' not in st.session_state:
    st.session_state.keywords = ""
if new_button:
    st.session_state.final_text = generate_query("", st.session_state.query_text).replace("```", "").replace("sql", "")
    returned_data = execute_query(st.session_state.final_text, rowopp)
    if(not hasattr(returned_data, '__iter__')):
        tab3.markdown("Query executed successfully, returned "+str(returned_data))
    else:
        tab3.dataframe(returned_data)
    print(st.session_state.final_text)
    tab3.header("Provided Query:")
    tab3.markdown(st.session_state.final_text)

def render_ui():
    header_cols = tab1.columns([2, 2, 2, 4])  # Adjust widths as needed
    header_cols[0].markdown("**Score**")
    header_cols[1].markdown("**E-Mail**")
    header_cols[2].markdown("**Download**")
    header_cols[3].markdown("**Advice**")
    #print(str(st.session_state.email_list))
    for result in st.session_state.results:
        curr_index = int(result["id"])
        score = str(result["@search.score"])
        file_id = str(result["id"])
        file_name = st.session_state.file_names[curr_index]
        download_button_data = st.session_state.download_buttons[curr_index]
        #print("Type of download_button_data:", type(download_button_data))
        # Build advice string
        st.session_state.tempstring = ""
        response = str(provide_feedback(st.session_state.curr_description, st.session_state.text_list[curr_index]))
        #print()
        st.session_state.advice_list.append(response)
        advice_text = response
        email_curr = st.session_state.email_list[curr_index]
        # Render the row
        cols = tab1.columns([2, 2, 2, 4])  # Match header widths
        if(cols[0].button(label="send email", key=f"{str(curr_index+len(st.session_state.keyword_list))}")):
            if("@" in email_curr and ".com" in email_curr):
                try:
                    email_key = AzureKeyCredential(os.environ("EMAIL_KEY"))
                    endpoint = os.environ("EMAIL_ENDPOINT")

                    email_client = EmailClient(endpoint, email_key)

                    message = {
                        "content": {
                            "subject": "This is the subject",
                            "plainText": "This is the plaintext",
                            "html": "<html><h1>Hi! My name is Tharun!</h1></html>"
                        },
                        "recipients": {
                            "to": [
                                {
                                    "address": email_curr,
                                    "displayName": "Customer Name"
                                }
                            ]
                        },
                        "senderAddress": "DoNotReply@6f5836b9-a988-408b-b5d0-a4b4f5b37695.azurecomm.net"
                    }

                    poller = email_client.begin_send(message)
                    print("email sent to "+email_curr)
                except Exception as e:
                    print(e)
            else:
                print("not a real email")
        cols[1].markdown(email_curr)
        cols[2].download_button(
            label="Download",
            data=download_button_data,
            file_name=file_name,
            mime="text/plain",
            key=f"dl_{file_id}"
        )
        cols[3].markdown(advice_text)#markdown(str(result["@search.score"])+" - "+str(result["id"])+" - "+file_names[int(result["id"])])
        st.session_state.data_rendered = True
if st.session_state.data_rendered:
    print("true")
    render_ui()
if upload_csv:
    if uploaded_file is not None:
        push_to_database(uploaded_file, st.session_state.database_name)
if process_description:
    if txt != "":
        st.session_state.curr_description = txt
        response = openai_client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Extract keywords from the following job description and return them as a valid Lucene flat query string:\n\n{st.session_state.curr_description}\n\nfocus on actual skills and level (e.g junior vs senior), don't include any verbs or conjunctions, include quotations around the skills, and only return the Python string, nothing else."}
        ],
        max_tokens=200
        )
        st.session_state.keywords = str(response.choices[0].message.content)#.replace('"', '')
        st.session_state.keywords = st.session_state.keywords.replace("```python", "")
        st.session_state.keywords = st.session_state.keywords.replace("```", "")
        st.session_state.keyword_list = st.session_state.keywords.split(" ")
        print(str(st.session_state.keyword_list))
if upload:
    if uploaded_file is not None:
    # Convert Streamlit file uploader object to bytes stream
        file_bytes = uploaded_file.read()
        file_stream = io.BytesIO(file_bytes)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=uploaded_file.name)
        blob_client.upload_blob(file_bytes)
        with st.spinner("Analyzing..."):
            poller = doc_client.begin_analyze_document("prebuilt-document", document=file_stream)
            result = poller.result()
            #tab2.markdown(result)
if reload:
    count = 0
    st.session_state.file_names = []
    #st.write("Why hello there")
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container=container_name) 
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        print(blob.name)
        st.session_state.file_names.append(blob.name)
        blob_data = container_client.download_blob(blob.name).readall()
        if blob_data is not None:
            # Convert Streamlit file uploader object to bytes stream
            file_bytes = blob_data
            file_stream = io.BytesIO(file_bytes)
            st.session_state.download_buttons.append(file_stream)
            poller = doc_client.begin_analyze_document("prebuilt-document", document=file_stream)
            result = poller.result()
            #resume_text.append(file_stream)
            #print(str(file_stream))
            # Display the result
            text = ""
            # Print extracted text
            for page in result.pages:
                for line in page.lines:
                    text += line.content + "\n"
            resume_text.append(text)
            #print(text)
            response = openai_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Extract the email from the given string without any additional characters or markdown: "+text}
            ],
            max_tokens=200
            )
            st.session_state.email_list.append(response.choices[0].message.content)
            st.session_state.text_list.append(text)
        newdict = {
            "res1": text[:text.lower().find(substring.lower())], #Tharun
            "id": str(count),
            "resumetext": text[text.lower().find(substring.lower()):]
        }
        payload.append(newdict)
        count+=1
    print(len(payload))
    result = search_client.upload_documents(documents=payload)
    
    print("Upload succeeded:", all([r.succeeded for r in result]))
    print(st.session_state.keywords)
    # === 3. Run the search query using scoring profile ===
    st.session_state.results = list(search_client.search(
        query_type="simple",
        search_text = st.session_state.keywords,#'(skills:("python"^5 OR senior^5 OR"numpy" OR "scipy" OR "pandas" OR "dask" OR "spacy" OR "nltk" OR "scikit-learn" OR "pytorch" OR "django" OR "flask" OR "pyramid" OR "sql" OR "nosql") AND experience:("machine learning"^3 OR "data pipelines" OR "code reviews" OR "cloud platforms" OR "aws" OR "azure" OR "google cloud" OR "open-source")) AND education:("computer science" OR "software engineering") AND softskills:("collaboration" OR "problem-solving" OR "communication")',
        scoring_profile="pythonScoring",
        select="id",
        include_total_count=True))
    

    #print(payload)


    print("Total Documents Matching Query:", len(st.session_state.results))
    render_ui()
