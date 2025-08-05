import os
import csv
import requests
from flask import Flask, render_template, request, send_file
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

app = Flask(__name__)

CSV_FILE = 'outputs.csv'

def save_to_csv(platform, content):
    timestamp = datetime.now().isoformat()
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['platform', 'content', 'timestamp'])
        writer.writerow([platform, content, timestamp])

def call_openrouter(prompt, model="openrouter/auto"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

def generate_outputs(longform):
    outputs = {}
    # LinkedIn Post
    linkedin_prompt = f"Rewrite the following as a LinkedIn post with a hook and CTA:\n{longform}"
    linkedin = call_openrouter(linkedin_prompt)
    outputs['linkedin'] = linkedin
    save_to_csv('LinkedIn', linkedin)

    # Instagram Caption
    insta_prompt = f"Rewrite as an Instagram caption with emojis and 3 relevant hashtags:\n{longform}"
    instagram = call_openrouter(insta_prompt)
    outputs['instagram'] = instagram
    save_to_csv('Instagram', instagram)

    # Newsletter Email
    newsletter_prompt = f"Create a newsletter email with subject, preview text, and body from this:\n{longform}"
    newsletter = call_openrouter(newsletter_prompt)
    outputs['newsletter'] = newsletter
    save_to_csv('Newsletter', newsletter)

    # Blog Meta Description & H1
    blog_prompt = f"Generate a blog meta description and H1 title from this:\n{longform}"
    blog = call_openrouter(blog_prompt)
    outputs['blog'] = blog
    save_to_csv('Blog', blog)

    # Summary
    summary_prompt = f"Summarize this content in 2 lines:\n{longform}"
    summary = call_openrouter(summary_prompt)
    outputs['summary'] = summary
    save_to_csv('Summary', summary)

    # Word counts
    for key in list(outputs.keys()):
        outputs[f"{key}_count"] = len(outputs[key].split())

    return outputs

@app.route('/', methods=['GET', 'POST'])
def home():
    outputs = None
    longform = ''
    if request.method == 'POST':
        longform = request.form.get('longform', '')
        if longform.strip():
            outputs = generate_outputs(longform)
    return render_template('home.html', outputs=outputs, longform=longform)

@app.route('/download_csv')
def download_csv():
    return send_file(CSV_FILE, as_attachment=True)

@app.route('/clear_csv')
def clear_csv():
    open(CSV_FILE, 'w').close()
    return "CSV cleared!"

@app.route('/download_txt')
def download_txt():
    if not os.path.exists(CSV_FILE):
        return "No outputs yet!"
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    with open('outputs.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    return send_file('outputs.txt', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)