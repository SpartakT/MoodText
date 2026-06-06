import os
from flask import Flask, render_template, request, jsonify
from langdetect import detect, LangDetectException
from langdetect.lang_detect_exception import ErrorCode
import langdetect
from transformers import pipeline


langdetect.DetectorFactory.seed = 0

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "multilingual-sentiment-analysis"
)


classifier = pipeline(
    task="text-classification",
    model=MODEL_PATH,
    tokenizer=MODEL_PATH,
    top_k=None,
    truncation=True,
    max_length=512,
    device=-1  # CPU
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_sentiment():

    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({
            'status': 'error',
            'message': 'No text provided'
        }), 400

    text = data['text'].strip()

    if not text:
        return jsonify({
            'status': 'error',
            'message': 'Empty text provided'
        }), 400

    try:

        if len(text) < 10:
            language = 'short-text'
        else:
            sample = text[:200]
            language = detect(sample)

    except LangDetectException as e:

        if hasattr(e, 'code') and e.code == ErrorCode.CantDetectLanguage:
            language = 'undetermined'
        else:
            language = 'error'

    try:

        api_results = classifier(text)

        results = api_results[0]

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        top_result = results[0]

        return jsonify({
            'status': 'success',
            'warnings': [],
            'label': top_result['label'],
            'score': round(top_result['score'], 4),
            'all_results': results,
            'language': language
        })

    except Exception as e:

        return jsonify({
            'status': 'error',
            'message': f'An error occurred during analysis: {str(e)}'
        }), 500

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )