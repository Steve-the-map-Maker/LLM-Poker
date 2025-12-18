# LLM Poker Arena

A Texas Hold'em poker platform where human players can compete against advanced AI agents powered by Large Language Models (LLMs), or spectate matches between different AI personalities.

## Overview

LLM Poker Arena is a modern web application that bridges the gap between traditional poker mechanics and cutting-edge generative AI. By leveraging the **PokerKit** library for robust game logic and integrating with **OpenAI (GPT-4/3.5)** and **Google Gemini**, this project allows for dynamic, personality-driven poker gameplay.

## Features

-   **Human vs. AI**: Challenge various AI personalities, ranging from the bluff-heavy "CosmicAce" to the conservative "GeminiPro".
-   **AI vs. AI Spectation**: Watch different LLMs battle it out and analyze their strategies in real-time.
-   **Interactive UI**: A sleek, dark-mode web interface built with React, featuring real-time game updates and chat logs where AIs "talk" about their hands.
-   **Robust Game Engine**: Powered by [PokerKit](https://github.com/uoftcprg/pokerkit) for mathematically accurate Texas Hold'em rules.
-   **Chat & Personality**: AI agents don't just play cards; they engage in table talk, explaining their reasoning (or lying about it!) based on their assigned personas.

## Technology Stack

-   **Frontend**: React, TypeScript, Modern CSS (Glassmorphism design)
-   **Backend**: Python, FastAPI, PokerKit
-   **AI Integration**: OpenAI API, Google Gemini API

## Getting Started

### Prerequisites

-   Time and motivation to play or watch poker!
-   A modern web browser.

### Interactive Demo

*Coming Soon!*

## Local Development

For the fastest way to get started, see the **[QUICKSTART.md](./QUICKSTART.md)** guide.

If you wish to run this project manually:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Steve-the-map-Maker/LLM-Poker.git
    cd LLM-Poker
    ```

2.  **Backend Setup**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *Create a `.env` file in `backend/` with your API keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`).*

3.  **Frontend Setup**:
    ```bash
    cd ../frontend
    npm install
    npm start
    ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
