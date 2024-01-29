import random
from flask import Flask
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/sms", methods=["GET", "POST"])
def sms_reply():
    resp = MessagingResponse()

    item = random.choice([
        "Mobility",
        "Self-care",
        "Usual activities",
        "Pain/discomfort",
        "Anxiety/depression"
    ])

    resp.message(f"""
        På en skala fra 1 til 5, hvor mange problemer har du med {item}?
    """)

    # TODO: verify correct format (single-digit integer)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
