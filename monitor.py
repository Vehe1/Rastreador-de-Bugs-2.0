import os
import time
import requests
import urllib.parse
import xml.etree.ElementTree as ET

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_DISCOUNT_PERCENT = 50.0

# As lojas exatas que quer monitorizar nos agregadores
LOJAS_ALVO = [
    "kabum", "terabyte", "pichau", "nike", "adidas", 
    "centauro", "netshoes", "mercado livre", "mercadolivre", 
    "aliexpress", "shein", "amazon"
]

# Palavras que indicam um provável bug de preço ou promoção gigante
PALAVRAS_BUG = ["bug", "erro", "absurdo", "imperdível", "80%", "90%", "surreal", "grátis", "corra", "despenca"]

FEEDS = [
    {"nome": "Hardmob Promoções", "url": "https://www.hardmob.com.br/external.php?type=RSS2&forumids=407"},
    {"nome": "Gatry", "url": "https://gatry.com/promocoes/rss"}
]

def notificar_telegram(titulo, link, origem, e_bug=False, desconto=0.0):
    if e_bug or desconto >= 80.0:
        header = "🚨🔥 *BUG / PROMOÇÃO EXTREMA DETETADA!* 🔥🚨"
        repeat_count = 3
    else:
        header = "⚡ *OFERTA FORTE ENCONTRADA* ⚡"
        repeat_count = 1

    msg = (
        f"{header}\n\n"
        f"🌐 *Origem:* {origem}\n"
        f"📦 *Item:* {titulo[:85]}\n"
    )
    
    if desconto > 0:
        msg += f"💥 *Desconto:* *{desconto:.1f}% OFF*\n\n"
    else:
        msg += "\n"
        
    msg += f"🔗 [COMPRAR / VER DETALHES]({link})"

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

# =========================================================
# 1. API DIRETA (MERCADO LIVRE) - Rápido e Infalível
# =========================================================
def scan_mercadolivre_api():
    print("=== A INICIAR RASTREIO DIRETO (MERCADO LIVRE) ===")
    url = "https://api.mercadolibre.com/sites/MLB/search?q=ofertas&limit=50"
    max_disc = 0.0
    try:
        data = requests.get(url, timeout=10).json()
        results = data.get("results", [])
        for item in results:
            orig = item.get("original_price")
            curr = item.get("price")
            if orig and curr and orig > curr:
                disc = ((orig - curr) / orig) * 100
                if disc > max_disc: max_disc = disc
                if disc >= MIN_DISCOUNT_PERCENT:
                    notificar_telegram(item.get("title", "Produto ML"), item.get("permalink", ""), "Mercado Livre", False, disc)
        print(f"[MERCADO LIVRE] Analisados: {len(results)} itens | Maior desconto: {max_disc:.1f}%")
    except Exception as e:
        print(f"[MERCADO LIVRE] Erro na API: {e}")

# =========================================================
# 2. CAÇADOR DE BUGS VIA AGREGADORES E PROXY ALLORIGINS
# =========================================================
def analisar_feeds():
    print("\n=== A INICIAR CAÇADOR DE BUGS (COMUNIDADES RSS) ===")
    
    for feed in FEEDS:
        print(f"\n[*] A varrer: {feed['nome']}...")
        try:
            # Codifica a URL para o Proxy AllOrigins não se perder nos carateres especiais
            url_codificada = urllib.parse.quote(feed["url"])
            proxy_url = f"https://api.allorigins.win/raw?url={url_codificada}"
            
            headers = {"User-Agent": "Mozilla/5.0"}
            resposta = requests.get(proxy_url, headers=headers, timeout=20)
            
            if resposta.status_code == 200:
                try:
                    raiz = ET.fromstring(resposta.text)
                    itens_analisados = 0
                    
                    for item in raiz.findall(".//item"):
                        itens_analisados += 1
                        
                        titulo_elemento = item.find("title")
                        link_elemento = item.find("link")
                        
                        if titulo_elemento is not None and link_elemento is not None:
                            titulo = titulo_elemento.text.strip()
                            link = link_elemento.text.strip()
                            titulo_minusculo = titulo.lower()
                            
                            # Verifica se o título contém alguma das lojas alvo
                            loja_encontrada = any(loja in titulo_minusculo for loja in LOJAS_ALVO)
                            
                            if loja_encontrada:
                                e_bug = any(palavra in titulo_minusculo for palavra in PALAVRAS_BUG)
                                notificar_telegram(titulo, link, feed["nome"], e_bug)
                                
                    print(f"    -> {itens_analisados} promoções recentes analisadas com sucesso.")
                except ET.ParseError:
                    print("    -> Erro ao analisar o texto (Pode estar em manutenção).")
            else:
                print(f"    -> Erro na rede do Proxy (Status {resposta.status_code})")
        except Exception as e:
            print(f"    -> Falha ao processar feed: {e}")

    print("\n=== VARREDURA TOTAL FINALIZADA ===")

if __name__ == "__main__":
    scan_mercadolivre_api()
    analisar_feeds()
