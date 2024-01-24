import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(".env")

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="Party in the CIA",
    from_="+1 507 585 1781",
    to="+4560196801"
)

print(message.sid)
