# Milestone 3: Modern Conversational IVR UI

This milestone introduces a modern, responsive UI for the IRCTC IVR simulator, featuring conversational AI elements and enhanced user interaction.

## Features

- **Modern UI Design**: Clean, neumorphic design with cards, gradients, and animations.
- **Conversational Interface**: Chat-based interaction with typing indicators and message bubbles.
- **DTMF Keypad**: Interactive keypad for traditional IVR input.
- **Quick Actions**: Predefined buttons for common queries (booking, PNR, tracking).
- **Debug Panel**: Real-time inspection of session state, intents, and entities.
- **Web Speech API Integration**: Support for voice input (Chrome/Edge recommended).

## Setup

1. Ensure the backend from Milestone 2 is running:
   ```bash
   uvicorn main:app --reload
   ```

2. Open `irctc_m3.html` in a browser.

## Interaction Modes

- **Conversation**: Use natural language or quick action buttons.
- **DTMF Pad**: Switch to keypad mode for digit-based input.

## Files

- `irctc_m3.html`: Complete frontend application with embedded logic.

## Notes

- Frontend-only simulator; connects to Milestone 2 backend.
- Optimized for modern browsers with Web Speech API support.