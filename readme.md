# SMS-based data collection
This repo is under construction but will contain the code required to collect data from respondents via SMS, using Twilio.

The `app/.env` file (not in repo) should contain authentication information for Twilio, namely the following three entries:

```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
MESSAGING_SERVICE_SID=
```

# Sending Twilio-like requests
The file [`curl_requests.http`](/curl_requests.http) contains cURL requests that mimic those of Twilio through the webhook. The requests in the file use a dummy recipient, created at the end of [`postgres/init.sql`](/postgres/init.sql). Because the phone number isn't valid, one can't test this with an actual phone.
