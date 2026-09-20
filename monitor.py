import os
import time
import re
import cloudscraper
import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MIN_DISCOUNT_PERCENT = 50.0

STORES = [
    {
        "name": "Kabum",
        "url": "https://www.kabum.com.br/promocao/MENU_GERAL",
        "card": "article.productCard",
        "title": "span.nameCard",
    },
    {
        "name": "Terabyte",
        "url": "https://www.terabyteshop.com.br/promocoes",
        "card": "div.pbox",
        "title": "a.prod-name",
    },
    {
        "name": "Pichau",
        "url": "https://www.pichau.com.br/promocoes",
        "card": "div[class*='MuiCard-root']",
        "title": "h2",
    },
    {
        "name": "Nike",
        "url": "https://www.nike.com.br/nav/ofertas",
        "card": "div[data-testid='product-card']",
        "title": "h2",
    },
    {
        "name": "Adidas",
        "url": "https://www.adidas.com.br/outlet",
        "card": "div.glass-product-card-container",
        "title": "p.glass-product-card__title",
    },
    {
        "name": "Centauro",
        "url": "https://www.centauro.com.br/outlet",
        "card": "div[data-testid='product-card']",
        "title": "p[data-testid='product-title']",
    },
    {
        "name": "Netshoes",
        "url": "https://www.netshoes.com.br/promocoes",
        "card": "div[data-testid='product-card']",
        "title": "span.item-card__description",
    },
    {
        "name": "AliExpress",
        "url": "https://pt.aliexpress.com/campaign/superdeals",
        "card": "a[href*='/item/']",
        "title": "h1, h3, div.title",
    },
    {
        "name": "Shein",
        "url": "https://br.shein.com/campaigns/sale",
        "card": "section.product-card",
        "title": "a.goods-title-link",
    },
    {
        "name": "Amazon",
        "url": "https://www.amazon.com.br/deals",
        "card": "div[data-testid='deal-card']",
        "title": "div[class*='DealContent']",
    }
]

def send_telegram_alert(title, discount, link, store_name):
    if discount >= 80.0:
        header = f"🚨🔥 *BUG DETETADO / PREÇO ANÓMALO ({discount:.0f}% OFF)!* 🔥🚨"
        repeat_count = 3
    else:
        header = f"⚡ *OPORTUNIDADE FORTE ({discount:.0f}% OFF)* ⚡"
        repeat_count = 1

    clean_title = re.sub(r"\s+", " ", title).strip()[:85]
    msg = (
        f"{header}\n\n"
        f"🌐 *Origem:* {store_name}\n"
        f"📦 *Item:* {clean_title}\n"
        f"💥 *Desconto:* *{discount:.1f}% OFF*\n\n"
        f"⚡ [COMPRAR AGORA]({link})"
    )

    for i in range(repeat_count):
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                timeout=10,
            )
            print(f"   -> [ALERTA {i+1}/{repeat_count}] {clean_title[:30]}... ({discount:.1f}% OFF)")
            if repeat_count > 1:
                time.sleep(1.5)
        except Exception as e:
            print(f"Erro Telegram: {e}")

def scan_mercadolivre_api():
    print("[MERCADO LIVRE] A consultar API oficial...")
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
                    send_telegram_alert(item.get("title", "Produto ML"), disc, item.get("permalink", ""), "Mercado Livre")
        print(f"[MERCADO LIVRE] Analisados: {len(results)} itens | Maior desconto: {max_disc:.1f}%")
    except Exception as e:
        print(f"[MERCADO LIVRE] Erro na API: {e}")

def scan_html_stores():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    for store in STORES:
        name = store["name"]
        print(f"[{name.upper()}] A extrair dados da página...")
        max_disc = 0.0
        items_count = 0

        try:
            resp = scraper.get(store["url"], timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = soup.select(store["card"])
                items_count = len(cards)

                for card in cards:
                    texto_card = card.get_text(separator=" ", strip=True)
                    match = re.search(r"(\d{1,2})%\s*(?:OFF|off|desconto)?", texto_card)
                    
                    if match:
                        disc = float(match.group(1))
                        if 0 < disc < 100:
                            if disc > max_disc: max_disc = disc
                            if disc >= MIN_DISCOUNT_PERCENT:
                                title_el = card.select_one(store["title"])
                                title = title_el.get_text(strip=True) if title_el else texto_card.split("R$")[0][:60]
                                
                                link_el = card.find("a", href=True)
                                link = link_el["href"] if link_el else store["url"]
                                if link.startswith("/"):
                                    base_url = "/".join(store["url"].split("/")[:3])
                                    link = base_url + link
                                
                                send_telegram_alert(title, disc, link, name)
            else:
                print(f"[{name.upper()}] Bloqueio de rede (Status {resp.status_code}).")
        except Exception as e:
            print(f"[{name.upper()}] Erro: {e}")

        print(f"[{name.upper()}] Analisados: {items_count} itens | Maior desconto: {max_disc:.1f}%\n")

if __name__ == "__main__":
    print("=== INICIANDO SISTEMA DE RASTREIO (V2 BACK-END) ===")
    scan_mercadolivre_api()
    scan_html_stores()
    print("=== VARREDURA FINALIZADA ===")
