import telebot
import yt_dlp
import os
import requests
from flask import Flask
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Bot vivo!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT ---
TOKEN = '8405851563:AAFm492bdi0Pko4VcoPWvekn57vxUR5XSPo' # <--- COLE SEU TOKEN AQUI
bot = telebot.TeleBot(TOKEN)

# Função para criar o Chrome Invisível
def get_driver():
    opcoes = Options()
    opcoes.add_argument("--headless") # Roda invisível
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--mute-audio")
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=opcoes)
    return navegador

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Envie o link e eu baixo o vídeo. 🎥")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⏳ Vestindo meu disfarce e abrindo o Chrome invisível... (Pode demorar uns 20 segundos)")

    # --- SE FOR SHOPEE, USA O CHROME INVISÍVEL ---
    if "shopee" in url or "shp.ee" in url:
        navegador = None
        try:
            navegador = get_driver()
            navegador.get(url)
            
            bot.edit_message_text("🕵️ Esperando a página carregar igual a um humano...", chat_id, msg.message_id)
            
            # O bot vai esperar até 15 segundos para o player de vídeo aparecer na tela
            video_element = WebDriverWait(navegador, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            # Pega o arquivo cru (.mp4) de dentro do player
            video_url = video_element.get_attribute("src")
            
            if video_url:
                bot.edit_message_text("✅ Encontrei o vídeo! Baixando...", chat_id, msg.message_id)
                
                # Faz o download
                video_data = requests.get(video_url)
                nome_arquivo = f"shopee_{chat_id}.mp4"
                
                with open(nome_arquivo, 'wb') as f:
                    f.write(video_data.content)
                
                # Envia para você
                with open(nome_arquivo, 'rb') as video_file:
                    bot.send_video(chat_id, video_file, caption="Missão cumprida! 🎥")
                
                os.remove(nome_arquivo)
                bot.delete_message(chat_id, msg.message_id)
            else:
                bot.edit_message_text("❌ Achei o player de vídeo, mas ele estava vazio.", chat_id, msg.message_id)
                
        except Exception as e:
            bot.edit_message_text("❌ A Shopee me bloqueou ou a internet demorou muito para carregar a página.", chat_id, msg.message_id)
            print("Erro no Selenium:", e)
        finally:
            # Muito importante fechar o Chrome invisível no final
            if navegador:
                navegador.quit() 
        return

    # --- SE FOR OUTROS SITES (YouTube, TikTok), USA O SISTEMA PADRÃO ---
    bot.edit_message_text("⏳ Processando pelo sistema padrão...", chat_id, msg.message_id)
    ydl_opts = {'format': 'best', 'outtmpl': f'video_{chat_id}.%(ext)s', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        with open(filename, 'rb') as video:
            bot.send_video(chat_id, video, caption="Vídeo baixado com sucesso! ✅")
        os.remove(filename)
        bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Erro: {str(e)}", chat_id, msg.message_id)

keep_alive()
bot.polling(non_stop=True)
