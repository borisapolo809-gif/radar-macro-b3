import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import feedparser
from datetime import datetime
import os
from groq import Groq

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando)
st.set_page_config(page_title="Radar Macro B3 v2.0", layout="wide", page_icon="🛰️")

# 2. ESTILO VISUAL "ULTRON AI" (DARK NEON)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc !important; font-size: 30px !important; font-weight: bold; }
    div[data-testid="stMetricDelta"] { color: #ff4b4b !important; }
    .stMarkdown h1, h2, h3 { color: #ffffff; text-shadow: 0px 0px 8px #00ffcc66; }
    div.stButton > button:first-child {
        background-color: #00ffcc; color: black; border-radius: 8px;
        font-weight: bold; width: 100%; border: none; height: 3em; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #00cca3; color: white; }
    .stInfo { background-color: #161b22; border: 1px solid #00ffcc; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR - CONFIGURAÇÕES
# ---------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configurações")
    groq_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY") or "")
    st.info("Pegue sua chave grátis em: console.groq.com")
    
    st.divider()
    st.subheader("📲 Alertas Telegram")
    tg_token = st.text_input("Bot Token", type="password")
    tg_id = st.text_input("Seu Chat ID")

# ---------------------------------------------------
# FUNÇÕES DE DADOS
# ---------------------------------------------------
def pegar_preco(ticker):
    try:
        df = yf.download(ticker, period="2d", interval="1m", progress=False)
        if not df.empty:
            return float(df["Close"].iloc[-1])
        return None
    except:
        return None

def enviar_pro_telegram(texto):
    if tg_token and tg_id:
        try:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {"chat_id": tg_id, "text": f"🛰️ RADAR MACRO\n\n{texto[:3500]}"}
            requests.post(url, data=payload)
        except:
            pass

# ---------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------
st.title("🛰️ Radar Macro Global → B3")
st.write(f"📊 Monitoramento em Tempo Real • {datetime.now().strftime('%H:%M:%S')}")

# SEÇÃO 1: SENSORES GLOBAIS
st.subheader("🌍 Sensores Globais")
ativos = {
    "S&P500": "^GSPC", "NASDAQ": "^IXIC", "VIX": "^VIX",
    "DXY": "DX-Y.NYB", "T10Y": "^TNX", "T2Y": "^IRX",
    "Ouro": "GC=F", "Petróleo": "CL=F"
}

dados_mercado = {}
cols = st.columns(len(ativos))

for i, (nome, ticker) in enumerate(ativos.items()):
    valor = pegar_preco(ticker)
    dados_mercado[nome] = valor
    with cols[i]:
        if valor:
            st.metric(nome, f"{valor:,.2f}")
        else:
            st.metric(nome, "erro")

# SEÇÃO 2: RADAR BRASIL
st.subheader("🇧🇷 Radar Brasil")
col1, col2, col3 = st.columns(3)

ibov = pegar_preco("^BVSP")
dolar = pegar_preco("BRL=X")

with col1:
    st.metric("Ibovespa", f"{ibov:,.2f}" if ibov else "erro")
with col2:
    st.metric("USD/BRL", f"{dolar:,.2f}" if dolar else "erro")
with col3:
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        ipca = requests.get(url).json()[0]["valor"]
        st.metric("Focus IPCA", f"{ipca}%")
    except:
        st.metric("Focus IPCA", "erro")

# ---------------------------------------------------
# CÁLCULOS DE STRESS E NOTÍCIAS
# ---------------------------------------------------
vix = dados_mercado.get("VIX", 0) or 0
dxy = dados_mercado.get("DXY", 0) or 0
petroleo = dados_mercado.get("Petróleo", 0) or 0
t10 = dados_mercado.get("T10Y", 0) or 0
t2 = dados_mercado.get("T2Y", 0) or 0
spread = (t10 - t2)

# Radar Geopolítico
feeds = ["https://feeds.bbci.co.uk/news/world/rss.xml", "https://www.cnbc.com/id/100003114/device/rss/rss.html"]
keywords = ["war", "conflict", "inflation", "crisis", "recession", "fed", "rates", "china"]
tensao = 0
noticias = []

for url in feeds:
    try:
        f = feedparser.parse(url)
        for entry in f.entries[:8]:
            titulo = entry.title
            noticias.append(titulo)
            if any(k in titulo.lower() for k in keywords):
                tensao += 1
    except: pass

# ISG - Índice de Stress Global
st.divider()
col_isg, col_prob = st.columns([1, 2])

with col_isg:
    st.subheader("🌡️ Stress Global (ISG)")
    # Cálculo Score Macro
    score = 0
    if vix > 20: score += 2
    if dxy > 104: score += 2
    if spread < 0: score += 2
    
    isg = (score * 10) + (tensao * 3) + (vix if vix else 0)
    st.metric("ISG Index", round(isg, 2), delta="RISCO ALTO" if isg > 50 else "NORMAL")
    st.progress(min(isg/150, 1.0))

with col_prob:
    st.subheader("🎯 Probabilidades Operacionais")
    p_win = max(0, 70 - (score * 10) - tensao)
    p_wdo = min(100, 30 + (score * 10) + tensao)
    c1, c2 = st.columns(2)
    c1.metric("WIN Subir", f"{p_win}%")
    c2.metric("WDO Subir", f"{p_wdo}%")

# ---------------------------------------------------
# BOTÃO DE ANÁLISE IA
# ---------------------------------------------------
st.divider()
st.subheader("🧠 Veredito IA - Head Trader")

if st.button("🚀 GERAR PLANO DE TRADE"):
    if not groq_key:
        st.error("Insira a Groq API Key na barra lateral!")
    else:
        try:
            client = Groq(api_key=groq_key)
            prompt = f"""
            Analise como um Head Trader:
            PREÇOS B3: WIN {ibov:,.2f} | WDO {dolar:,.2f}
            MACRO: VIX {vix:.2f}, DXY {dxy:.2f}, ISG {isg:.2f}, GeoRisk {tensao}
            NOTÍCIAS: {'. '.join(noticias[:3])}
            
            RETORNE:
            1. VIÉS (WIN e WDO).
            2. ALVO e STOP baseados nos preços reais acima.
            3. RESUMO do risco do dia.
            """

            with st.spinner("Analisando mercado mundial..."):
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Analista macro profissional."},
                              {"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                resposta = chat_completion.choices[0].message.content
                st.info(resposta)
                enviar_pro_telegram(resposta)
                st.success("✅ Plano enviado para o Telegram!")
        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")
st.caption("Radar Macro Pro v2.0 | Dados: Yahoo Finance & BCB | Inteligência: Llama-3 via Groq")
