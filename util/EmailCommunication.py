from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()
try:
    key = AzureKeyCredential(os.environ.get("EMAIL_KEY"))
    endpoint = AzureKeyCredential(os.environ.get("EMAIL_ENDPOINT"))

    email_client = EmailClient(endpoint, key)

    message = {
        "content": {
            "subject": "This is the subject",
            "plainText": "This is the plaintext",
            "html": "<html><h1>Hi there!</h1></html>"
        },
        "recipients": {
            "to": [
                {
                    "address": "tharun.dilliraj@gmail.com",
                    "displayName": "Customer Name"
                }
            ]
        },
        "senderAddress": "DoNotReply@6f5836b9-a988-408b-b5d0-a4b4f5b37695.azurecomm.net"
    }

    poller = email_client.begin_send(message)
    print("Result: " + str(poller.result()))
except Exception as e:
    print(e)
