# Monitor de Criptomonedas (versión web)

Adaptación web de `monitor_crypto.py`. La lógica es la misma; solo cambió
la forma de entrada/salida.

## Qué se mantuvo igual

- La consulta a la API de CoinGecko (`obtener_precios`).
- El parseo de alertas (`parsear_alertas`), mismo formato `moneda:arriba:abajo`.
- La idea de revisar umbrales y avisar cuando se disparan.
- El diagnóstico de "monedas no encontradas".

## Qué cambió (consola → web)

| Consola (`argparse` / `input` / `print`)      | Web (Streamlit)                              |
|------------------------------------------------|-----------------------------------------------|
| `--coins` (argumento de línea de comandos)     | Cuadro de texto en la barra lateral           |
| `--moneda-ref`                                  | Selector (`selectbox`) en la barra lateral    |
| `--alertas`                                     | Campo de texto en la barra lateral            |
| `--interval` + loop `while True` + `sleep`     | Botón "Consultar ahora" (recarga bajo demanda)|
| `print()` con colores ANSI                     | `st.metric`, tablas y `st.warning` para alertas|
| Ctrl+C para detener                            | No aplica (no hay loop infinito en el servidor)|

Nota sobre el intervalo automático: en la versión de consola el script queda
corriendo indefinidamente. En la web, mantener un loop infinito en el servidor
no es práctico (consume recursos incluso sin nadie mirando). Por eso aquí se
consulta bajo demanda (al cargar la página o al tocar el botón). Si más adelante
quieres auto-refresco real cada X segundos sin que el usuario haga nada, se
puede agregar con el paquete `streamlit-autorefresh` — avísame y lo sumamos.

## Probarlo en tu computador

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Desplegarlo gratis (Streamlit Community Cloud)

1. Sube `app.py`, `requirements.txt` y este `README.md` a un repositorio de GitHub.
2. Entra a https://share.streamlit.io con tu cuenta de GitHub.
3. "New app" → elige el repo, la rama y `app.py` → Deploy.
4. Abre la URL resultante desde tu Android y agrégala a la pantalla de inicio.
