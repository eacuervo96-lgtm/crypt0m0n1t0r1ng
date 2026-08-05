"""
Monitor de Criptomonedas (versión web)
--------------------------------------
Misma lógica que el script de consola original (consulta a la API pública
de CoinGecko, formato de cambios, alertas por umbral), pero con Streamlit
como capa de entrada/salida en vez de argparse + print().
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://api.coingecko.com/api/v3/simple/price"

COINS_DEFAULT = (
    "binancecoin,ripple,solana,tron,dogecoin,stellar,cardano,chainlink,"
    "litecoin,avalanche-2,near,uniswap,pax-gold,worldcoin,polkadot,"
    "internet-computer,polygon-ecosystem-token,ethena,algorand,arbitrum,injective-protocol"
)

st.set_page_config(page_title="Monitor de Criptomonedas", page_icon="🪙", layout="wide")


# ----------------------------------------------------------------
# LÓGICA (idéntica en espíritu al script original de consola)
# ----------------------------------------------------------------
@st.cache_data(ttl=30)
def obtener_precios(monedas: tuple, moneda_ref: str):
    """Consulta los precios actuales para una lista de monedas."""
    params = {
        "ids": ",".join(monedas),
        "vs_currencies": moneda_ref,
        "include_24hr_change": "true",
    }
    resp = requests.get(API_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def parsear_alertas(lista_alertas: str):
    """
    Convierte algo como:
        bitcoin:100000:90000,ethereum:5000:
    en:
        {"bitcoin": (100000, 90000), "ethereum": (5000, None)}
    """
    alertas = {}
    if not lista_alertas:
        return alertas
    for item in lista_alertas.split(","):
        partes = item.split(":")
        if len(partes) < 1 or not partes[0]:
            continue
        moneda = partes[0].strip()
        arriba = float(partes[1]) if len(partes) > 1 and partes[1] else None
        abajo = float(partes[2]) if len(partes) > 2 and partes[2] else None
        alertas[moneda] = (arriba, abajo)
    return alertas


def revisar_alertas(moneda, precio, alertas):
    """Devuelve una lista de mensajes de alerta disparados para esa moneda."""
    mensajes = []
    if moneda not in alertas:
        return mensajes
    umbral_arriba, umbral_abajo = alertas[moneda]
    if umbral_arriba and precio >= umbral_arriba:
        mensajes.append(f"⚠ {moneda} superó {umbral_arriba}")
    if umbral_abajo and precio <= umbral_abajo:
        mensajes.append(f"⚠ {moneda} cayó por debajo de {umbral_abajo}")
    return mensajes


# ----------------------------------------------------------------
# BARRA LATERAL — equivalente a los argumentos de línea de comandos
# ----------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")

    coins_input = st.text_area(
        "Monedas a monitorear (ids de CoinGecko, separados por coma)",
        value=COINS_DEFAULT,
        height=100,
    )

    moneda_ref = st.selectbox("Moneda de referencia", ["usd", "eur", "cop", "mxn", "ars"], index=0)

    alertas_input = st.text_input(
        "Alertas (formato moneda:arriba:abajo, separadas por coma)",
        value="",
        placeholder="bitcoin:100000:90000,ethereum:5000:",
    )

    st.caption("Deja el intervalo de recarga automática de Streamlit por defecto; usa el botón de abajo para refrescar cuando quieras.")

    consultar = st.button("🔄 Consultar ahora", use_container_width=True)


# ----------------------------------------------------------------
# INTERFAZ PRINCIPAL
# ----------------------------------------------------------------
st.title("🪙 Monitor de Criptomonedas")

monedas = tuple(m.strip() for m in coins_input.split(",") if m.strip())
alertas = parsear_alertas(alertas_input)

if not monedas:
    st.warning("Agrega al menos una moneda en la barra lateral.")
    st.stop()

if consultar:
    st.cache_data.clear()

try:
    datos = obtener_precios(monedas, moneda_ref)
except Exception as e:
    st.error(f"Error al consultar la API: {e}")
    st.stop()

ahora = datetime.now().strftime("%H:%M:%S")
st.caption(f"Última consulta: {ahora} · moneda de referencia: {moneda_ref.upper()}")

# Diagnóstico de monedas no encontradas (igual que el script original)
faltantes = [m for m in monedas if m not in datos]
if faltantes:
    st.warning(
        f"No se encontraron datos para: {', '.join(faltantes)}. "
        f"Revisa que el id sea exactamente el de CoinGecko, en minúsculas."
    )

# Armar filas de datos + disparar alertas
filas = []
mensajes_alerta = []
for moneda, info in datos.items():
    precio = info.get(moneda_ref)
    cambio = info.get(f"{moneda_ref}_24h_change")
    if precio is None:
        continue
    filas.append({"Moneda": moneda.capitalize(), "id": moneda, "Precio": precio, "Cambio 24h (%)": cambio})
    mensajes_alerta.extend(revisar_alertas(moneda, precio, alertas))

df = pd.DataFrame(filas).sort_values("Cambio 24h (%)", ascending=False).reset_index(drop=True)

# Mostrar alertas disparadas (equivalente al print en amarillo del script original)
for msg in mensajes_alerta:
    st.warning(msg)

# Tarjetas (3 por fila)
n_columnas = 3
for i in range(0, len(df), n_columnas):
    fila = df.iloc[i:i + n_columnas]
    cols = st.columns(len(fila))
    for col, (_, m) in zip(cols, fila.iterrows()):
        precio_str = f"{m['Precio']:,.4f}" if m["Precio"] < 1 else f"{m['Precio']:,.2f}"
        cambio = m["Cambio 24h (%)"]
        cambio_str = f"{cambio:+.2f}%" if cambio is not None else "N/D"
        col.metric(label=m["Moneda"], value=f"{precio_str} {moneda_ref.upper()}", delta=cambio_str)

st.divider()
st.subheader("Tabla completa")
st.dataframe(
    df[["Moneda", "Precio", "Cambio 24h (%)"]].rename(columns={"Precio": f"Precio ({moneda_ref.upper()})"}),
    use_container_width=True,
)

st.caption("Fuente: CoinGecko API (pública, sin API key). No es asesoría financiera.")
