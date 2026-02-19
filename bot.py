import telebot
import yt_dlp
import os
from flask import Flask
from threading import Thread

# Configuração para manter o bot acordado na nuvem
app = Flask('')
@app.route('/')
def home():
    return "O bot está funcionando!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# Configuração do Bot (Cole seu token na linha abaixo, entre as aspas)
TOKEN = '8405851563:AAFm492bdi0Pko4VcoPWvekn57vxUR5XSPo' 
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Envie o link de um vídeo (Shopee, etc) e eu vou tentar baixar para você. 🎥")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⏳ Processando o vídeo... Aguarde.")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{chat_id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, caption="Vídeo baixado com sucesso! ✅")
            
        os.remove(filename) # Apaga o arquivo da nuvem após enviar para não lotar o espaço
        bot.delete_message(chat_id, msg.message_id)
        
    except Exception as e:
        bot.edit_message_text("❌ Desculpe, não consegui baixar esse vídeo. Verifique se o link está correto ou se o site bloqueou o acesso.", chat_id, msg.message_id)

# Liga o sistema
keep_alive()
bot.polling(non_stop=True)
