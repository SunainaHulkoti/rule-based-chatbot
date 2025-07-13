from flask import Flask, render_template, request, jsonify
import json
import requests
from rapidfuzz import fuzz, process

app = Flask(__name__)

# Load data from the JSON file
def load_data():
    try:
        with open("qa_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist
    except json.JSONDecodeError:
        return []  # Return an empty list if the JSON is malformed

data = load_data()

# Preprocess text for better matching
def preprocess_text(text):
    return ' '.join(text.lower().strip().split())

# Find the best matching answer
def find_answer(user_query):
    user_query = preprocess_text(user_query)  # Preprocess the user query
    all_questions = []
    question_to_answers = {}

    # Extract questions and answers from the JSON data
    for topic in data:
        for question in topic["questions"]:
            processed_question = preprocess_text(question)
            all_questions.append(processed_question)
            question_to_answers[processed_question] = topic["answers"]

    # Find the best match using RapidFuzz
    result = process.extractOne(user_query, all_questions, scorer=fuzz.token_set_ratio)
    if result:
        best_match, score, _ = result  # Unpack the match and score (ignore index)
        if score > 80:  # Set a matching threshold
            return question_to_answers[best_match][0]  # Return the first answer

    return None  # No match found

# Query DuckDuckGo API
def query_duckduckgo(user_query):
    url = "https://api.duckduckgo.com/"
    params = {
        "q": user_query,
        "format": "json",
        "no_html": 1
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            # Check if there's an abstract (main answer) available
            if data.get("AbstractText"):
                return data["AbstractText"]
            elif data.get("RelatedTopics"):
                # Fallback to related topics if abstract is not available
                return data["RelatedTopics"][0]["Text"] if data["RelatedTopics"] else None
        return None
    except Exception:
        return None  # Handle errors gracefully

# Route for rendering the index page
@app.route("/")
def index():
    return render_template("index.html")

# Route for handling POST requests with user queries
@app.route("/api", methods=["POST"])
def api():
    user_query = request.json.get("message")
    if not user_query:
        return jsonify({"answer": "Invalid input. Please provide a valid question."}), 400

    # First, try finding an answer in the JSON
    answer = find_answer(user_query)

    # If no answer is found, try querying DuckDuckGo
    if not answer:
        answer = query_duckduckgo(user_query)

    # Final fallback
    if not answer:
        answer = "I'm sorry, I couldn't find an answer to your question."

    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
