# Eurix Notifier

This is v1 of this app; the repository is empty. We will build the first version of the app from this specification.

## Purpose

This application is a simple, timed job that checks whether https://felixruckert.de/2015/10/01/eurix/ has information about ticket sales for a festival, and notifies users on SMS via the AWS SNS service if so.

The implementation should be pragmatic and easily maintainable.

## Architecture

- The app runs on AWS Lightsail, using bootstrap.sh to set up all required server infrastructure on the running instance
- The whole app is stored in /srv/eurixnotifier
- A Python script that fetches the correct URL, wraps the HTML with an LLM prompt and sends it to OpenAI, receiving JSON in return. Based on the JSON, it will log the attempt to the database and maybe notify users via SMS through AWS SNS.
- A cron job runs this Python script, but it may also be run manually, for testing and verification
- We have an OpenAI account for OpenAI queries
- We have an AWS SNS topic, and will use the SMS sandbox only. Numbers to notify are defined in AWS.

## bootstrap.sh

This shell script should perform all actions required to prepare the server for running the app. Keep in mind that there are other apps running on the server, and we will make reasonable efforts not to touch them.

You can ssh the server with 'ssh bergenomap'; there is a key set up from this machine.

## Justfile

We will use Just as the build system. Actions:

- deploy: copy all required files to the server and run any shell commands required
- force-notify: perform a run with forced notification
- status: returns top 10 most recent rows of the DB, excluding web_html

## Python script details

- Allow a parameter for forcing SMS notification, regardless of should_notify
- No dedupe behavior, for now. Might update this later.
- SMS contents:
    - Preface the SMS with "Dette er en melding fra Eurix-bot 🦾\n\n"
    - Insert sms_content from prompt result here
    - Suffix the SMS with "\n\nDu mottar disse meldingene fordi Geir vil holde deg informert, men si ifra til ham hvis du ikke vil ha dem lenger 😘"

## Cron job details

- The script should run daily, at 11:45 AM
- Every Wednesday, the script should be run with forced notification

## OpenAI prompt

We will use the model gpt-5.2, via API.

```
Read the HTML below and determine the following: 

1) What dates and editions for this event are available for registration? 
2) What *future* dates and editions does the page inform about?

It is <insert_current_date> today.

The page describes which editions of the festival are currently open for registration, as well as information about previous festivals. (We are not interested in the previous festivals, and we are also not interested in any *2026* festival).

You are responsible for deciding whether to notify the user about festival availability. Notify if this web page has information about any *2027* edition of this festival. It is normally arranged in spring and autumn.

The user will want to know if *information is available* for a 2027 festival, and also if *registration has been opened* for a 2027 festival.

Regardless of whether you notify or not, you must compose a brief SMS explaining the current situation to the user, focusing on the 2027 edition. The SMS must be in Norwegian.

Return only JSON, as per the following example:

{
    "sms_content": "Insert your SMS content here",
    "should_notify": true
}

Here is the HTML that you will analyze:

<insert_html_here>
```

## Data model

SQLite table "eurix_monitoring", with columns

- id, primary key, ascending
- checked_at, timestamp
- web_html, string
- sms_content, string
- should_notify, bool
- force_notify, bool
- notified_at, timestamp, will most often be null