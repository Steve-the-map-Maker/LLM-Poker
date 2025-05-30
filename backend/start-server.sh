#!/bin/bash
# Simple script to start the LLM Poker FastAPI server

cd /Users/lantzsteve/Documents/PokerRound5/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
