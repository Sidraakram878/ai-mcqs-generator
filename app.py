from flask import Flask, request, jsonify, render_template
from google import genai
import os
import fitz  # PyMuPDF for PDF
import docx  # python-docx for DOCX

app = Flask(__name__)

API_KEY = "AIzaSyCEOkdtHwcAPCwlPIefI6q2YVrgr2SGMLE "
client = genai.Client(api_key=API_KEY)

app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs("uploads", exist_ok=True)

# ---------- TEXT EXTRACTION FUNCTIONS ----------
def extract_text_from_pdf(path):
    text = ""
    pdf = fitz.open(path)
    for page in pdf:
        text += page.get_text()
    return text

def extract_text_from_docx(path):
    doc = docx.Document(path)
    full = [p.text for p in doc.paragraphs]
    return "\n".join(full)

# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    count = int(request.form.get("count", 10))

    if "file" not in request.files:
        return jsonify({"reply": "No file uploaded!"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"reply": "Empty file name!"})

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Detect file type
    ext = file.filename.lower().split(".")[-1]

    if ext == "pdf":
        extracted_text = extract_text_from_pdf(filepath)

    elif ext in ["docx", "doc"]:
        extracted_text = extract_text_from_docx(filepath)

    else:
        return jsonify({"reply": "Only PDF and DOCX files are supported (no images)"})

    if not extracted_text.strip():
        return jsonify({"reply": "Could not extract text from file!"})

    # ---------- MCQ'S Generation ----------
    mcq_prompt = f"""
    Generate {count} multiple-choice questions (4 options: A, B, C, D) from this text.
    Provide the correct answer for each question.
    Format it cleanly:

    Q1: Question text
    A. Option 1
    B. Option 2
    C. Option 3
    D. Option 4
    Answer: C

    Text:
    {extracted_text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=mcq_prompt
        )
        reply = response.text
    except Exception as e:
        reply = f"Error generating MCQs: {str(e)}"

    return jsonify({"reply": reply})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_text = data.get("text", "").strip()
    count = int(data.get("count", 10))

    if not user_text:
        return jsonify({"reply": "Please paste some text!"})

    prompt = f"""
    Generate {count} multiple-choice questions (4 options: A, B, C, D) from this text.
    Provide the correct answer for each question.
    Format it cleanly:

    Q1: Question text
    A. Option 1
    B. Option 2 
    C. Option 3
    D. Option 4
    Answer: B

    Text:
    {user_text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        reply = response.text
    except Exception as e:
        reply = f"Error generating MCQs: {str(e)}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)


