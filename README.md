# Voice Waitress

Take food orders over the phone using AI!

> This project was created for the 2025 Google Cloud Run Hackathon

## Project Architecture

This project uses FastAPI, Python, Twilio, Google ADK, Gemini, Docker, Cloud Run, and a few more technologies.

Twilio takes phone calls and handles them by sending audio to the backend FastAPI server over a websocket connection. The backend API sends the audio data to Gemini through Google ADK which is configured for live bidirectional streaming, allowing the AI model to respond in real time.

## Running the Project

This project requires [`uv`](https://docs.astral.sh/uv/), the Python package and project manager, to run properly. Once you have it installed, run `uv sync` in the project root to create a virtual environment and install required dependencies.

Make sure you have the required environment variables configured in `.env`. You can copy the template from `.env.example`.

To run the API locally, run `poe api-run`. Make sure the virtual environment is created and active in your terminal.

In order to hit your local API from Twilio, you should also install [`ngrok`](https://ngrok.com/). This will give you a public URL you can use to hit your local API. Run `ngrok http 8000` and it will give you a URL.

In Twilio, under `# Phone Numbers > Manage > Active Numbers > <your number>`, under `Configure with`, select `Webhook, TwiML Bin, Function, Studio Flow, Proxy Service`. Under `A call comes in`, select `Webhook`. Under URL, put `https://<ngrok url>/twilio/connect`. Under HTTP, select `POST`. Save your changes. Now, any phone calls to that number will be handled by your locally running API!

## Deployment

This project uses Docker to build an image which is deployed to Google Cloud Run. This is automatically done any time changes are committed and pushed to the main branch.

## Roadmap

Currently, the agent functionality is limited. I need to add additional tools, experiment with prompts, evaluate performance, and setup guardrails.

Additional tools like POS integration, ability to transfer calls, live inventory integration would post significant improvements to the overall quality of the agent.
