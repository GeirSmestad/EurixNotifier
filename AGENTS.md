# AGENTS.md - Cursor Agent Instructions

This file provides context and guidelines for AI agents working on this codebase.

## Project Overview

- This application is a simple, timed job that checks whether a certain web site has information about ticket sales for a festival, and notifies users on SMS via the AWS SNS service if so.


## Tech Stack

- **Backend**: Python script, normally executed from a cron job, calling AWS SNS and OpenAI
- **Database**: SQLite (`data/eurix-monitor.db`)
- **Runtime/hosting**: Linux VPS (Lightsail). This app is set up via a script, bootstrap.sh. Note that the server has other tenant apps that we will not touch.
