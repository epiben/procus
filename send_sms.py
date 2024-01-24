import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(".env")

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="Party in the CIA, still",
    # from_="+1 507 585 1781",
    messaging_service_sid="MG06f833d7ac2df6991225efb31a9c8577",
    to="+4560196801"
)

print(message.sid)
