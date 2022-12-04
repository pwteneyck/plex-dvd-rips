#! /usr/bin/bash

# put anything in here
# for example:

curl -X POST https://api.twilio.com/2010-04-01/Accounts/ACCOUNT_ID/Messages.json \
        --data-urlencode "Body=$1" \
        --data-urlencode "From=TWILIO_NUMBER" \
        --data-urlencode "To=MY_COOL_PHONE_NUMBER" \
        -u TWILIO_API_KEY