import telebot
import yt_dlp
import os
import requests
import re
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

# --- COLOQUE SEU TOKEN DO TELEGRAM AQUI ---
TOKEN = '8405851563:AAFm492bdi0Pko4VcoPWvekn57vxUR5XSPo'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Envie o link de um vídeo (Shopee, etc) e eu vou tentar baixar para você. 🎥")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⏳ Analisando o link...")

    # --- HABILIDADE NOVA: DETETIVE DE SHOPEE ---
    # Se a palavra 'shopee' ou 'shp.ee' estiver no link, ele usa o modo detetive
    if "shopee" in url or "shp.ee" in url:
        try:
            bot.edit_message_text("🕵️ Procurando o vídeo escondido na Shopee...", chat_id, msg.message_id)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            # O bot entra no site
            site = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            
            # Procura no código fonte qualquer link que termine em .mp4
            links_brutos = re.findall(r'(https?[^\s"\'<>]+?\.mp4[^\s"\'<>]*)', site.text)
            
            if links_brutos:
                # Limpa o link e prepara o download
                mp4_url = links_brutos[0].replace('\\/', '/')
                bot.edit_message_text("✅ Encontrei o arquivo bruto! Baixando...", chat_id, msg.message_id)
                
                # Baixa o vídeo direto do servidor da Shopee
                video_data = requests.get(mp4_url, headers=headers)
                nome_arquivo = f"shopee_{chat_id}.mp4"
                
                with open(nome_arquivo, 'wb') as f:
                    f.write(video_data.content)
                
                # Envia para o Telegram
                with open(nome_arquivo, 'rb') as video_file:
                    bot.send_video(chat_id, video_file, caption="Aqui está o seu vídeo da Shopee! 🎥")
                
                os.remove(nome_arquivo)
                bot.delete_message(chat_id, msg.message_id)
                return # Termina a função com sucesso e não precisa usar o yt-dlp
                
        except Exception as e:
            print("Modo detetive falhou:", e)
            # Se o modo detetive falhar, ele segue a vida e tenta o yt-dlp abaixo

    # --- MODO PADRÃO (yt-dlp) PARA YOUTUBE, TIKTOK, ETC ---
    bot.edit_message_text("⏳ Processando pelo sistema padrão...", chat_id, msg.message_id)
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'video_{chat_id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, caption="Vídeo baixado com sucesso! ✅")
            
        os.remove(filename)
        bot.delete_message(chat_id, msg.message_id)
        
    except Exception as e:
        erro_msg = str(e)
        if "Unsupported URL" in erro_msg:
            bot.edit_message_text("❌ A Shopee escondeu muito bem esse vídeo. Meu sistema de detetive não conseguiu achá-lo no código da página.", chat_id, msg.message_id)
        else:
            bot.edit_message_text("❌ Erro ao baixar o vídeo. Tente novamente mais tarde.", chat_id, msg.message_id)
