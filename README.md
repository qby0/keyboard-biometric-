# Keyboard Biometric Authentication System

A machine learning-based security system that authenticates users based on their keystroke dynamics.

## Overview

This project implements behavioral biometrics to identify users by analyzing their typing patterns (flight time, dwell time, and rhythm). It serves as an additional security layer alongside traditional passwords.

## Features

- **Data Collection**: Modules to capture precise keystroke timings
- **Feature Extraction**: Calculation of dwell time (key press to release) and flight time (release to next press)
- **ML Models**: Implementation of Random Forest and SVM classifiers for user identification
- **Real-time Verification**: Interface for testing authentication in real-time

## Tech Stack

- Python (scikit-learn, pandas, numpy)
- PyHook for event capturing
- Data visualization with Matplotlib

## Installation

```bash
pip install -r requirements.txt
python main.py
```
