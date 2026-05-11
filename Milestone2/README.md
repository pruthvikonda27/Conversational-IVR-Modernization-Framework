# Milestone 2: IRCTC IVR Backend and Basic UI

This milestone implements the core FastAPI backend for the IRCTC IVR system and a basic HTML UI for interaction.

## Features

- **FastAPI Backend**: Endpoints for IVR start, input handling, PNR status, booking, Tatkal, and train tracking.
- **Basic UI**: Simple HTML interface with chat simulation, PNR input, and DTMF keypad.
- **Session Management**: Handles IVR sessions with state tracking.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```

3. Open `ui.html` in a browser to interact with the IVR simulator.

## Endpoints

- `POST /ivr/start`: Initialize IVR session
- `POST /ivr/input`: Handle DTMF input
- `POST /ivr/pnr`: Check PNR status
- `POST /ivr/booking`: Perform ticket booking
- `POST /ivr/tatkal`: Tatkal booking
- `POST /ivr/tracking`: Train tracking

## Files

- `backend.py`: FastAPI application
- `ui.html`: Frontend interface
- `requirements.txt`: Python dependencies