import os
import openai
import gradio as gr
import pytesseract
from PIL import Image
import random

openai.api_key = os.getenv("OPENAI_API_KEY")

# -- OCR + Auto-fill --
def extract_and_fill(img):
    try:
        text = pytesseract.image_to_string(img)
        return text, text
    except Exception as e:
        return f"❌ Error: {e}", ""

# -- Solver --
def solve_question(q, mode):
    if not q:
        return "⚠️ Please enter a question.", ""
    prompt = {
        "💡 Hint": f"Give a helpful hint. Question: {q}",
        "🔄 Steps": f"Explain step-by-step. Question: {q}",
        "✅ Final": f"Explain and give the final answer. Question: {q}"
    }.get(mode, q)
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        full = res.choices[0].message.content.strip()
        final = full.split("Final Answer:")[-1].strip() if "Final Answer:" in full else ""
        return full, final
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

# -- Game Mode --
def generate_game_question(grade):
    prompt = f"Create a {grade} math question with 1 correct and 3 incorrect answers. Format: Question: ... A: ... B: ... C: ... D: ... Correct: ..."
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        text = res.choices[0].message.content.strip()
        lines = text.splitlines()
        question = [l for l in lines if l.startswith("Question:")][0][9:].strip()
        choices = {l.split(":")[0]: l.split(":")[1].strip() for l in lines if l[:1] in "ABCD"}
        correct = [l for l in lines if l.startswith("Correct:")][0].split(":")[1].strip()
        correct_full = f"{correct}: {choices[correct]}"
        shuffled = [f"{k}: {v}" for k, v in random.sample(list(choices.items()), len(choices))]
        return question, gr.update(choices=shuffled), correct_full
    except Exception as e:
        return "❌ Error generating question.", gr.update(choices=[]), ""

def check_answer(selected, correct):
    if not selected:
        return "❓ Choose an answer."
    return "✅ Correct!" if selected == correct else "❌ Try again."

# -- Smart Tutor --
def smart_tutor(q, attempt, mode, concept, grade):
    if not q:
        return "⚠️ Please enter a question."
    prompts = {
        "💡 Just a Hint": f"Give a hint for this {grade} level question: {q}",
        "✅ Check My Work": f"My attempt: {attempt}. Question: {q}. Feedback?",
        "🧭 Walk Me Through It": f"Guide me through this {grade} level question: {q}",
        "🔁 Try a Similar Problem": f"Create a similar problem to: {q}",
        "📘 Explain the Concept": f"Explain the concept of '{concept}' for {grade} level."
    }
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompts[mode]}]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"

# -- AI Lab --
def ai_lab(text, mode):
    if not text:
        return "⚠️ Enter content"
    prompts = {
        "🔍 Predict Difficulty": f"How hard is this? {text}",
        "🧠 Classify Topic": f"What topic is this? {text}",
        "🧪 Create Practice Set": f"Make 3 problems for: {text}",
        "🧠 Explain Confusion Point": f"Why is this confusing: {text}",
        "🎯 Make Similar Questions": f"Make 2 similar questions: {text}",
        "🎓 Estimate Grade Level": f"What grade is this? {text}",
        "🔢 Predict Step Count": f"How many steps to solve this? {text}",
        "🧩 Extract Keywords": f"List math keywords in: {text}",
        "🚫 Common Mistakes": f"What mistakes are made with: {text}"
    }
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompts[mode]}]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"

# -- Settings --
settings = {"theme": "default", "grade": "7th Grade", "skills": []}

def save_settings(theme, grade, skills):
    settings["theme"] = theme
    settings["grade"] = grade
    settings["skills"] = skills.split(",")
    return f"✅ Settings saved: {settings}"

# -- UI --
with gr.Blocks() as app:
    with gr.Tab("💭 Solver + Image Upload"):
        img = gr.Image(label="📸 Upload Image", type="pil", sources=["upload"])
        img_text = gr.Textbox(label="🔍 OCR Extracted", visible=False)
        question = gr.Textbox(label="✍️ Your Question")
        mode = gr.Radio(["💡 Hint", "🔄 Steps", "✅ Final"], label="Mode")
        response = gr.Textbox(label="🤖 AI Response")
        final = gr.Textbox(label="✅ Final Answer")
        img.change(extract_and_fill, img, [img_text, question])
        gr.Button("💭 Think For Me").click(solve_question, [question, mode], [response, final])
        gr.Button("🧹 Clear").click(lambda: ("", "", "", ""), None, [question, response, final, img_text])

    with gr.Tab("🎮 Game"):
        grade = gr.Dropdown(["3rd Grade", "4th Grade", "5th Grade", "6th Grade", "7th Grade"], label="Grade", value="7th Grade")
        gq = gr.Textbox(label="Question")
        gchoices = gr.Radio(label="Choices", choices=[])
        gcorrect = gr.Textbox(visible=False)
        feedback = gr.Textbox(label="Feedback")
        gr.Button("🎲 New Question").click(generate_game_question, [grade], [gq, gchoices, gcorrect])
        gr.Button("✅ Submit").click(check_answer, [gchoices, gcorrect], feedback)
        gr.Button("🧹 Clear").click(lambda: ("", [], ""), None, [gq, gchoices, gcorrect])

    with gr.Tab("📘 Smart Tutor"):
        sq = gr.Textbox(label="Question")
        satt = gr.Textbox(label="What did you try?")
        smode = gr.Radio(["💡 Just a Hint", "✅ Check My Work", "🧭 Walk Me Through It", "🔁 Try a Similar Problem", "📘 Explain the Concept"], label="Mode")
        sconcept = gr.Textbox(label="Concept")
        sgrade = gr.Dropdown(["3rd Grade", "4th Grade", "5th Grade", "6th Grade", "7th Grade"], label="Grade", value="7th Grade")
        sres = gr.Textbox(label="Tutor Response")
        gr.Button("🧠 Tutor Me").click(smart_tutor, [sq, satt, smode, sconcept, sgrade], sres)
        gr.Button("🧹 Clear").click(lambda: ("", "", None, "", "", ""), None, [sq, satt, smode, sconcept, sgrade, sres])

    with gr.Tab("🧪 AI Lab"):
        lq = gr.Textbox(label="Input")
        lmode = gr.Radio(["🔍 Predict Difficulty", "🧠 Classify Topic", "🧪 Create Practice Set", "🧠 Explain Confusion Point", "🎯 Make Similar Questions", "🎓 Estimate Grade Level", "🔢 Predict Step Count", "🧩 Extract Keywords", "🚫 Common Mistakes"], label="Tool")
        lres = gr.Textbox(label="AI Output")
        gr.Button("Run AI Tool").click(ai_lab, [lq, lmode], lres)
        gr.Button("🧹 Clear").click(lambda: ("", None, ""), None, [lq, lmode, lres])

    with gr.Tab("⚙️ Settings"):
        theme = gr.Radio(["default", "soft", "compact"], label="Theme")
        default_grade = gr.Dropdown(["3rd Grade", "4th Grade", "5th Grade", "6th Grade", "7th Grade"], label="Default Grade")
        skills = gr.Textbox(label="Math Skills (comma separated)")
        saved = gr.Textbox(label="Saved Settings")
        gr.Button("💾 Save Settings").click(save_settings, [theme, default_grade, skills], saved)
        gr.Button("🧹 Clear").click(lambda: (None, None, ""), None, [theme, default_grade, skills])

app.launch()
