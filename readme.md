# SMS-based data collection
This repo is under construction but will contain the code required to collect data from respondents via SMS, using CPSMS (cpsms.dk) as the SMS gateway.

Two configuration files are needed to make this system work, but they are unstaged and so must be recreated after cloning this repo.

First, the `app/.env` file must specify the API token of CPSMS:

```
CPSMS_API_TOKEN=<token>
```

Second, the `ngrok/ngrok.yaml` file should contain the following information (at least):

```
version: "2"
authtoken: <token>
tunnels:
  fastapi:
    proto: http
    addr: fastapi:5000
    domain: <ngrok_subdomain>.ngrok-free.app
```

## Sending CPSMS-like requests
The file [`curl_requests.http`](/curl_requests.http) contains cURL requests that mimic those of CPSMS through the webhook. The requests in the file use a dummy recipient (Mr McUrl), created at the end of [`postgres/init.sql`](/postgres/init.sql). Because the phone number isn't valid, one can't test this with an actual phone.
