import os
import time
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ALVOS_SNIPER = [
    # --- Smartphones ---
    {"termo": "iPhone 15", "preco_min": 800.0, "preco_max": 3800.0},
    {"termo": "iPhone 14", "preco_min": 800.0, "preco_max": 2800.0},
    {"termo": "iPhone 13", "preco_min": 800.0, "preco_max": 2200.0},
    {"termo": "Galaxy S26", "preco_min": 1000.0, "preco_max": 4000.0},
    {"termo": "Galaxy S25", "preco_min": 1000.0, "preco_max": 3500.0},
    {"termo": "Galaxy S24", "preco_min": 1000.0, "preco_max": 2800.0},
    
    # --- Consoles ---
    {"termo": "Playstation 5", "preco_min": 300.0, "preco_max": 2800.0},
    {"termo": "PS5", "preco_min": 300.0, "preco_max": 2800.0},
    {"termo": "Xbox Series X", "preco_min": 300.0, "preco_max": 2900.0},
    {"termo": "Xbox Series S", "preco_min": 200.0, "preco_max": 1400.0},
    
    # --- Sim Racing & Hardware Especializado ---
    {"termo": "Volante Moza", "preco_min": 400.0, "preco_max": 2500.0},
    {"termo": "Moza R5", "preco_min": 400.0, "preco_max": 2500.0},
    {"termo": "Volante Fanatec", "preco_min": 400.0, "preco_max": 2800.0},
    
    # --- Hardware PC (High-End) ---
    {"termo": "Ryzen 7 5700X3D", "preco_min": 150.0, "preco_max": 900.0},
    {"termo": "RTX 4070", "preco_min": 400.0, "preco_max": 3000.0},
    {"termo": "RTX 4060", "preco_min": 300.0, "preco_max": 1350.0},
    {"termo": "Water Cooler 360mm", "preco_min": 80.0, "preco_max": 300.0},
    {"termo": "Teclado Magnético", "preco_min": 50.0, "preco_max": 250.0},
    {"termo": "Mouse Sem Fio Leve", "preco_min": 30.0, "preco_max": 150.0}
]

CANAIS_BUGS = [
    "bugspromocoes",
    "ofertasdebugs",
    "promobugsbr",
    "promocoesaliexpress",
    "shopeebugs",
    "hardmob_promo"
]

ITENS_ENVIADOS = set()

def notificar_telegram(titulo, preco, link, origem):
    assinatura = f"{titulo}-{preco}"
    if assinatura in ITENS_ENVIADOS:
        return
    
    msg = (
        f"🚨🔥 *BUG SNIPER DETETADO!* 🔥🚨\n\n"
        f"🌐 *Origem:* {origem}\n"
        f"📦 *Item:* {titulo[:85]}...\n"
        f"💰 *Preço:* *R$ {preco:.2f}*\n\n"
        f"⚡ [COMPRAR URGENTE]({link})"
    )

    try:
        for _ in range(3):
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            time.sleep(1)
        print(f"   -> [BUG ENCONTRADO!] {titulo[:40]} por R$ {preco}")
    except Exception as e:
        print(f"Erro ao notificar o Telegram: {e}")
        
    ITENS_ENVIADOS.add(assinatura)

# =========================================================
# 1. MERCADO LIVRE API
# =========================================================
def sniper_mercadolivre():
    print("=== SNIPER API MERCADO LIVRE ===")
    
    for alvo in ALVOS_SNIPER:
        termo = alvo["termo"]
        p_min = alvo["preco_min"]
        p_max = alvo["preco_max"]
        
        url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo}&condition=new&limit=20"
        try:
            data = requests.get(url, timeout=10).json()
            resultados = data.get("results", [])
            print(f"[*] Varrendo Mercado Livre por '{termo}': {len(resultados)} anúncios analisados.")
            
            for item in resultados:
                preco_atual = float(item.get("price", 0))
                titulo = item.get("title", "")
                
                if p_min <= preco_atual <= p_max:
                    palavras_chave = termo.lower().split()
                    if all(palavra in titulo.lower() for palavra in palavras_chave):
                        link = item.get("permalink", "")
                        notificar_telegram(titulo, preco_atual, link, "Mercado Livre")
                        
        except Exception as e:
            print(f"[ERRO] Falha ao procurar {termo} no ML: {e}")

# =========================================================
# 2. TELEGRAM WEB
# =========================================================
def extrair_preco(texto):
    import re
    valores = re.findall(r"R\$\s*([\d\.,]+)", texto)
    if valores:
        limpo = valores[0].replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except:
            return 0.0
    return 0.0

def sniper_canais_telegram():
    print("\n=== SNIPER CANAIS DE BUGS (AGREGADORES) ===")
    headers = {"User-Agent": "Mozilla/5.0"}

    for canal in CANAIS_BUGS:
        url = f"https://t.me/s/{canal}"
        try:
            resposta = requests.get(url, headers=headers, timeout=15)
            if resposta.status_code == 200:
                soup = BeautifulSoup(resposta.text, 'html.parser')
                mensagens = soup.find_all('div', class_='tgme_widget_message_text')
                
                print(f"[*] Varrendo canal @{canal}: {len(mensagens)} mensagens recentes carregadas.")
                
                for msg_html in reversed(mensagens[-8:]):
                    texto_msg = msg_html.get_text(separator=" ", strip=True)
                    texto_minusculo = texto_msg.lower()
                    
                    for alvo in ALVOS_SNIPER:
                        termo_lower = alvo["termo"].lower()
                        
                        if termo_lower in texto_minusculo:
                            preco_encontrado = extrair_preco(texto_msg)
                            
                            if (alvo["preco_min"] <= preco_encontrado <= alvo["preco_max"]) or (preco_encontrado == 0.0 and "bug" in texto_minusculo):
                                link_tag = msg_html.find('a', href=True)
                                link_oferta = link_tag['href'] if link_tag else f"https://t.me/s/{canal}"
                                
                                titulo = texto_msg.split('http')[0].strip()[:80]
                                notificar_telegram(titulo, preco_encontrado, link_oferta, f"Alerta Comunidade (@{canal})")
                                break 
            else:
                print(f"    -> Erro ao aceder ao canal @{canal} (Status {resposta.status_code})")
        except Exception as e:
            print(f"    -> Falha ao processar canal @{canal}: {e}")

if __name__ == "__main__":
    print("=== INICIANDO SNIPER DE BUGS MULTI-LOJAS ===")
    sniper_mercadolivre()
    sniper_canais_telegram()
    print("\n=== VARREDURA FINALIZADA ===")
