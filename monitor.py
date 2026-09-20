import os
import time
import requests
import xml.etree.ElementTree as ET

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# As lojas exatas que quer monitorizar
LOJAS_ALVO = [
    "kabum", "terabyte", "pichau", "nike", "adidas", 
    "centauro", "netshoes", "mercado livre", "mercadolivre", 
    "aliexpress", "shein", "amazon"
]

# Palavras que indicam um provável bug de preço ou promoção gigante
PALAVRAS_BUG = ["bug", "erro", "absurdo", "imperdível", "80%", "90%", "surreal", "grátis", "corra"]

FEEDS = [
    {"nome": "Hardmob Promoções", "url": "https://www.hardmob.com.br/external.php?type=RSS2&forumids=407"},
    {"nome": "Gatry", "url": "https://gatry.com/promocoes/rss"}
]

def notificar_telegram(titulo, link, origem, e_bug):
    if e_bug:
        header = "🚨🔥 *BUG / PROMOÇÃO EXTREMA DETETADA!* 🔥🚨"
        repeat_count = 3
    else:
        header = "⚡ *OFERTA ENCONTRADA NAS SUAS LOJAS* ⚡"
        repeat_count = 1

    msg = (
        f"{header}\n\n"
        f"🌐 *Origem do Alerta:* {origem}\n"
        f"📦 *Item:* {titulo}\n\n"
        f"🔗 [COMPRAR / VER DETALHES]({link})"
    )
    
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

def analisar_feeds():
    print("=== A INICIAR CAÇADOR DE BUGS (VIA AGREGADORES RSS) ===")
    
    for feed in FEEDS:
        print(f"\n[*] A varrer: {feed['nome']}...")
        try:
            # Usa um cabeçalho simples
            headers = {"User-Agent": "Mozilla/5.0"}
            resposta = requests.get(feed["url"], headers=headers, timeout=15)
            
            if resposta.status_code == 200:
                raiz = ET.fromstring(resposta.text)
                itens_analisados = 0
                
                # Procura por itens no formato RSS
                for item in raiz.findall(".//item"):
                    itens_analisados += 1
                    titulo_elemento = item.find("title")
                    link_elemento = item.find("link")
                    
                    if titulo_elemento is not None and link_elemento is not None:
                        titulo = titulo_elemento.text.strip()
                        link = link_elemento.text.strip()
                        titulo_minusculo = titulo.lower()
                        
                        # Verifica se o título contém alguma das suas lojas
                        loja_encontrada = any(loja in titulo_minusculo for loja in LOJAS_ALVO)
                        
                        if loja_encontrada:
                            # Verifica se o título sugere que é um bug/erro
                            e_bug = any(palavra in titulo_minusculo for palavra in PALAVRAS_BUG)
                            notificar_telegram(titulo, link, feed["nome"], e_bug)
                            
                print(f"    -> {itens_analisados} promoções recentes analisadas com sucesso.")
            else:
                print(f"    -> Erro ao aceder (Status {resposta.status_code})")
        except Exception as e:
            print(f"    -> Falha ao processar feed: {e}")

    print("\n=== VARREDURA FINALIZADA ===")

if __name__ == "__main__":
    analisar_feeds()
