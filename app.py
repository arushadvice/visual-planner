from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import openai
import re

load_dotenv()

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv('OPENAI_API_KEY')

def parse_script(script):
    """Break script into lines/sentences"""
    lines = re.split(r'(?<=[.!?])\s+|(?<=\n)\s*', script.strip())
    lines = [line.strip() for line in lines if line.strip()]
    return lines

def get_visual_suggestions(script_lines):
    """Get AI suggestions for each line"""
    suggestions = []
    
    for line in script_lines:
        if not line:
            continue;
            
        prompt = f"""For this video script line, provide visual suggestions in exact JSON format:

Line: \"{line}\"

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "visual": "specific visual description (e.g., person running, dark room, crowd cheering)",
    "source": "free source with search keyword (e.g., Pexels — search 'person running')",
    "mood": "2-3 mood descriptors separated by ' + ' (e.g., Energetic + Hopeful)"
}}

Be concise and direct. The visual description should be 5-10 words maximum."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a visual production assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            response_text = response['choices'][0]['message']['content'].strip()
            
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            suggestion = eval(response_text)
            suggestion['text'] = line
            suggestions.append(suggestion)
            
        except Exception as e:
            print(f"Error processing line: {e}")
            suggestions.append({
                'text': line,
                'visual': 'Visual element',
                'source': 'Search relevant stock footage',
                'mood': 'Dynamic'
            })
    
    return suggestions

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        script = data.get('script', '').strip()
        
        if not script:
            return jsonify({'error': 'No script provided'}), 400
        
        lines = parse_script(script)
        
        if not lines:
            return jsonify({'error': 'Could not parse script'}), 400
        
        suggestions = get_visual_suggestions(lines)
        
        return jsonify({
            'lines': suggestions,
            'total_lines': len(suggestions)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)