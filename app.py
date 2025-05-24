from flask import Flask, request, jsonify
from smolagents import OpenAIServerModel, ToolCallingAgent
from smolagents import Tool
import requests

app = Flask(__name__)

# Setup your model and agent here (same as your current code)
model = OpenAIServerModel(
    model_id="gemini-2.0-flash",
    api_base="https://generativelanguage.googleapis.com/v1beta",
    api_key="AIzaSyCIG1ZmPhDJktAmuzuSpajmivpaMeo5nDo",
)

class SearchWebTool(Tool):
    name = "moroccan_darija_web_search"
    description = "كيقلب فالمواقع المغربية على الوثائق اللي كيتطلبو فالإدارات بالدارجة المغربية."
    inputs = {
        "query": {
            "type": "string",
            "description": "شنو بغيتي تقلب عليه، مثلا: 'شنو خاصني نوجد لجواز السفر المغرب'"
        }
    }
    output_type = "string"

    def forward(self, query: str) -> str:
        try:
            api_key = "59987dee629e60fa56510999efde2faecac8beee73bcab5ad1fcea0b6d1244e8"
            response = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "hl": "ar",        # لغة الواجهة: العربية
                    "gl": "ma",        # البلد: المغرب
                    "engine": "google",
                    "api_key": api_key
                }
            )
            data = response.json()
            results = data.get("organic_results", [])[:3]
            if not results:
                return "ما لقيتش نتائج دابا، جرب تسول بطريقة أخرى."

            return "\n\n".join(f"{r['title']}\n{r['link']}" for r in results)
        except Exception as e:
            return f"خطأ فالبحث: {str(e)}"

agent = ToolCallingAgent(model=model, tools=[SearchWebTool()])

chat_history = []

def chat(user_input):
    global chat_history
    chat_history.append(f"User: {user_input}")
    conversation = "\n".join(chat_history) + "\nAssistant:"
    result = agent.run(conversation)
    chat_history.append(f"Assistant: {result}")

    return {
        "reply": result,
        "user_input": user_input,
        "chat_history": chat_history,
        "tool_used": agent.tools[0].name if isinstance(agent.tools, list) and len(agent.tools) > 0 else "none",
        "raw_prompt": conversation
    }


@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.json
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    reply = chat(user_message)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
