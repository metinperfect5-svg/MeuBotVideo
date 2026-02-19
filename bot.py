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
TOKEN = '8405851563:AAFm492bdi0Pko4VcoPWvekn57vxUR5XSPo' # <--- NÃO ESQUEÇA DE COLOCAR SEU TOKEN AQUI
bot = telebot.TeleBot(TOKEN)

def get_driver():
    opcoes = Options()
    opcoes.add_argument("--headless")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--mute-audio")
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    servico = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=servico, options=opcoes)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Envie o link e eu baixo o vídeo. 🎥")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    chat_id = message.chat.id

    # --- PODER 1: TRUQUE DO INSTAGRAM ---
    if "instagram.com" in url:
        # Troca o link normal pelo link mágico
        novo_link = url.replace("instagram.com", "ddinstagram.com")
        
        texto = f"✨ **Magia do Instagram ativada!**\n\nO vídeo vai carregar logo abaixo desta mensagem. Quando ele aparecer, basta clicar nele, ir nos 3 pontinhos e salvar na galeria:\n\n👉 {novo_link}"
        
        bot.send_message(chat_id, texto, parse_mode="Markdown")
        return # Para a execução aqui, não precisa fazer mais nada!

    msg = bot.send_message(chat_id, "⏳ Processando seu link...")

    # --- PODER 2: CHROME INVISÍVEL PARA SHOPEE ---
    if "shopee" in url or "shp.ee" in url:
        navegador = None
        try:
            bot.edit_message_text("🕵️ Usando o disfarce para entrar na Shopee...", chat_id, msg.message_id)
            navegador = get_driver()
            navegador.get(url)
            
            video_element = WebDriverWait(navegador, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            video_url = video_element.get_attribute("src")
            
            if video_url:
                bot.edit_message_text("✅ Encontrei! Baixando...", chat_id, msg.message_id)
                video_data = requests.get(video_url)
                nome_arquivo = f"shopee_{chat_id}.mp4"
                
                with open(nome_arquivo, 'wb') as f:
                    f.write(video_data.content)
                
                with open(nome_arquivo, 'rb') as video_file:
                    bot.send_video(chat_id, video_file, caption="Aqui está! 🎥")
                
                os.remove(nome_arquivo)
                bot.delete_message(chat_id, msg.message_id)
            else:
                bot.edit_message_text("❌ Achei o player de vídeo, mas ele estava vazio.", chat_id, msg.message_id)
                
        except Exception as e:
            bot.edit_message_text("❌ A Shopee me bloqueou ou a internet demorou muito.", chat_id, msg.message_id)
        finally:
            if navegador: navegador.quit() 
        return

    # --- PODER 3: SISTEMA PADRÃO PARA O RESTO (YouTube, TikTok, etc) ---
    bot.edit_message_text("⏳ Baixando pelo sistema padrão...", chat_id, msg.message_id)
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
