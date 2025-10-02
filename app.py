# app.py
import streamlit as st
import plotly.graph_objects as go

st.title("Diagrama de Sankey de consumos de energía")

# --- Entrada de información ---
energ = st.text_input("¿Qué tipo de energía utilizas en tu inmueble?", "Eléctrica")
pisos = st.number_input("¿Cuántos pisos tiene tu inmueble?", min_value=1, value=1, step=1)

# Número de usos de energía
usenr = st.number_input(f"¿Cuántos usos de energía {energ} tienes en tu inmueble?", min_value=1, value=1, step=1)

# Capturar los usos de energía
usos = []
for i in range(usenr):
    uso = st.text_input(f"Uso de la energía {i+1}", f"Uso {i+1}")
    usos.append(uso)

# Capturar subcategorías
subcategorias = {cat: [] for cat in usos}
categorias_usadas = []

st.write("### Subcategorías (opcional)")
for cat in usos:
    agregar_sub = st.checkbox(f"Agregar subcategorías a {cat}?")
    if agregar_sub:
        num_sub = st.number_input(f"¿Cuántas subcategorías para {cat}?", min_value=1, value=1, step=1, key=f"num_{cat}")
        for i in range(num_sub):
            sub = st.text_input(f"Subcategoría {i+1} de {cat}", key=f"{cat}_{i}")
            subcategorias[cat].append(sub)

# Capturar consumos por piso
consumos = {}
st.write("### Consumos por piso")
for piso_num in range(1, pisos + 1):
    piso_key = f"Piso {piso_num}"
    consumos[piso_key] = {}
    st.write(f"#### {piso_key}")
    for cat in usos:
        consumos[piso_key][cat] = {}
        if subcategorias[cat]:
            for sub in subcategorias[cat]:
                valor = st.number_input(f"Consumo de '{sub}' en '{cat}'", min_value=0.0, value=0.0, step=0.1, key=f"{piso_key}_{cat}_{sub}")
                consumos[piso_key][cat][sub] = valor
        else:
            valor = st.number_input(f"Consumo de '{cat}'", min_value=0.0, value=0.0, step=0.1, key=f"{piso_key}_{cat}_total")
            consumos[piso_key][cat]["total"] = valor

# --- Crear diagrama Sankey ---
fuente_energia = energ

# Nodos
nodos = [fuente_energia] + usos.copy()
sub_nodos = []
piso_nodos = [f"Piso {i}" for i in range(1, pisos + 1)]

for cat in usos:
    for sub in subcategorias[cat]:
        nodo_nombre = f"{cat} - {sub}"
        sub_nodos.append(nodo_nombre)

nodos += sub_nodos + piso_nodos
nodo_idx = {nombre: i for i, nombre in enumerate(nodos)}

# Colores
colores = []
for nodo in nodos:
    if nodo == fuente_energia:
        colores.append("orange")
    elif nodo in usos:
        colores.append("green")
    elif any(nodo.startswith(f"{cat} -") for cat in usos):
        colores.append("purple")
    else:
        colores.append("blue")

# Enlaces
source = []
target = []
value = []

# Fuente → Usos
for cat in usos:
    total_cat = sum(sum(consumos[piso][cat].values()) for piso in consumos)
    source.append(nodo_idx[fuente_energia])
    target.append(nodo_idx[cat])
    value.append(total_cat)

# Usos → Subcategorías
for cat in usos:
    if subcategorias[cat]:
        for sub in subcategorias[cat]:
            flujo_total = sum(consumos[piso][cat][sub] for piso in consumos)
            source.append(nodo_idx[cat])
            target.append(nodo_idx[f"{cat} - {sub}"])
            value.append(flujo_total)

# Subcategorías → Pisos
for cat in usos:
    if subcategorias[cat]:
        for sub in subcategorias[cat]:
            for piso in consumos:
                valor = consumos[piso][cat][sub]
                source.append(nodo_idx[f"{cat} - {sub}"])
                target.append(nodo_idx[piso])
                value.append(valor)
    else:
        for piso in consumos:
            valor = consumos[piso][cat]["total"]
            source.append(nodo_idx[cat])
            target.append(nodo_idx[piso])
            value.append(valor)

# Crear figura
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=nodos,
        color=colores
    ),
    link=dict(
        source=source,
        target=target,
        value=value
    )
)])

fig.update_layout(title_text="Diagrama de Sankey de consumos de energía por piso", font_size=12)

# Mostrar diagrama en Streamlit
st.plotly_chart(fig)