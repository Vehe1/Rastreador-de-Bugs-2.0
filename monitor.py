import os
import time
import requests
import re
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_DISCOUNT_PERCENT = 50.0

LOJAS_ALVO = [
    "kabum", "terabyte", "pichau", "nike", "adidas", 
    "centauro", "netshoes", "aliexpress", "shein", "amazon", "mercado livre"
]

PALAVRAS_BUG = ["bug", "erro", "absurdo", "imperdível", "80%", "90%", "surreal", "corra", "despenca"]

# Canais públicos do Telegram que agregam as melhores promoções
CANAIS_TELEGRAM = [
    "pelando",
    "gatry_oficial",
    "promobit"
]

# Registo simples para não enviar a mesma promoção duas vezes na mesma hora
ITENS_ENVIADOS = set()

def notificar_telegram(titulo, link, origem, e_bug=False, desconto=0.0):
    assinatura = f"{titulo}-{origem}"
    if assinatura in ITENS_ENVIADOS:
        return
    
    if e_bug or desconto >= 80.0:
        header = "🚨🔥 *BUG / PROMOÇÃO EXTREMA DETETADA!* 🔥🚨"
        repeat_count = 3
    else:
        header = "⚡ *OFERTA FORTE ENCONTRADA* ⚡"
        repeat_count = 1

    msg = (
        f"{header}\n\n"
        f"🌐 *Origem:* {origem}\n"
        f"📦 *Item:* {titulo[:85]}...\n"
    )
    
    if desconto > 0:
        msg += f"💥 *Desconto:* *{desconto:.1f}% OFF*\n\n"
    else:
        msg += "\n"
        
    msg += f"🔗 [VER DETALHES]({link})"

    for i in range(repeat_count):
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            print(f"   -> [ALERTA {i+1}/{repeat_count}] {titulo[:40]}...")
            if repeat_count > 1:
                time.sleep(1.5)
        except Exception as e:
            print(f"Erro ao notificar o Telegram: {e}")
            
    ITENS_ENVIADOS.add(assinatura)

# =========================================================
# 1. API DIRETA (MERCADO LIVRE) - Query Corrigida
# =========================================================
def scan_mercadolivre_api():
    print("=== A INICIAR RASTREIO DIRETO (MERCADO LIVRE) ===")
    # Alterado para pesquisar itens específicos onde os descontos são declarados
    termos = ["hardware", "tênis", "smartphone"]
    max_disc = 0.0
    total_analisados = 0
    
    for termo in termos:
        url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}&limit=20"
        try:
            data = requests.get(url, timeout=10).json()
            results = data.get("results", [])
            total_analisados += len(results)
            
            for item in results:
                orig = item.get("original_price")
                curr = item.get("price")
                if orig and curr and orig > curr:
                    disc = ((orig - curr) / orig) * 100
                    if disc > max_disc: max_disc = disc
                    if disc >= MIN_DISCOUNT_PERCENT:
                        notificar_telegram(item.get("title", "Produto ML"), item.get("permalink", ""), "Mercado Livre", False, disc)
        except Exception as e:
            print(f"[MERCADO LIVRE] Erro na API para o termo {termo}: {e}")
            
    print(f"[MERCADO LIVRE] Analisados: {total_analisados} itens | Maior desconto: {max_disc:.1f}%")

# =========================================================
# 2. RASPAGEM DE CANAIS PÚBLICOS DO TELEGRAM (IMUNE AO CLOUDFLARE)
# =========================================================
def scan_telegram_channels():
    print("\n=== A INICIAR CAÇADOR DE BUGS (VIA TELEGRAM WEB) ===")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    for canal in CANAIS_TELEGRAM:
        print(f"\n[*] A varrer canal: @{canal}...")
        url = f"https://t.me/s/{canal}"
        try:
            resposta = requests.get(url, headers=headers, timeout=15)
            if resposta.status_code == 200:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                # A classe 'tgme_widget_message_text' contém o texto da mensagem no Telegram Web
                mensagens = soup.find_all('div', class_='tgme_widget_message_text')
                itens_analisados = 0
                
                # Inverte para ler as mais recentes primeiro
                for msg_html in reversed(mensagens[-15:]):
                    itens_analisados += 1
                    texto_msg = msg_html.get_text(separator=" ", strip=True)
                    texto_minusculo = texto_msg.lower()
                    
                    loja_encontrada = any(loja in texto_minusculo for loja in LOJAS_ALVO)
                    
                    if loja_encontrada:
                        e_bug = any(palavra in texto_minusculo for palavra in PALAVRAS_BUG)
                        
                        # Tenta encontrar o link na mensagem
                        link_tag = msg_html.find('a', href=True)
                        link_oferta = link_tag['href'] if link_tag else f"https://t.me/s/{canal}"
                        
                        # Limpa o texto para o título (pega apenas a primeira frase)
                        titulo = texto_msg.split('R$')[0].split('http')[0].strip()
                        if len(titulo) < 10:
                            titulo = texto_msg[:80]
                            
                        notificar_telegram(titulo, link_oferta, f"Telegram @{canal}", e_bug)
                        
                print(f"    -> {itens_analisados} mensagens recentes analisadas.")
            else:
                print(f"    -> Erro ao aceder ao Telegram (Status {resposta.status_code})")
        except Exception as e:
            print(f"    -> Falha ao processar canal @{canal}: {e}")

    print("\n=== VARREDURA TOTAL FINALIZADA ===")

if __name__ == "__main__":
    scan_mercadolivre_api()
    scan_telegram_channels()
