import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
# Render automatically provides this environment variable for your app's URL
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') 

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("BOT_TOKEN or HF_TOKEN is missing in environment variables!")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client pointing to Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Handle incoming Telegram messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    user_text = message.text
    
    # Show "typing..." status in Telegram while waiting for the AI
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Call the Hugging Face Model
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_text},
            ],
            stream=False # Keep false for Telegram to avoid message edit rate-limits
        )
        
        # Extract the AI's response and send it back to the user
        ai_reply = response.choices[0].message.content
        bot.reply_to(message, ai_reply)
        
    except Exception as e:
        bot.reply_to(message, f"Sorry, an error occurred: {str(e)}")

# 5. Flask Webhook Routes
@app.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    # Telegram sends updates to this route
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook_setup():
    # Visit your Render URL to set up the webhook automatically
    bot.remove_webhook()
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
        return f"Webhook successfully set to {RENDER_URL}", 200
    else:
        return "Bot is running, but RENDER_EXTERNAL_URL is not set.", 200

if __name__ == "__main__":
    # Render assigns a dynamic port, default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
