# NLP Emotion Detection Application

This project implements an emotion detection web application using Flask.
It includes:

- an `EmotionDetection` package with an `emotion_detector` function
- unit tests for dominant emotion detection
- a simple web interface for running emotion analysis
- error handling for blank text input

## Project Structure

```text
.
|-- EmotionDetection/
|   |-- __init__.py
|   `-- emotion_detection.py
|-- static/
|   `-- mywebscript.js
|-- templates/
|   `-- index.html
|-- server.py
`-- test_emotion_detection.py
```

## Run Locally

1. Install dependencies:

```bash
pip install flask requests
```

2. Start the Flask server:

```bash
python3 server.py
```

3. Open `http://127.0.0.1:5000` in your browser.

## Run Unit Tests

```bash
python3 -m unittest test_emotion_detection.py
```

## Run Static Analysis

```bash
pylint server.py
```
