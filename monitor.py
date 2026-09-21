import os
import sys
import re
from telethon import TelegramClient, events

# Força o terminal a mostrar os textos instantaneamente sem travar
sys.stdout.reconfigure(encoding='utf-8')

print("==================================================")
print("🚀 A INICIALIZAR O SNIPER (COM RADAR DE CUPONS)...")
print("==================================================")

API_ID = 33513465
API_HASH = '9d8b8aa09655a837b0afc43a89acc19'

# ==========================================
# 1. A SUA LISTA COMPLETA RESTAURADA
# ==========================================
ALVOS_SNIPER = [
    # Smartphones
    {"termo": "iPhone 15", "preco_min": 800.0, "preco_max": 3800.0},
    {"termo": "iPhone 14", "preco_min": 800.0, "preco_max": 2800.0},
    {"termo": "iPhone 13", "preco_min": 800.0, "preco_max": 2200.0},
    {"termo": "Galaxy S26", "preco_min": 1000.0, "preco_max": 4000.0},
    {"termo": "Galaxy S25", "preco_min": 1000.0, "preco_max": 3500.0},
    {"termo": "Galaxy S24", "preco_min": 1000.0, "preco_max": 2800.0},
    
    # Consolas
    {"termo": "Playstation 5", "preco_min": 300.0, "preco_max": 2800.0},
    {"termo": "PS5", "preco_min": 300.0, "preco_max": 2800.0},
    {"termo": "Xbox Series X", "preco_min": 300.0, "preco_max": 2900.0},
    {"termo": "Xbox Series S", "preco_min": 200.0, "preco_max": 1400.0},
    
    # Sim Racing
    {"termo": "Volante Moza", "preco_min": 400.0, "preco_max": 2500.0},
    {"termo": "Moza R5", "preco_min": 400.0, "preco_max": 2500.0},
    {"termo": "Volante Fanatec", "preco_min": 400.0, "preco_max": 2800.0},
    
    # Processadores AMD
    {"termo": "Ryzen 5 5600", "preco_min": 100.0, "preco_max": 500.0},
    {"termo": "Ryzen 7 5700X3D", "preco_min": 150.0, "preco_max": 900.0},
    {"termo": "Ryzen 9 5900X", "preco_min": 300.0, "preco_max": 1300.0},
    {"termo": "Ryzen 7 7800X3D", "preco_min": 500.0, "preco_max": 2000.0},
    {"termo": "Ryzen 5 9600X", "preco_min": 400.0, "preco_max": 1200.0},
    {"termo": "Ryzen 7 9700X", "preco_min": 600.0, "preco_max": 1700.0},
    {"termo": "Ryzen 9 9900X", "preco_min": 800.0, "preco_max": 2200.0},
    {"termo": "Ryzen 9 9950X", "preco_min": 1000.0, "preco_max": 3200.0},

    # Placas de Vídeo (NVIDIA)
    {"termo": "RTX 4090", "preco_min": 2000.0, "preco_max": 8000.0},
    {"termo": "RTX 4080", "preco_min": 1500.0, "preco_max": 5000.0},
    {"termo": "RTX 4070 Ti", "preco_min": 1000.0, "preco_max": 3800.0},
    {"termo": "RTX 4070", "preco_min": 800.0, "preco_max": 3000.0},
    {"termo": "RTX 4060 Ti", "preco_min": 500.0, "preco_max": 1800.0},
    {"termo": "RTX 4060", "preco_min": 300.0, "preco_max": 1350.0},
    {"termo": "RTX 3060", "preco_min": 200.0, "preco_max": 900.0},

    # Placas de Vídeo (AMD)
    {"termo": "RX 7900 XTX", "preco_min": 1500.0, "preco_max": 4500.0},
    {"termo": "RX 7800 XT", "preco_min": 800.0, "preco_max": 2800.0},
    {"termo": "RX 7700 XT", "preco_min": 500.0, "preco_max": 2000.0},
    {"termo": "RX 7600", "preco_min": 300.0, "preco_max": 1200.0},
    {"termo": "RX 6700 XT", "preco_min": 300.0, "preco_max": 1300.0},
    
    # Periféricos e Refrigeração
    {"termo": "Teclado Magnético", "preco_min": 50.0, "preco_max": 250.0},
    {"termo": "Mouse Sem Fio", "preco_min": 30.0, "preco_max": 150.0},
    {"termo": "Water Cooler 360mm", "preco_min": 80.0, "preco_max": 300.0}
]

# ==========================================
# 2. RADAR DE CUPONS BUGADOS
# ==========================================
PALAVRAS_CHAVE_CUPOM = ["cupom", "codigo", "código"]
GATILHOS_DE_BUG = ["bug", "erro", "imperdível", "surreal", "grátis", "100%", "90%", "80%"]

CANAIS_MONITORIZADOS = [
    'hardmob_promo',
    'bugspromocoes',
    'ofertasdebugs',
    'promobugsbr',
    'promobit'
]

print("[*] A ligar ao cliente do Telegram...")
client = TelegramClient('sessao_sniper', API_ID, API_HASH)

def extrair_preco(texto):
    valores = re.findall(r"R\$\s*([\d\.,]+)", texto)
    if valores:
        limpo = valores[0].replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except:
            return 0.0
    return 0.0

@client.on(events.NewMessage(chats=CANAIS_MONITORIZADOS))
async def ouvinte_de_bugs(event):
    texto = event.message.text
    if not texto:
        return
        
    texto_minusculo = texto.lower()
    bug_encontrado = False
    
    # 1. VERIFICAÇÃO DE PREÇO (O SEU HARDWARE)
    for alvo in ALVOS_SNIPER:
        if alvo["termo"].lower() in texto_minusculo:
            preco_encontrado = extrair_preco(texto)
            if alvo["preco_min"] <= preco_encontrado <= alvo["preco_max"]:
                print(f"\n🚨 PREÇO SNIPER: {alvo['termo']} por R$ {preco_encontrado}")
                await event.message.forward_to('me')
                await client.send_message('me', f"🔥 ALERTA DE HARDWARE: {alvo['termo']} detetado a R$ {preco_encontrado:.2f}!")
                bug_encontrado = True
                break

    # 2. VERIFICAÇÃO DE CUPOM BUGADO (Se não for hardware de cima, mas for um cupom insano)
    if not bug_encontrado:
        tem_cupom = any(palavra in texto_minusculo for palavra in PALAVRAS_CHAVE_CUPOM)
        tem_gatilho_bug = any(gatilho in texto_minusculo for gatilho in GATILHOS_DE_BUG)
        
        # Também verifica se a palavra "cupom" está junto com o nome de um dos seus alvos
        cupom_no_alvo = tem_cupom and any(alvo["termo"].lower() in texto_minusculo for alvo in ALVOS_SNIPER)
        
        if (tem_cupom and tem_gatilho_bug) or cupom_no_alvo:
            print(f"\n🎟️ ALERTA DE CUPOM BUGADO DETETADO NA MENSAGEM!")
            await event.message.forward_to('me')
            await client.send_message('me', "🎟️⚠️ **POSSÍVEL CUPOM BUGADO DETETADO!** Verifique a mensagem acima rápido!")

print("[*] Pronto para iniciar. Se for o primeiro uso validará a sessão...")
client.start()
print("🎯 SUCESSO! LISTA COMPLETA CARREGADA. A ESCUTAR CANAIS...")
client.run_until_disconnected()
