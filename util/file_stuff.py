from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import streamlit as st
import os
import io
import openai
from openai import AzureOpenAI

# Replace with your values
endpoint = os.environ.get("OPENAI_DOC_ENDPOINT")
key = os.environ.get("OPENAI_DOC_API_KEY")
client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),  
    api_version="2024-10-21",
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
# Set up client
client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

# Open the file and send it
file_path = "Color block resume.docx"
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "jpg", "png", "tiff"])
if uploaded_file is not None:
    # Convert Streamlit file uploader object to bytes stream
    file_bytes = uploaded_file.read()
    file_stream = io.BytesIO(file_bytes)

    with st.spinner("Analyzing..."):
        poller = client.begin_analyze_document("prebuilt-document", document=file_stream)
        result = poller.result()

    # Display the result
    name = st.text_input(label="",value="")
    while(name==None):
        pass
    text = ""
    # Print extracted text
    for page in result.pages:
        for line in page.lines:
            text += line.content + "\n"

    task = f"{name}"#"What programming languages does this person know?"
    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),  
        api_version="2024-10-21",
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        
    deployment_name='gpt-4o' 
        
    # Send a completion call to generate an answer
    print('Sending a test completion job')
    start_phrase = 'Write a tagline for an ice cream shop. '
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Provided is a sample resume{text}\n\nAnswer the following question:{task}"}
        ],
        max_tokens=1000
    )
    #print(response.choices[0].message.content)
    st.markdown("Question: "+task)
    st.markdown("Answer: "+response.choices[0].message.content)


