from groq import Groq
import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import feedparser
from datetime import datetime
import os

# 1. Configuração da Página
st.set_page_config(page_title="Radar Macro B3 v2.0", layout="wide", page_icon="🛰️")

# ---------------------------------------------------
# SIDEBAR - CONFIGURAÇÕES
# ---------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configurações")
    # Tenta pegar a chave do ambiente ou do campo de texto
    api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GOOGLE_API_KEY") or "")
    st.info("O 'Veredito IA' utiliza o modelo gemini-2.0-flash.")

# ---------------------------------------------------
# FUNÇÃO DE DADOS (YFINANCE)
# ---------------------------------------------------
def pegar_preco(ticker):
    try:
        # Busca 2 dias para garantir dados em janelas de fechamento
        df = yf.download(ticker, period="2d", interval="1m", progress=False)
        if not df.empty:
            return float(df["Close"].iloc[-1])
        return None
    except:
        return None

# ---------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------
st.title("🛰️ Radar Macro Global → B3")
st.write(f"Monitoramento em tempo real • {datetime.now().strftime('%H:%M:%S')}")

# RADAR GLOBAL
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

# RADAR BRASIL
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
        st.metric("Focus IPCA", ipca)
    except:
        st.metric("Focus IPCA", "erro")

# ---------------------------------------------------
# CÁLCULOS DE STRESS E SCORE
# ---------------------------------------------------
t10 = dados_mercado.get("T10Y")
t2 = dados_mercado.get("T2Y")
spread = (t10 - t2) if (t10 and t2) else 0

vix = dados_mercado.get("VIX", 0) or 0
dxy = dados_mercado.get("DXY", 0) or 0
petroleo = dados_mercado.get("Petróleo", 0) or 0

# Score Macro (0 a 10)
score = 0
if vix > 20: score += 2
if vix > 25: score += 2
if dxy > 104: score += 1
if spread < 0: score += 2
if petroleo > 90: score += 1

# GeoRisk (Notícias)
st.subheader("🌐 Radar Geopolítico")
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
    except:
        pass

col_risk, col_news = st.columns([1, 3])
with col_risk:
    st.metric("GeoRisk Score", tensao)
with col_news:
    with st.expander("Ver manchetes recentes"):
        for n in noticias[:15]:
            st.write(f"• {n}")

# ISG - Índice de Stress Global
st.subheader("🌡️ Índice de Stress Global")
isg = (score * 10) + (tensao * 3) + (vix if vix else 0)
st.metric("ISG", round(isg, 2))
st.progress(min(isg/150, 1.0))

# -# ---------------------------------------------------
# PROBABILIDADES WIN / WDO (O QUE TINHA ANTES)
# ---------------------------------------------------
st.divider()
col_win, col_wdo = st.columns(2)

# Cálculo baseado no seu Score e Tensão Geopolítica
prob_win = max(0, 70 - (score * 10) - tensao)
prob_wdo = min(100, 30 + (score * 10) + tensao)

with col_win:
    st.metric("Probabilidade WIN Subir", f"{prob_win}%")

with col_wdo:
    st.metric("Probabilidade WDO Subir", f"{prob_wdo}%")

# ---------------------------------------------------
# ANALISTA + TRADER MACRO IA (VIA GROQ) 
# -----------------------------------------------------------------------------------------------------
# ---------------------------------------------------
# ANALISTA + TRADER MACRO IA (VIA GROQ)
# ---------------------------------------------------
from groq import Groq

st.subheader("🧠 Veredito IA (Alta Velocidade Groq)")

with st.sidebar:
    st.divider()
    groq_key = st.text_input("Groq API Key", type="password")
    st.info("Pegue sua chave grátis em: console.groq.com")

if st.button("Gerar Plano de Trade"):
    if not groq_key:
        st.error("Insira a Groq API Key na barra lateral!")
    else:
        try:
            client = Groq(api_key=groq_key)
            
            # Contexto resumido para o Llama 3
            prompt = f"""
            Analise como um Head Trader de Mesa Proprietária:
            VIX: {vix:.2f} | DXY: {dxy:.2f} | ISG: {isg:.2f} | GeoRisk: {tensao}
            Spread Juros EUA: {spread:.4f}
            
            Notícias: {'. '.join(noticias[:5])}
            
            Com base nesses dados e na volatilidade atual:
            1. Dê o VIÉS para WIN e WDO.
            2. Forneça ALVOS e STOPS específicos para o contrato atual de WIN e WDO.
            3. Seja direcional, realista e focado em números técnicos.
            """

            with st.spinner("Groq processando..."):
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Você é um analista macro de mesa de operações."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                
                st.info("### 🏁 Plano de Trade Profissional")
                st.write(chat_completion.choices[0].message.content)
                
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
