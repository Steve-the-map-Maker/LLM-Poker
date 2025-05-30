#!/bin/bash
export PYTHONPATH=/Users/lantzsteve/Documents/PokerRound5/backend:$PYTHONPATH
cd /Users/lantzsteve/Documents/PokerRound5/backend
uvicorn main:app --reload --port 8000
