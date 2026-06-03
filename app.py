# app_consumo.py
# ===========================================
# ⚡ APP STREAMLIT: Oficina / Salud / Otros usos + Residencial (integrado) + Consejos dinámicos
# ===========================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import time
from docx import Document
from datetime import date

def generar_reporte_word(datos, plantilla_path, salida_path):
    doc = Document(plantilla_path)

    for paragraph in doc.paragraphs:
        for key, value in datos.items():
            marcador = f"{{{{{key}}}}}"
            if marcador in paragraph.text:
                paragraph.text = paragraph.text.replace(marcador, str(value))

    doc.save(salida_path)

# Reiniciar datos cada vez que se recarga la app
if "sankey_data" not in st.session_state:
    st.session_state["sankey_data"] = []
else:
    st.session_state["sankey_data"].clear()

# Lista de equipos que permanecen conectados todo el día
equipos_continuos = [
    "Refrigerador",
    "Teléfono inalámbrico",
    "Teléfono analógico",
    "Teléfono con pantalla",
    "Servidores",
    "Routers Wi-Fi",
    "Bocina inteligente",
    "Celular / Smartphone",
    "Laptop",
    "Bocina inteligente (Amazon Echo / Echo Dot, Google Nest Mini, Apple HomePod)"
]

# ------------------------
# BASES DE DATOS (potencias y COPs)
# ------------------------

# Potencias nominales por subuso (W)
potencias_nominales = {
    "Tubo LED T8": 18, "Tubo LED T5": 16, "Foco LED": 10, "Panel LED": 25,
    "Tubo fluorescente T8": 36, "Tubo fluorescente T5": 28, "Fluorescente compacto": 20,
    "Incandescente": 60, "Halógena": 50, "Computadora de escritorio": 250, "Laptop": 5.2,
    "Refrigerador": 47, "Cafetera": 1000, "Microondas": 1000, "Parrilla o estufa eléctrica": 1500,
    "Horno eléctrico": 1200, "Purificador de aire": 150, "Bomba de agua": 1800,
    "Elevador": 12000, "Escaleras eléctricas": 15000, "Compresor": 4000,
    "Fotocopiadora/ Impresora": 300, "Escáner": 30, "Multiusos": 100, "Ventilador individual": 80,
    "Cañones y proyectores": 200, "Teléfono analógico": 0.67, "Teléfono con pantalla": 1.65,
    "Teléfono inalámbrico": 3.3, "Routers Wi-Fi": 20, "Plancha": 1745, "Licuadora": 750,
    "Ventilador de techo": 100, "Bocina inteligente (Amazon Echo / Echo Dot, Google Nest Mini, Apple HomePod)": 11,
    "Televisor LED / LCD": 150, "Televisor de plasma": 240, "Consola de videojuegos": 250, "Equipo de audio / estéreo": 120,
    "Lavadora 7-15 kg": 550, "Lavadora más de 15 kg": 800, "Secadora eléctrica": 1500, "Celular / Smartphone": 1.4,
    "Lavavajillas":1350, "Servicio de televisión por cable": 20, "Caminadora": 2000, "Eliptica eléctrica": 250, 
    "Escaladora": 1200, "Sillón de masaje": 300, "Calentador eléctrico instantaneo": 10000 ,  
    "Calentador eléctrico con deposito": 3500, "Resistencia eléctrica": 1500
}

# COPs para uso general (no residenciales)
cop_data = {
    "Acondicionadores de aire tipo cuarto/ventana": {"nuevo": 3.2, "5-10 años": 2.9, "+10 años": 2.5},
    "Acondicionadores de aire tipo dividido (Heat pump)": {"nuevo": 3.5, "5-10 años": 3.0, "+10 años": 2.5},
    "Acondicionadores de aire tipo dividido (Fan & Coil)": {"nuevo": 3.5, "5-10 años": 3.0, "+10 años": 2.5},
    "Acondicionadores de aire tipo dividido (Split)": {"nuevo": 3.3, "5-10 años": 2.8, "+10 años": 2.3},
    "Acondicionadores de aire tipo dividido (Split inverter)": {"nuevo": 4.0, "5-10 años": 3.3, "+10 años": 2.8},
    "Sistema de enfriamiento constante o variable (VRV o VRF)": {"nuevo": 4.5, "5-10 años": 3.8, "+10 años": 3.3},
    "Chiller (condensador enfriado por agua)": {"nuevo": 5.0, "5-10 años": 4.5, "+10 años": 3.5},
    "Chiller (condensador enfriado por aire)": {"nuevo": 3.3, "5-10 años": 2.8, "+10 años": 2.3},
    "Chiller de Absorción": {"nuevo": 1.0, "5-10 años": 0.8, "+10 años": 0.6},
    "Chiller Modular": {"nuevo": 4.5, "5-10 años": 4.0, "+10 años": 3.3}
}

# COPs residenciales (base individual para la pestaña Residencial)
cop__data = {
    "Acondicionadores de aire tipo cuarto/ventana": {"nuevo": 3.2, "5-10 años": 2.9},
    "Acondicionadores de aire tipo minisplit (convencional)": {"nuevo": 2.95, "5-10 años": 2.6},
    "Acondicionadores de aire tipo minisplit (inverter)": {"nuevo": 3.3, "5-10 años": 3.0},
    "Acondicionadores de aire tipo multisplit": {"nuevo": 3.18, "5-10 años": 2.9},
    "Acondicionadores de aire tipo dividido/paquete": {"nuevo": 3.3, "5-10 años": 2.9},
    "Acondicionadores de aire tipo portatil": {"nuevo": 2.87, "5-10 años": 2.5},
}

# Usos por tipo de inmueble (tal como solicitaste)
usos_por_inmueble = {
    "Oficina": ["Iluminación", "Acondicionamiento de aire", "Equipos de cómputo", "Site de computo",
                "Electrodomésticos", "Equipos de fuerza", "Equipos de oficina", "Telecomunicaciónes", "Otros"],
    "Salud": ["Iluminación", "Acondicionamiento de aire", "Equipos de cómputo", "Site de computo",
              "Electrodomésticos", "Equipos de fuerza", "Equipos de oficina", "Telecomunicaciónes",
              "Equipos médicos", "Equipos de laboratorio",
              "Servicios auxiliares (esterilización, calentadores eléctricos etc)", "Otros"],
    "Otros usos": ["Iluminación", "Acondicionamiento de aire", "Equipos de cómputo", "Site de computo",
                   "Electrodomésticos", "Equipos de fuerza", "Equipos de oficina", "Telecomunicaciónes",
                   "Sistemas audiovisuales", "Equipos de ejercicio y recreativos", "Otros"],
    # Residencial estará como pestaña separada, pero también dejamos la definición para subusos compartidos
}

# Sub-usos
subusos = {
    "Iluminación": ["Tubo LED T8", "Tubo LED T5", "Foco LED", "Panel LED", "Tubo fluorescente T8",
                    "Tubo fluorescente T5", "Fluorescente compacto", "Incandescente", "Halógena", "Otro"],
    "Acondicionamiento de aire": list(cop_data.keys()) + ["Otro"],
    "Acondicionamiento de aire residencial": list(cop__data.keys()) + ["Otro"],
    "Electrodomésticos": ["Refrigerador", "Cafetera", "Microondas", "Parrilla o estufa eléctrica",
                          "Horno eléctrico", "Purificador de aire", "Ventilador de techo", "Ventilador individual", "Otro"],
    "Electrodomésticos residenciales": ["Refrigerador", "Cafetera", "Microondas", "Parrilla o estufa eléctrica",
                          "Horno eléctrico", "Purificador de aire", "Plancha", "Licuadora","Ventilador de techo",
                          "Lavadora 7-15 kg", "Lavadora más de 15 kg", "Secadora eléctrica", "Lavavajillas", "Otro"],
    "Equipos de oficina": ["Fotocopiadora/ Impresora", "Escáner", "Multiusos", "Cañones y proyectores", "Otro"],
    "Equipos de fuerza": ["Bomba de agua", "Compresor", "Elevador", "Escaleras eléctricas", "Otro"],
    "Equipos de cómputo": ["Computadora de escritorio", "Laptop", "Otro"],
    "Site de computo": ["Servidores"],
    "Telecomunicaciónes": ["Celular / Smartphone","Teléfono analógico","Teléfono con pantalla", "Teléfono inalámbrico", "Routers Wi-Fi", "Otro"],
    "Equipos médicos": ["Equipos médicos"],
    "Equipos de laboratorio": ["Equipos de laboratorio"],
    "Servicios auxiliares (esterilización, calentadores eléctricos etc)": ["Servicios auxiliares (esterilización, calentadores eléctricos etc)"],
    "Sistemas audiovisuales": ["Televisor LED / LCD", "Televisor de plasma", "Consola de videojuegos", "Equipo de audio / estéreo", 
    "Bocina inteligente (Amazon Echo / Echo Dot, Google Nest Mini, Apple HomePod)", "Servicio de televisión por cable", "Otro"],
    "Equipos de ejercicio y recreativos": ["Caminadora", "Eliptica eléctrica", "Escaladora", "Sillón de masaje", "Otros"],
    "Equipos sanitarios": ["Bomba de agua", "Calentador eléctrico instantaneo", "Calentador eléctrico con deposito", "Resistencia eléctrica", "Otro"],
    "Entretenimiento": ["Televisor LED / LCD", "Televisor de plasma", "Consola de videojuegos", "Equipo de audio / estéreo", 
    "Bocina inteligente (Amazon Echo / Echo Dot, Google Nest Mini, Apple HomePod)", "Servicio de televisión por cable", "Otro"],
    "Otros": ["Otros"]
}

# Consejos completos (mapa subuso -> lista de consejos)
consejos = {

    # --- Iluminación ---
    "Iluminación (Consejos generales)": [
        "Apagar las luces cuando estas no se utilicen.",
        "Aprovechar al máximo la luz natural (ventanas, domos, tragaluces).",
        "Considerar el uso de sensores de presencia, vacancia o timers en pasillos, elevadores, escaleras, baños etc.",
        "Pintar el interior y exterior del inmueble con colores claros ayuda a reflejar la luz evitando el calentamiento excesivo y aumenta la iluminación del interior.",
        "Mantén focos y lámparas limpios para asegurar una cantidad adecuada de luz.",
        "Procura que tus instalaciones cumplan con la NOM-025-STPS-2008, Condiciones de iluminación en los centros de trabajo."
    ],

    "Panel LED": [
        "Elegir focos LED con la temperatura de color adecuada según el uso.",
        "Al adquirir focos y lámparas nuevos, verifica que cuenten con sello de eficiencia energética, el Sello Fide o Energy Star."
    ],

    "Tubo LED T5": [
        "Elegir focos LED con la temperatura de color adecuada según el uso.",
        "Al adquirir focos y lámparas nuevos, verifica que cuenten con sello de eficiencia energética, el Sello Fide o Energy Star."
    ],

    "Tubo LED T8": [
        "Elegir focos LED con la temperatura de color adecuada según el uso.",
        "Al adquirir focos y lámparas nuevos, verifica que cuenten con sello de eficiencia energética, el Sello Fide o Energy Star."
    ],

    "Foco LED": [
        "Elegir focos LED con la temperatura de color adecuada según el uso.",
        "Al adquirir focos y lámparas nuevos, verifica que cuenten con sello de eficiencia energética, el Sello Fide o Energy Star."
    ],

    "Tubo fluorescente T5": [
        "Reemplazar tubos fluorescentes viejos o con balastos electromagnéticos por tubos con balastos electrónicos (más eficientes).",
        "Priorizar el uso de la tecnología más eficiente disponible (LED).",
        "Cuando un foco termine su vida útil o se adquiera una nueva tecnología asegurarse de retirar el balasto de la instalación."
    ],

    "Tubo fluorescente T8": [
        "Reemplazar tubos fluorescentes viejos o con balastos electromagnéticos por tubos con balastos electrónicos (más eficientes).",
        "Priorizar el uso de la tecnología más eficiente disponible (LED).",
        "Cuando un foco termine su vida útil o se adquiera una nueva tecnología asegurarse de retirar el balasto de la instalación."
    ],

    "Fluorescente compacto": [
        "Reemplazar tubos fluorescentes viejos o con balastos electromagnéticos por tubos con balastos electrónicos (más eficientes).",
        "Priorizar el uso de la tecnología más eficiente disponible (LED).",
        "Cuando un foco termine su vida útil o se adquiera una nueva tecnología asegurarse de retirar el balasto de la instalación."
    ],

    "Halógena": [
        "Colocar reflectores o difusores para maximizar la distribución de luz.",
        "Priorizar el uso de la tecnología más eficiente disponible (LED)."
    ],

    "Incandescente": [
        "Priorizar el uso de la tecnología más eficiente disponible (LED)."
    ],


    # --- Acondicionamiento de aire ---
    "Acondicionamiento de aire (Consejos generales)": [
        "Aprovecha al máximo la climatización natural cuando sea posible.",
        "Dales mantenimiento a tus equipos de Acondicionamiento de aire por lo menos 2 veces al año, los equipos con más de 2 años sin mantenimiento suelen consumir el doble de energía",
        "Limpia los filtros de aire por lo menos 1 una vez al mes para mejorar su eficiencia.",
        "Ajusta la temperatura de enfriamiento entre 23 y 25 °C ya que cada grado que bajes consumes un 8% más de energía",
        "Cierra puertas y ventanas para evitar fugas. Se recomienda el uso de burletes.",
        "En regiones secas y cálidas, considera el uso de enfriadores de aire en lugar de acondicionadores de aire.",
        "Se recomienda complementar este servicio con ventiladores de techo o pedestal ya que puede reducir la sensación térmica hasta 2 °C.",
        "Si tu equipo tiene más de 10 años de antigüedad se recomienda considerar la adquisición de un equipo más eficiente.",
        "Si se piensa adquirir un nuevo equipo verificar que tenga la etiqueta amarilla de eficiencia energética, el Sello Fide o Energy Star."
    ],

    "Acondicionamiento de aire residencial (Consejos generales)": [
        "Aprovecha al máximo la climatización natural cuando sea posible.",
        "Dales mantenimiento a tus equipos de Acondicionamiento de aire por lo menos 2 veces al año, los equipos con más de 2 años sin mantenimiento suelen consumir el doble de energía",
        "Limpia los filtros de aire por lo menos 1 una vez al mes para mejorar su eficiencia.",
        "Ajusta la temperatura de enfriamiento entre 23 y 25 °C ya que cada grado que bajes consumes un 8% más de energía",
        "Cierra puertas y ventanas para evitar fugas. Se recomienda el uso de burletes.",
        "En regiones secas y cálidas, considera el uso de enfriadores de aire en lugar de acondicionadores de aire.",
        "Se recomienda complementar este servicio con ventiladores de techo o pedestal ya que puede reducir la sensación térmica hasta 2 °C.",
        "Si tu equipo tiene más de 10 años de antigüedad se recomienda considerar la adquisición de un equipo más eficiente.",
        "Si se piensa adquirir un nuevo equipo verificar que tenga la etiqueta amarilla de eficiencia energética, el Sello Fide o Energy Star."
    ],

    "Acondicionadores de aire tipo cuarto/ventana": [
        "Evita instalarlo en lugares con luz solar directa.",
        "Apaga cuando no haya nadie en la habitación."
    ],

    "Acondicionadores de aire tipo minisplit (convencional)": [
        "Evita configuraciones de temperatura extrema; el sistema ajusta potencia automáticamente.",
        "Usa modos 'Eco' o 'Confort' para minimizar consumo.",
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Acondicionadores de aire tipo minisplit (inverter)": [
        "Programa el encendido y apagado según tus horarios para evitar que el equipo funcione innecesariamente."
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Acondicionadores de aire tipo multisplit": [
        "Usa solo las unidades interiores necesarias.",
        "Ajusta temperaturas similares en todas las unidades encendidas.",
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Acondicionadores de aire tipo dividido/paquete": [
        "Revisa y limpia periódicamente la unidad exterior.",
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],
    "Acondicionadores de aire tipo portatil": [
        "Coloca el equipo cerca de una ventana o salida de aire adecuada.",
        "Mantén el tubo de descarga lo más corto y recto posible para reducir pérdidas de eficiencia.",
        "Apaga el equipo cuando no estés en la habitción."
    ],

    "Acondicionadores de aire tipo dividido (Heat pump)": [
        "Revisa periódicamente que el refrigerante esté en niveles correctos.",
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Acondicionadores de aire tipo dividido (Fan & Coil)": [
        "Evita obstrucciones frente a los difusores de aire.",
        "Controla el flujo de aire según ocupación del espacio."
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Acondicionadores de aire tipo dividido (Split)": [
        "Evita configuraciones de temperatura extrema; el sistema ajusta potencia automáticamente.",
        "Usa modos 'Eco' o 'Confort' para minimizar consumo."
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Acondicionadores de aire tipo dividido (Split inverter)": [
        "Aprovecha su capacidad de modulación para mantener temperatura constante con menor energía.",
        "Evita configuraciones de temperatura extrema; el sistema ajusta potencia automáticamente.",
        "Usa modos 'Eco' o 'Confort' para minimizar consumo."
        "Revisa que todos los ductos y tuberías estén debidamente forrados con aislante térmico."
    ],

    "Sistema de enfriamiento constante o variable (VRV o VRF)": [
        "Optimiza la configuración de flujo de refrigerante y velocidad de ventiladores."
    ],

    "Chiller (condensador enfriado por agua)": [
        "Ajusta temperatura de agua de salida según demanda real.",
        "Usa variadores de velocidad para ventiladores según carga."
    ],

    "Chiller (condensador enfriado por aire)": [
        "Usa variadores de velocidad para ventiladores según carga."
    ],

    "Chiller de Absorción": [
        "Ajusta la carga según demanda real; evitar operar a baja carga por periodos prolongados."
    ],

    "Chiller Modular": [
        "Ajusta el número de módulos en operación según la carga real, evitando mantener módulos innecesarios encendidos."
    ],


    # --- Electrodomésticos ---
    "Electrodomésticos (Consejos generales)": [
        "Apaga y desconecta los electrodomésticos cuando no los utilices.",
        "Asegúrate que cuenten con etiqueta amarilla de eficiencia energética, Sello Fide o Energy Star.",
        "Programa limpieza recurrente o mantenimiento para asegurar buen funcionamiento.",
        "Lee las recomendaciones de uso en el manual del fabricante."
    ],

    "Electrodomésticos residenciales (Consejos generales)": [
        "Apaga y desconecta los electrodomésticos cuando no los utilices.",
        "Asegúrate que cuenten con etiqueta amarilla de eficiencia energética, Sello Fide o Energy Star.",
        "Programa limpieza recurrente o mantenimiento para asegurar buen funcionamiento.",
        "Lee las recomendaciones de uso en el manual del fabricante."
    ],

    "Refrigerador": [
        "Si tienes un refrigerador con más de 10 años de antigüedad considera reemplazarlo con uno nuevo, estos consumen hasta 60% menos electricidad que un modelo anterior del mismo tamaño.",
        "No guardes alimentos calientes.",
        "Evita exponer el refrigerador a fuentes de calor (rayos del sol, estufa, horno etc).",
        "Selecciona la temperatura correcta de operación para conservar los alimentos.",
        "Abre la puerta lo menos posible y ciérrala con rapidez.",
        "Si tu refrigerador tiene parrilla en la parte trasera, límpiala al menos 2 veces al año.",
        "Asegúrate de que los sellos de las puertas estén en buen estado.",
        "Coloca el refrigerador en un lugar fresco y ventilado, dejando un espacio de al menos 10 cm entre el equipo y la pared.",
        "Elige un refrigerador acorde a tus necesidades."
    ],

    "Lavadora 7-15 kg": [
        "Opta por secar la ropa al sol cuando el clima lo permita.",
        "Carga la lavadora con la cantidad de ropa adecuada.",
        "Usa siempre el ciclo más corto posible.",
        "Procura lavar con agua fría.",
        "Cuando sea posible utiliza el ciclo de centrifugado en vez de la secadora.",
        "Compra una secadora que no exceda tus requerimientos."
    ],

    "Lavadora más de 15 kg": [
        "Opta por secar la ropa al sol cuando el clima lo permita.",
        "Carga la lavadora con la cantidad de ropa adecuada.",
        "Usa siempre el ciclo más corto posible.",
        "Procura lavar con agua fría.",
        "Cuando sea posible utiliza el ciclo de centrifugado en vez de la secadora.",
        "Compra una secadora que no exceda tus requerimientos."
    ],

    "Secadora eléctrica": [
        "Procura que la secadora trabaje siempre a carga completa.",
        "Antes de usarla, centrifuga tu ropa en la lavadora.",
        "Limpia periódicamente el filtro de la secadora.",
        "Utiliza el programa 'punto de planchado' si tu secadora cuenta con él.",
        "No uses exceso de detergente en lavadora: genera más humedad y aumenta el tiempo de secado."
    ],

    "Cafetera": [
        "Evita recalentar café ya hecho.",
        "No llenes el equipo con más agua de la necesaria.",
        "Si usas cápsulas individuales, prepara varias tazas seguidas."
    ],

    "Microondas": [
        "Utiliza el microondas para calentar pequeñas cantidades de alimento.",
        "No utilices el microondas para descongelar la comida.",
        "Mantén limpio el microondas ya que los restos de comida y humedad afectan la eficiencia del equipo."
    ],

    "Parrilla o estufa eléctrica": [
        "Precaliéntala solo el tiempo necesario.",
        "Apágala unos minutos antes de terminar de cocinar y que los alimentos se cocinen con el calor residual.",
        "Cocinar con tapa reduce el tiempo de cocción hasta un 30%.",
        "Usa olla de presión cuando sea posible."
    ],

    "Horno eléctrico": [
        "Evita abrir la puerta durante la cocción ya que esto aumenta el tiempo de calentamiento en un 30%.",
        "Apaga el horno 5–10 minutos antes de terminar.",
        "Usa moldes del tamaño adecuado."
    ],

    "Purificador de aire": [
        "Cierra puertas y ventanas mientras está funcionando.",
        "Evita colocarlo junto a fuentes de calor o humedad.",
        "Ubícalo en el centro o en un punto con buena circulación de aire."
    ],

    "Plancha": [
        "No la dejes encendida si interrumpes la actividad.",
        "Precaliéntala solo el tiempo necesario.",
        "Sacude y cuelga la ropa al terminar la lavadora para evitar planchado innecesario."
    ],

    "Licuadora": [
        "Evita sobrecargar la licuadora.",
        "Agrega primero alimentos líquidos.",
        "Evita encender la licuadora sin contenido, esto provoca desgaste del motor y desperdicio de energía."
    ],

    "Aspiradora": [
        "Revisa que las mangueras estén en buenas condiciones.",
        "Utiliza la boquilla adecuada para cada área.",
        "Limpia los filtros al terminar."
    ],

    "Calentador eléctrico instantaneo": [
        "Ajusta el termostato a 45–50 °C.",
        "Aprovecha el agua caliente racionalmente.",
        "Considera la instalación de regaderas ahorradoras."
    ],

    "Calentador eléctrico con deposito": [
        "Ajusta el termostato a 45–50 °C.",
        "Aprovecha el agua caliente racionalmente.",
        "Considera la instalación de regaderas ahorradoras."        
    ],

    "Resistencia eléctrica": [
        "Úsalos solo cuando sea necesario, no como sistema continuo.",
        "No calientes más agua de la necesaria.",
        "Evita mantener el recipiente destapado (aumenta pérdidas de calor)."
    ],

    "Lavavajillas": [
        "Enciende el lavavajillas solo cuando esté totalmente lleno, aprovechando al máximo cada ciclo.",
        "Retira los restos de comida grandes con una espatula o papel pero no con agua.",
        "Programa el lavavajillas para funcionar en horarios de bajo costo eléctrico (horas valle).",
        "Si tu equipo lo permite, usa el secado por aire natural (abre la puerta al terminar el ciclo)."        
    ],

    # --- Equipos de oficina ---
    "Equipos de Oficina (Consejos generales)": [
        "Apaga y desconecta los equipos cuando no se utilicen.",
        "Asegúrate que cuenten con etiqueta amarilla de eficiencia energética.",
        "Programa mantenimiento periódico.",
        "Lee las recomendaciones de uso en el manual del fabricante."
    ],

    "Fotocopiadora/ Impresora": [
        "Activa el modo 'ahorro de energía' o 'sleep mode'.",
        "Haz copias o impresiones por lotes.",
        "Aprovecha la función dúplex."
    ],

    "Escáner": [
        "Usa resoluciones adecuadas (DPI).",
        "Activa el modo suspensión."
    ],

    "Multiusos": [
        "Activa los modos de ahorro.",
        "Usa resoluciones adecuadas (DPI).",
        "Imprime por lotes."
    ],

    "Ventilador de techo": [
        "Refresca naturalmente antes de encenderlo.",
        "Utilízalo en velocidad media-baja.",
        "Colócalo donde haya flujo natural de aire."
    ],

    "Cañones y proyectores": [
        "Usa brillo y contraste adecuados.",
        "Atenuar la iluminación permite usar modo de bajo brillo."
    ],

    # --- Equipos de fuerza ---
    "Equipos de fuerza (Consejos generales)": [
        "Verificar que los motores cumplan con las Normas Oficiales Mexicanas de eficiencia.",
        "Evita el sobredimensionamiento.",
        "Realiza mantenimiento periódico."
    ],

    "Bomba de agua": [
        "Evita operar con válvulas parcialmente cerradas.",
        "Verifica que el sistema no presente fugas.",
        "Evita arranques y paros frecuentes, aumentan el consumo y el desgaste del motor.",
        "Se suguiere programagar su uso en horarios con menor demanda de corriente. (horas valle)" 
    ],

    "Compresor": [
        "Ajusta la presión a la mínima necesaria, cada 1 bar (14.5 psi) extra de presión incrementa el consumo eléctrico 6–8%.",
        "Verifica que el sistema no presente fugas.",
        "Evita arranques y paros frecuentes, aumentan el consumo y el desgaste del motor.",
        "Cambia filtros periódicamente."
    ],

    "Elevador": [
        "Promueve el uso de escaleras en trayectos cortos menores a 3 pisos.",
        "Evita sobrecargar la cabina."
    ],

    "Escaleras eléctricas": [
        "Evita sobrecargar la escalera.",
        "Implementa sensores de presencia o velocidad variable.",
        "Lubrica cadenas y rodillos.",
        "Verifica tensión de correas."
    ],

    # --- Computadoras ---
    "Equipos de cómputo (Consejos generales)": [
        "Activa los modos de ahorro de energía.",
        "Evita brillo máximo.",
        "Desconecta periféricos innecesarios.",
        "Elige pantallas LED eficientes.",
        "Lee las recomendaciones de uso en el manual del fabricante."
    ],

    "Computadora de escritorio": [
        "Apaga y desconecta si no se usará por más de 2 horas.",
        "Evita protectores de pantalla animados."
    ],

    "Laptop": [
        "Evita suspender: apaga completamente al final de la jornada.",
        "Desconecta el cargador cuando la batería esté completa.",
        "Apaga la retroiluminación del teclado si no es necesaria."
    ],

    # --- Entretenimiento ---
    "Entretenimiento (Consejos generales)": [
        "Apaga y desconecta los equipos cuando no se utilicen.",
        "Al no ser equipos criticos se recomienda utilizarlos con moderación.",
        "Utiliza un volumen moderado para prolonga la vida de los amplificadores y reducir el consumo eléctrico.",
        "Ubica los equipos lejos de fuentes de calor o radiación solar directa.",
        "Mantén limpios los equipos y sus filtros o rejillas de ventilación.",
        "Lee las recomendaciones de uso en el manual del fabricante."
    ],

    "Televisor LED / LCD": [
        "Evita reproducir contenido solo como fondo si no se está visualizando.",
        "Ajusta el brillo y contraste ya que un nivel moderado reduce el consumo hasta un 20 %.",
        "En caso de tener más de dos televisores reúne a los miembros de la familia cuando quieran ver el mismo contenido."
    ],

    "Televisor de plasma": [
        "Evita reproducir contenido solo como fondo si no se está visualizando.",
        "Ajusta el brillo y contraste ya que un nivel moderado reduce el consumo hasta un 20 %.",
        "En caso de tener más de dos televisores reúne a los miembros de la familia cuando quieran ver el mismo contenido.",
        "Si está considerando adquirir un nuevo equipo opte por un televisor con pantalla LED / LCD."
    ],

    "Consola de videojuegos": [
        "Ajustar calidad de gráficos y frecuencia de actualización reduce consumo de energía y temperatura.",
        "Evita jugar con todos los periféricos conectados innecesariamente."
    ]
}

# Referencia más cómoda
sankey_data = st.session_state["sankey_data"]

# ------------------------
# FUNCIONES AUXILIARES
# ------------------------

def calcular_tr_desde_m2(m2: float) -> float:
    """Calcula TR estimada a partir de m2 usando la fórmula provista."""
    return (0.00009 * m2**3) - (0.0025 * m2**2) + (0.0628 * m2) + 0.4053

def kwh_mes_desde_potencia(pot_w: float, num_equipos: int, horas_dia: float, factor_mensual: float) -> float:
    """Calcula kWh/mes desde potencia en W por equipo."""
    return round((pot_w / 1000) * num_equipos * horas_dia * factor_mensual, 2)

def pot_w_por_tr(toneladas: float, COP: float) -> float:
    """Calcula potencia (W) a partir de TR y COP (1 TR = 3517 W térmicos aprox)."""
    return (toneladas * 3517) / COP

def agregar_subuso_seleccionado(subuso_label: str):
    """Almacena subusos seleccionados en session_state para mostrar consejos dinámicos."""
    if "subusos_seleccionados" not in st.session_state:
        st.session_state["subusos_seleccionados"] = []  # inicializamos como lista
    if subuso_label not in st.session_state["subusos_seleccionados"]:
        st.session_state["subusos_seleccionados"].append(subuso_label)

# ------------------------
# Función auxiliar para calcular kWh/mes
# ------------------------
def calcular_kwh_mes(potencia_w, num_equipos=1, horas=8, factor_mensual=21, continuo=False):
    """
    Calcula kWh/mes para un equipo.
    - potencia_w: potencia en W
    - num_equipos: número de equipos
    - horas: horas/día (se ignora si continuo=True)
    - factor_mensual: factor días de operación al mes
    - continuo: si True, asume equipo siempre conectado 24h × 30 días (720 h/mes)
    """
    if continuo:
        kwh = (potencia_w / 1000) * num_equipos * 24 * 30  # 720 h/mes
    else:
        kwh = (potencia_w / 1000) * num_equipos * horas * factor_mensual
    return round(kwh, 2)

# ------------------------
# INTERFAZ: PESTAÑAS
# ------------------------

tab_oficina, tab_salud, tab_otros, tab_residencial, tab_consejos = st.tabs(["🏢 Oficina", "🏥 Salud", "🏦 Otros usos", "🏘️ Residencial", "💡 Consejos"])

# Parámetros comunes (días de operación por semana -> factor mensual aproximado)

LOGOCONUEE = "https://upload.wikimedia.org/wikipedia/commons/d/d3/CONUEE_Logo.png"
LINK = "https://www.gob.mx/conuee"

with st.sidebar:
    st.markdown(
        f'<a href="{LINK}" target="_blank">'
        f'<img src="{LOGOCONUEE}" alt="CONUEE" style="width:100%;">'
        '</a>',
        unsafe_allow_html=True
    )
    # ------------------------
    # CONFIGURACIÓN DEL INMUEBLE (nuevo)
    # ------------------------
    modo_calculo = st.radio(
        "¿Cómo deseas contabilizar el consumo del inmueble?",
        ["Global (todo el edificio)", "Por piso"],
        index=0,
        key="modo_calculo"
    )

    #st.markdown("### Parámetros globales")
    dias_semana = st.slider("Días de operación por semana:", 1, 7, 5)
    #st.markdown("### Para Inmuebles Residenciales Selecciona 7 días")
    factor_mensual = round(dias_semana * 4.287, 3)
    #st.caption(f"Factor mensual usado: {factor_mensual} (días/semana × 4.287)")

# ------------------------
# Pestaña Oficina
# ------------------------
with tab_oficina:
    st.header("🏢 Oficina — entrada de equipos y servicios")
    
    # ------------------------
    # MODO GLOBAL
    # ------------------------
    if modo_calculo == "Global (todo el edificio)":
        usos = usos_por_inmueble["Oficina"]
        usos_seleccionados = st.multiselect("Selecciona los usos de Oficina:", usos, key="oficina_usos")

        for uso in usos_seleccionados:
            st.subheader(uso)
            if uso in subusos:
                for sub in subusos[uso]:
                    key_base = f"of_{uso}_{sub}"
                    marcado = st.checkbox(f"{sub}", key=key_base)
                    if marcado:
                        agregar_subuso_seleccionado(sub)

                        # --- CASO 1: Aire acondicionado ---
                        if uso == "Acondicionamiento de aire" and sub in cop_data:
                            num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            antig = st.selectbox("Antigüedad:", ["nuevo", "5-10 años", "+10 años"], key=f"{key_base}_ant")
                            toneladas = st.number_input("Toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=1.0, key=f"{key_base}_ton")
                            horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            COP = cop_data[sub][antig]
                            pot_w = pot_w_por_tr(toneladas, COP)
                            kwh_mes = kwh_mes_desde_potencia(pot_w, num_eq, horas, factor_mensual)
                            st.session_state["sankey_data"].append({
                                "origen": "Energía eléctrica",
                                "uso": uso,
                                "subuso": sub,
                                "valor": kwh_mes
                            })

                        # --- CASO 2: Subuso "Otros" ---
                        elif sub in ["Otros", "Otro"]:
                            otros_equipos = st.session_state.get(f"{key_base}_otros", [])
                            agregar = st.button(f"➕ Agregar equipo a {uso} ({sub})", key=f"{key_base}_add")

                            if agregar:
                                otros_equipos.append({"nombre": "", "potencia": 0, "horas": 8})
                                st.session_state[f"{key_base}_otros"] = otros_equipos
                                st.rerun()

                            for i, equipo in enumerate(otros_equipos):
                                with st.expander(f"⚙️ Equipo {i+1} — {equipo.get('nombre','(sin nombre)')}", expanded=True):
                                    cols = st.columns([3, 1])
                                    with cols[0]:
                                        nombre = st.text_input("Nombre del equipo:", value=equipo["nombre"], key=f"{key_base}_nombre_{i}")
                                    with cols[1]:
                                        eliminar = st.button("🗑️ Eliminar", key=f"{key_base}_del_{i}")

                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num_{i}")
                                    potencia = st.number_input("Potencia (W):", min_value=0, max_value=50000, value=equipo.get("potencia", 100), key=f"{key_base}_pot_{i}")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=float(equipo.get("horas", 8.0)), step=1.0, key=f"{key_base}_hr_{i}")

                                    otros_equipos[i] = {"nombre": nombre, "potencia": potencia, "horas": horas}
                                    st.session_state[f"{key_base}_otros"] = otros_equipos

                                    kwh_mes = round(potencia / 1000 * horas * num_eq * factor_mensual, 2)
                                    nuevo_registro = {
                                        "origen": "Energía eléctrica",
                                        "uso": uso,
                                        "subuso": nombre or sub,
                                        "valor": kwh_mes
                                    }
                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)
                                    if eliminar:
                                        otros_equipos.pop(i)
                                        st.session_state[f"{key_base}_otros"] = otros_equipos
                                        st.rerun()

                        # --- CASO 3: Equipos normales ---
                        else:
                            num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")

                            if sub in equipos_continuos:
                                horas = 24
                                st.info("⏱️ Este equipo es de uso continuo.")
                            else:
                                horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            potencia = potencias_nominales.get(sub)
                            if potencia is None:
                                potencia = st.number_input(
                                    f"Potencia (W) ({sub}), si no la conoces revisa la etiqueta del equipo (W=V*A)",
                                    0, 50000, 200, key=f"{key_base}_pot"
                                )

                            kwh_mes = calcular_kwh_mes(
                                potencia_w=potencia,
                                num_equipos=num_equipos,
                                horas=horas,
                                factor_mensual=factor_mensual,
                                continuo=(sub in equipos_continuos)
                            )
                            nuevo_registro = {
                                "origen": "Energía eléctrica",
                                "uso": uso,
                                "subuso": sub,
                                "valor": kwh_mes
                            }
                            if nuevo_registro not in st.session_state["sankey_data"]:
                                st.session_state["sankey_data"].append(nuevo_registro)

    # ------------------------
    # MODO POR PISO
    # ------------------------
    elif modo_calculo == "Por piso":
        st.subheader("🏢 Cálculo de consumo por piso — Oficina")

        num_pisos = st.number_input(
            "Número de pisos del inmueble:",
            min_value=1, step=1, value=1, key="oficina_pisos"
        )

        for piso in range(1, num_pisos + 1):
            with st.expander(f"Piso {piso}", expanded=(piso == 1)):
                usos = usos_por_inmueble["Oficina"]
                usos_sel = st.multiselect(f"Selecciona los usos en Piso {piso}:", usos, key=f"of_usos_piso_{piso}")

                for uso in usos_sel:
                    st.subheader(f"{uso} (Piso {piso})")

                    if uso in subusos:
                        for sub in subusos[uso]:
                            key_base = f"of_p{piso}_{uso}_{sub}"
                            marcado = st.checkbox(sub, key=f"{key_base}_check")
                            if marcado:
                                agregar_subuso_seleccionado(sub)

                                # --- Aire acondicionado ---
                                if uso == "Acondicionamiento de aire" and sub in cop_data:
                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    antig = st.selectbox("Antigüedad:", ["nuevo", "5-10 años", "+10 años"], key=f"{key_base}_ant")
                                    toneladas = st.number_input("Toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=1.0, key=f"{key_base}_ton")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")
                                    COP = cop_data[sub][antig]
                                    pot_w = pot_w_por_tr(toneladas, COP)
                                    kwh_mes = kwh_mes_desde_potencia(pot_w, num_eq, horas, factor_mensual)
                                    st.session_state["sankey_data"].append({
                                        "origen": "Energía eléctrica",
                                        "piso": f"Piso {piso}",
                                        "uso": uso,
                                        "subuso": sub,
                                        "valor": kwh_mes
                                    })

                                # --- Equipos normales / otros ---
                                else:
                                    num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")

                                    if sub in equipos_continuos:
                                        horas = 24
                                        st.info("⏱️ Este equipo es de uso continuo.")
                                    else:
                                        horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                                    potencia = potencias_nominales.get(sub)
                                    if potencia is None:
                                        potencia = st.number_input(
                                            f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot"
                                        )

                                    kwh_mes = calcular_kwh_mes(
                                        potencia_w=potencia,
                                        num_equipos=num_equipos,
                                        horas=horas,
                                        factor_mensual=factor_mensual,
                                        continuo=(sub in equipos_continuos)
                                    )

                                    nuevo_registro = {
                                        "origen": "Energía eléctrica",
                                        "piso": f"Piso {piso}",
                                        "uso": uso,
                                        "subuso": sub,
                                        "valor": kwh_mes
                                    }

                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

        st.success("✅ Cálculo completado por piso. Puedes ver el diagrama Sankey más abajo.")

# ------------------------
# Pestaña Salud
# ------------------------
with tab_salud:
    st.header("🏥 Salud — entrada de equipos y servicios")

    # ------------------------
    # MODO GLOBAL
    # ------------------------
    if modo_calculo == "Global (todo el edificio)":
        usos = usos_por_inmueble["Salud"]
        usos_seleccionados = st.multiselect("Selecciona los usos de Salud:", usos, key="salud_usos")

        for uso in usos_seleccionados:
            st.subheader(uso)
            if uso in subusos:
                for sub in subusos[uso]:
                    key_base = f"sal_{uso}_{sub}"
                    marcado = st.checkbox(f"{sub}", key=key_base)
                    if marcado:
                        agregar_subuso_seleccionado(sub)

                        # --- CASO 1: Aire acondicionado ---
                        if uso == "Acondicionamiento de aire" and sub in cop_data:
                            num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            antig = st.selectbox("Antigüedad:", ["nuevo", "5-10 años", "+10 años"], key=f"{key_base}_ant")
                            toneladas = st.number_input("Toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=1.0, key=f"{key_base}_ton")
                            horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            COP = cop_data[sub][antig]
                            pot_w = pot_w_por_tr(toneladas, COP)
                            kwh_mes = kwh_mes_desde_potencia(pot_w, num_eq, horas, factor_mensual)
                            st.session_state["sankey_data"].append({
                                "origen": "Energía eléctrica",
                                "uso": uso,
                                "subuso": sub,
                                "valor": kwh_mes
                            })

                        # --- CASO 2: Subuso “Otros / libre ingreso” ---
                        elif sub in ["Otros", "Otro", "Equipos médicos", "Equipos de laboratorio", "Servicios auxiliares (esterilización, calentadores eléctricos etc)"]:
                            otros_equipos = st.session_state.get(f"{key_base}_otros", [])
                            agregar = st.button(f"➕ Agregar equipo a {uso} ({sub})", key=f"{key_base}_add")
                            if agregar:
                                otros_equipos.append({"nombre": "", "potencia": 0, "horas": 8})
                                st.session_state[f"{key_base}_otros"] = otros_equipos
                                st.rerun()

                            for i, equipo in enumerate(otros_equipos):
                                with st.expander(f"⚙️ Equipo {i+1} — {equipo.get('nombre','(sin nombre)')}", expanded=True):
                                    cols = st.columns([3, 1])
                                    with cols[0]:
                                        nombre = st.text_input("Nombre del equipo:", value=equipo["nombre"], key=f"{key_base}_nombre_{i}")
                                    with cols[1]:
                                        eliminar = st.button("🗑️ Eliminar", key=f"{key_base}_del_{i}")

                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num_{i}")
                                    potencia = st.number_input("Potencia (W):", min_value=0, max_value=50000, value=equipo.get("potencia", 100), key=f"{key_base}_pot_{i}")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=float(equipo.get("horas", 8.0)), step=1.0, key=f"{key_base}_hr_{i}")

                                    otros_equipos[i] = {"nombre": nombre, "potencia": potencia, "horas": horas}
                                    st.session_state[f"{key_base}_otros"] = otros_equipos

                                    kwh_mes = round(potencia / 1000 * horas * factor_mensual, 2)
                                    nuevo_registro = {"origen": "Energía eléctrica", "uso": uso, "subuso": nombre or sub, "valor": kwh_mes}
                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

                                    if eliminar:
                                        otros_equipos.pop(i)
                                        st.session_state[f"{key_base}_otros"] = otros_equipos
                                        st.rerun()

                        # --- CASO 3: Equipos normales ---
                        else:
                            num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            if sub in equipos_continuos:
                                horas = 24
                                st.info("⏱️ Este equipo es de uso continuo.")
                            else:
                                horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            potencia = potencias_nominales.get(sub)
                            if potencia is None:
                                potencia = st.number_input(f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot")

                            kwh_mes = calcular_kwh_mes(potencia_w=potencia, num_equipos=num_equipos, horas=horas, factor_mensual=factor_mensual, continuo=(sub in equipos_continuos))
                            nuevo_registro = {"origen": "Energía eléctrica", "uso": uso, "subuso": sub, "valor": kwh_mes}
                            if nuevo_registro not in st.session_state["sankey_data"]:
                                st.session_state["sankey_data"].append(nuevo_registro)

    # ------------------------
    # MODO POR PISO
    # ------------------------
    elif modo_calculo == "Por piso":
        st.subheader("🏥 Cálculo de consumo por piso — Salud")
        num_pisos = st.number_input("Número de pisos del inmueble:", min_value=1, step=1, value=1, key="salud_pisos")

        for piso in range(1, num_pisos + 1):
            with st.expander(f"Piso {piso}", expanded=(piso == 1)):
                usos = usos_por_inmueble["Salud"]
                usos_sel = st.multiselect(f"Selecciona los usos en Piso {piso}:", usos, key=f"sal_usos_piso_{piso}")

                for uso in usos_sel:
                    st.subheader(f"{uso} (Piso {piso})")

                    if uso in subusos:
                        for sub in subusos[uso]:
                            key_base = f"sal_p{piso}_{uso}_{sub}"
                            marcado = st.checkbox(sub, key=f"{key_base}_check")
                            if marcado:
                                agregar_subuso_seleccionado(sub)

                                # --- Aire acondicionado ---
                                if uso == "Acondicionamiento de aire" and sub in cop_data:
                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    antig = st.selectbox("Antigüedad:", ["nuevo", "5-10 años", "+10 años"], key=f"{key_base}_ant")
                                    toneladas = st.number_input("Toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=1.0, key=f"{key_base}_ton")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                                    COP = cop_data[sub][antig]
                                    pot_w = pot_w_por_tr(toneladas, COP)
                                    kwh_mes = kwh_mes_desde_potencia(pot_w, num_eq, horas, factor_mensual)

                                    st.session_state["sankey_data"].append({
                                        "origen": "Energía eléctrica",
                                        "piso": f"Piso {piso}",
                                        "uso": uso,
                                        "subuso": sub,
                                        "valor": kwh_mes
                                    })

                                # --- Equipos normales / otros ---
                                else:
                                    num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    if sub in equipos_continuos:
                                        horas = 24
                                        st.info("⏱️ Este equipo permanece conectado las 24 horas del día.")
                                    else:
                                        horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                                    potencia = potencias_nominales.get(sub)
                                    if potencia is None:
                                        potencia = st.number_input(f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot")

                                    kwh_mes = calcular_kwh_mes(potencia_w=potencia, num_equipos=num_equipos, horas=horas, factor_mensual=factor_mensual, continuo=(sub in equipos_continuos))
                                    nuevo_registro = {
                                        "origen": "Energía eléctrica",
                                        "piso": f"Piso {piso}",
                                        "uso": uso,
                                        "subuso": sub,
                                        "valor": kwh_mes
                                    }

                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

        st.success("✅ Cálculo completado por piso. Puedes ver el diagrama Sankey más abajo.")

# ------------------------
# Pestaña Otros usos
# ------------------------
with tab_otros:
    st.header("🏦 Otros usos — entrada de equipos y servicios")

    # ------------------------
    # MODO GLOBAL
    # ------------------------
    if modo_calculo == "Global (todo el edificio)":
        usos = usos_por_inmueble["Otros usos"]
        usos_seleccionados = st.multiselect("Selecciona los usos de Otros:", usos, key="otros_usos")

        for uso in usos_seleccionados:
            st.subheader(uso)
            if uso in subusos:
                for sub in subusos[uso]:
                    key_base = f"otr_{uso}_{sub}"
                    marcado = st.checkbox(f"{sub}", key=key_base)
                    if marcado:
                        agregar_subuso_seleccionado(sub)

                        # --- CASO 1: Aire acondicionado ---
                        if uso == "Acondicionamiento de aire" and sub in cop_data:
                            num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            antig = st.selectbox("Antigüedad:", ["nuevo", "5-10 años", "+10 años"], key=f"{key_base}_ant")
                            toneladas = st.number_input("Toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=0.5, key=f"{key_base}_ton")
                            horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            COP = cop_data[sub][antig]
                            pot_w = pot_w_por_tr(toneladas, COP)
                            kwh_mes = kwh_mes_desde_potencia(pot_w, num_eq, horas, factor_mensual)

                            st.session_state["sankey_data"].append({
                                "origen": "Energía eléctrica",
                                "uso": uso,
                                "subuso": sub,
                                "valor": kwh_mes
                            })

                        # --- CASO 2: Subuso “Otros / libre ingreso” ---
                        elif sub in ["Otros", "Otro"]:
                            otros_equipos = st.session_state.get(f"{key_base}_otros", [])
                            agregar = st.button(f"➕ Agregar equipo a {uso} ({sub})", key=f"{key_base}_add")
                            if agregar:
                                otros_equipos.append({"nombre": "", "potencia": 0, "horas": 8})
                                st.session_state[f"{key_base}_otros"] = otros_equipos
                                st.rerun()

                            for i, equipo in enumerate(otros_equipos):
                                with st.expander(f"⚙️ Equipo {i+1} — {equipo.get('nombre','(sin nombre)')}", expanded=True):
                                    cols = st.columns([3, 1])
                                    with cols[0]:
                                        nombre = st.text_input("Nombre del equipo:", value=equipo["nombre"], key=f"{key_base}_nombre_{i}")
                                    with cols[1]:
                                        eliminar = st.button("🗑️ Eliminar", key=f"{key_base}_del_{i}")

                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num_{i}")
                                    potencia = st.number_input("Potencia (W):", min_value=0, max_value=50000, value=equipo.get("potencia", 100), key=f"{key_base}_pot_{i}")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=float(equipo.get("horas", 8.0)), step=1.0, key=f"{key_base}_hr_{i}")

                                    otros_equipos[i] = {"nombre": nombre, "potencia": potencia, "horas": horas}
                                    st.session_state[f"{key_base}_otros"] = otros_equipos

                                    kwh_mes = round(potencia / 1000 * horas * factor_mensual, 2)
                                    nuevo_registro = {"origen": "Energía eléctrica", "uso": uso, "subuso": nombre or sub, "valor": kwh_mes}
                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

                                    if eliminar:
                                        otros_equipos.pop(i)
                                        st.session_state[f"{key_base}_otros"] = otros_equipos
                                        st.rerun()

                        # --- CASO 3: Equipos normales ---
                        else:
                            num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            if sub in equipos_continuos:
                                horas = 24
                                st.info("⏱️ Este equipo es de uso continuo.")
                            else:
                                horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            potencia = potencias_nominales.get(sub)
                            if potencia is None:
                                potencia = st.number_input(f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot")

                            kwh_mes = calcular_kwh_mes(potencia_w=potencia, num_equipos=num_equipos, horas=horas, factor_mensual=factor_mensual, continuo=(sub in equipos_continuos))
                            nuevo_registro = {"origen": "Energía eléctrica", "uso": uso, "subuso": sub, "valor": kwh_mes}
                            if nuevo_registro not in st.session_state["sankey_data"]:
                                st.session_state["sankey_data"].append(nuevo_registro)

    # ------------------------
    # MODO POR PISO
    # ------------------------
    elif modo_calculo == "Por piso":
        st.subheader("🏦 Cálculo de consumo por piso — Otros usos")
        num_pisos = st.number_input("Número de pisos del inmueble:", min_value=1, step=1, value=1, key="otros_pisos")

        for piso in range(1, num_pisos + 1):
            with st.expander(f"Piso {piso}", expanded=(piso == 1)):
                usos = usos_por_inmueble["Otros usos"]
                usos_sel = st.multiselect(f"Selecciona los usos en Piso {piso}:", usos, key=f"otr_usos_piso_{piso}")

                for uso in usos_sel:
                    st.subheader(f"{uso} (Piso {piso})")

                    if uso in subusos:
                        for sub in subusos[uso]:
                            key_base = f"otr_p{piso}_{uso}_{sub}"
                            marcado = st.checkbox(sub, key=f"{key_base}_check")
                            if marcado:
                                agregar_subuso_seleccionado(sub)

                                # --- Aire acondicionado ---
                                if uso == "Acondicionamiento de aire" and sub in cop_data:
                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    antig = st.selectbox("Antigüedad:", ["nuevo", "5-10 años", "+10 años"], key=f"{key_base}_ant")
                                    toneladas = st.number_input("Toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=0.5, key=f"{key_base}_ton")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                                    COP = cop_data[sub][antig]
                                    pot_w = pot_w_por_tr(toneladas, COP)
                                    kwh_mes = kwh_mes_desde_potencia(pot_w, num_eq, horas, factor_mensual)

                                    st.session_state["sankey_data"].append({
                                        "origen": "Energía eléctrica",
                                        "piso": f"Piso {piso}",
                                        "uso": uso,
                                        "subuso": sub,
                                        "valor": kwh_mes
                                    })

                                # --- Equipos normales / otros ---
                                else:
                                    num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    if sub in equipos_continuos:
                                        horas = 24
                                        st.info("⏱️ Este equipo es de uso continuo.")
                                    else:
                                        horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                                    potencia = potencias_nominales.get(sub)
                                    if potencia is None:
                                        potencia = st.number_input(f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot")

                                    kwh_mes = calcular_kwh_mes(potencia_w=potencia, num_equipos=num_equipos, horas=horas, factor_mensual=factor_mensual, continuo=(sub in equipos_continuos))
                                    nuevo_registro = {
                                        "origen": "Energía eléctrica",
                                        "piso": f"Piso {piso}",
                                        "uso": uso,
                                        "subuso": sub,
                                        "valor": kwh_mes
                                    }

                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

        st.success("✅ Cálculo completado por piso. Puedes ver el diagrama Sankey más abajo.")

# ------------------------
# Pestaña Residencial (completa)
# ------------------------

# Inicializar session_state para controlar mensaje
if "res_tab_msg_shown" not in st.session_state:
    st.session_state.res_tab_msg_shown = False

with tab_residencial:

    # Mostrar toast solo la primera vez que se selecciona la tab
    if not st.session_state.res_tab_msg_shown:
        st.toast("Para Inmuebles de uso residencial selecciona 7 días de operación.", icon="📌")
        st.session_state.res_tab_msg_shown = True

    st.header("🏘️ Residencial — entrada de equipos y servicios")
    
    # Límites mensuales de consumo por tarifa (kWh/mes)
    limites_tarifa = {
        "1": 250, "1A": 300, "1B": 400, "1C": 850, "1D": 1000, "1E": 2000, "1F": 2500
    } 

    # Selección de tarifa
    tarifa_sel = st.selectbox(
        "Selecciona la tarifa doméstica que aplica a tu vivienda:",
        ["1", "1A", "1B", "1C", "1D", "1E", "1F"],
        index=0
    )
    limite_tarifa = limites_tarifa[tarifa_sel]
    st.markdown("Selecciona los equipos y servicios residenciales que quieras calcular.")

    # Lista de subusos residenciales
    usos_residenciales = ["Iluminación", "Acondicionamiento de aire residencial", "Electrodomésticos residenciales", 
                          "Equipos de cómputo", "Entretenimiento", "Equipos sanitarios", "Otros"]

    # ------------------------
    # MODO GLOBAL
    # ------------------------
    if modo_calculo == "Global (todo el edificio)":
        usos_sel_res = st.multiselect("Selecciona los usos residenciales:", usos_residenciales, key="res_usos_global")

        for uso in usos_sel_res:
            st.subheader(uso)
            if uso in subusos:
                for sub in subusos[uso]:
                    key_base = f"res_{uso}_{sub}"
                    marcado = st.checkbox(f"{sub}", key=key_base)
                    if marcado:
                        agregar_subuso_seleccionado(sub)

                        # --- Acondicionamiento residencial ---
                        if uso == "Acondicionamiento de aire residencial" and sub in cop__data:
                            num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            antiguedad = st.selectbox("Antigüedad del equipo:", ["nuevo", "5-10 años"], key=f"{key_base}_ant")
                            metodo = st.radio("¿Ingresar Toneladas (TR) o metros cuadrados que enfría?", 
                                              ["Toneladas (TR)", "Metros cuadrados (m²)"], key=f"{key_base}_metodo")
                            if metodo == "Toneladas (TR)":
                                toneladas = st.number_input("Ingrese las toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=0.5, key=f"{key_base}_ton")
                            else:
                                m2 = st.number_input("Ingrese los metros cuadrados que enfría:", min_value=1.0, value=10.0, step=1.0, key=f"{key_base}_m2")
                                toneladas = calcular_tr_desde_m2(m2)
                                st.write(f"Toneladas estimadas: **{round(toneladas,2)} TR** (a partir de {m2} m²)")

                            horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")
                            COP = cop__data[sub][antiguedad]
                            pot_w = pot_w_por_tr(toneladas, COP)
                            kwh_mes = kwh_mes_desde_potencia(pot_w, num_equipos, horas, factor_mensual)
                            st.session_state["sankey_data"].append({"origen": "Energía eléctrica", "uso": uso, "subuso": sub, "valor": kwh_mes})

                        # --- Subuso "Otros" / ingreso libre ---
                        elif sub in ["Otros", "Otro"]:
                            otros_equipos = st.session_state.get(f"{key_base}_otros", [])
                            agregar = st.button(f"➕ Agregar equipo a {uso} ({sub})", key=f"{key_base}_add")
                            if agregar:
                                otros_equipos.append({"nombre": "", "potencia": 0, "horas": 8})
                                st.session_state[f"{key_base}_otros"] = otros_equipos
                                st.rerun()

                            for i, equipo in enumerate(otros_equipos):
                                with st.expander(f"⚙️ Equipo {i+1} — {equipo.get('nombre','(sin nombre)')}", expanded=True):
                                    cols = st.columns([3, 1])
                                    with cols[0]:
                                        nombre = st.text_input("Nombre del equipo:", value=equipo["nombre"], key=f"{key_base}_nombre_{i}")
                                    with cols[1]:
                                        eliminar = st.button("🗑️ Eliminar", key=f"{key_base}_del_{i}")

                                    num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num_{i}")
                                    potencia = st.number_input("Potencia (W):", min_value=0, max_value=50000, value=equipo.get("potencia", 100), key=f"{key_base}_pot_{i}")
                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=float(equipo.get("horas", 8.0)), step=1.0, key=f"{key_base}_hr_{i}")

                                    otros_equipos[i] = {"nombre": nombre, "potencia": potencia, "horas": horas}
                                    st.session_state[f"{key_base}_otros"] = otros_equipos

                                    kwh_mes = round(potencia / 1000 * horas * factor_mensual, 2)
                                    nuevo_registro = {"origen": "Energía eléctrica", "uso": uso, "subuso": nombre or sub, "valor": kwh_mes}
                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

                                    if eliminar:
                                        otros_equipos.pop(i)
                                        st.session_state[f"{key_base}_otros"] = otros_equipos
                                        st.rerun()

                        # --- Equipos normales ---
                        else:
                            num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                            if sub in equipos_continuos:
                                horas = 24
                                st.info("⏱️ Este equipo es de uso continuo.")
                            else:
                                horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                            potencia = potencias_nominales.get(sub)
                            if potencia is None:
                                potencia = st.number_input(f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot")

                            kwh_mes = calcular_kwh_mes(potencia_w=potencia, num_equipos=num_equipos, horas=horas, factor_mensual=factor_mensual, continuo=(sub in equipos_continuos))
                            nuevo_registro = {"origen": "Energía eléctrica", "uso": uso, "subuso": sub, "valor": kwh_mes}
                            if nuevo_registro not in st.session_state["sankey_data"]:
                                st.session_state["sankey_data"].append(nuevo_registro)

    # ------------------------
    # MODO POR PISO
    # ------------------------
    elif modo_calculo == "Por piso":
        st.subheader("🏘️ Cálculo de consumo por piso — Residencial")
        num_pisos = st.number_input("Número de pisos del inmueble:", min_value=1, step=1, value=1, key="res_pisos")

        for piso in range(1, num_pisos + 1):
            with st.expander(f"Piso {piso}", expanded=(piso == 1)):
                usos_sel_res = st.multiselect(f"Selecciona los usos residenciales en Piso {piso}:", usos_residenciales, key=f"res_usos_piso_{piso}")

                for uso in usos_sel_res:
                    st.subheader(f"{uso} (Piso {piso})")
                    if uso in subusos:
                        for sub in subusos[uso]:
                            key_base = f"res_p{piso}_{uso}_{sub}"
                            marcado = st.checkbox(sub, key=f"{key_base}_check")
                            if marcado:
                                agregar_subuso_seleccionado(sub)

                                # --- Acondicionamiento residencial ---
                                if uso == "Acondicionamiento de aire residencial" and sub in cop__data:
                                    num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    antiguedad = st.selectbox("Antigüedad del equipo:", ["nuevo", "5-10 años"], key=f"{key_base}_ant")
                                    metodo = st.radio("¿Ingresar Toneladas (TR) o metros cuadrados que enfría?", 
                                                      ["Toneladas (TR)", "Metros cuadrados (m²)"], key=f"{key_base}_metodo")
                                    if metodo == "Toneladas (TR)":
                                        toneladas = st.number_input("Ingrese las toneladas de refrigeración (TR):", min_value=0.1, value=1.0, step=0.5, key=f"{key_base}_ton")
                                    else:
                                        m2 = st.number_input("Ingrese los metros cuadrados que enfría:", min_value=1.0, value=10.0, step=1.0, key=f"{key_base}_m2")
                                        toneladas = calcular_tr_desde_m2(m2)
                                        st.write(f"Toneladas estimadas: **{round(toneladas,2)} TR** (a partir de {m2} m²)")

                                    horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")
                                    COP = cop__data[sub][antiguedad]
                                    pot_w = pot_w_por_tr(toneladas, COP)
                                    kwh_mes = kwh_mes_desde_potencia(pot_w, num_equipos, horas, factor_mensual)
                                    st.session_state["sankey_data"].append({"origen": "Energía eléctrica", "piso": f"Piso {piso}", "uso": uso, "subuso": sub, "valor": kwh_mes})

                                # --- Subuso “Otros” / ingreso libre ---
                                elif sub in ["Otros", "Otro"]:
                                    otros_equipos = st.session_state.get(f"{key_base}_otros", [])
                                    agregar = st.button(f"➕ Agregar equipo a {uso} ({sub})", key=f"{key_base}_add")
                                    if agregar:
                                        otros_equipos.append({"nombre": "", "potencia": 0, "horas": 8})
                                        st.session_state[f"{key_base}_otros"] = otros_equipos
                                        st.rerun()

                                    for i, equipo in enumerate(otros_equipos):
                                        with st.expander(f"⚙️ Equipo {i+1} — {equipo.get('nombre','(sin nombre)')}", expanded=True):
                                            cols = st.columns([3, 1])
                                            with cols[0]:
                                                nombre = st.text_input("Nombre del equipo:", value=equipo["nombre"], key=f"{key_base}_nombre_{i}")
                                            with cols[1]:
                                                eliminar = st.button("🗑️ Eliminar", key=f"{key_base}_del_{i}")

                                            num_eq = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num_{i}")
                                            potencia = st.number_input("Potencia (W):", min_value=0, max_value=50000, value=equipo.get("potencia", 100), key=f"{key_base}_pot_{i}")
                                            horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=float(equipo.get("horas", 8.0)), step=1.0, key=f"{key_base}_hr_{i}")

                                            otros_equipos[i] = {"nombre": nombre, "potencia": potencia, "horas": horas}
                                            st.session_state[f"{key_base}_otros"] = otros_equipos

                                            kwh_mes = round(potencia / 1000 * horas * factor_mensual, 2)
                                            nuevo_registro = {"origen": "Energía eléctrica", "piso": f"Piso {piso}", "uso": uso, "subuso": nombre or sub, "valor": kwh_mes}
                                            if nuevo_registro not in st.session_state["sankey_data"]:
                                                st.session_state["sankey_data"].append(nuevo_registro)

                                            if eliminar:
                                                otros_equipos.pop(i)
                                                st.session_state[f"{key_base}_otros"] = otros_equipos
                                                st.rerun()

                                # --- Equipos normales ---
                                else:
                                    num_equipos = st.number_input(f"N° equipos ({sub})", min_value=1, step=1, key=f"{key_base}_num")
                                    if sub in equipos_continuos:
                                        horas = 24
                                        st.info("⏱️ Este equipo es de uso continuo.")
                                    else:
                                        horas = st.number_input("Horas/día:", min_value=0.1, max_value=24.0, value=8.0, step=1.0, key=f"{key_base}_hr")

                                    potencia = potencias_nominales.get(sub)
                                    if potencia is None:
                                        potencia = st.number_input(f"Potencia (W) ({sub})", 0, 50000, 200, key=f"{key_base}_pot")

                                    kwh_mes = calcular_kwh_mes(potencia_w=potencia, num_equipos=num_equipos, horas=horas, factor_mensual=factor_mensual, continuo=(sub in equipos_continuos))
                                    nuevo_registro = {"origen": "Energía eléctrica", "piso": f"Piso {piso}", "uso": uso, "subuso": sub, "valor": kwh_mes}
                                    if nuevo_registro not in st.session_state["sankey_data"]:
                                        st.session_state["sankey_data"].append(nuevo_registro)

        st.success("✅ Cálculo completado por piso. Puedes ver el diagrama Sankey más abajo.")

# ------------------------
# Evaluación de consumo contra la tarifa
# ------------------------
# Obtener el total residencial calculado
#sankey_data = st.session_state.get("sankey_data", [])
    total_residencial = sum(item["valor"] for item in sankey_data if item["uso"] in usos_residenciales)

    limite = limites_tarifa[tarifa_sel]
    porcentaje_res = total_residencial / limite * 100

# Crear barra de progreso estilo texto
    total_bloques = 20
    bloques_llenos = int(total_bloques * porcentaje_res / 100)
    barra = "█" * bloques_llenos + "░" * (total_bloques - bloques_llenos)

# Mostrar barra con porcentaje
    st.text(f"[{barra}] {porcentaje_res:.0f}% del límite de la tarifa {tarifa_sel}")


# Advertencias basadas en límite de tarifa
    if total_residencial > limite_tarifa:
        st.error("🚨 *Has excedido el límite de tu tarifa.* Podrías estar **en riesgo de pasar a Tarifa DAC**, donde el costo por kWh es mucho más alto.")
    elif total_residencial >= limite_tarifa - 10:
        st.warning("⚠️ *Te recomendamos moderar tu consumo de energía eléctrica* ya que estás **peligrosamente cerca** de cambiar a Tarifa DAC.")
    else:
        st.success("✅ Tu consumo está dentro del rango seguro para tu tarifa.")

# ------------------------
# Pestaña Consejos (dinámica)
# ------------------------
with tab_consejos:
    st.header("💡 Consejos de Eficiencia Energética")

    # Reunir todos los usos seleccionados (de cualquier pestaña)
    usos = []
    for key in st.session_state.keys():
        if "usos" in key:
            valor = st.session_state[key]
            if isinstance(valor, list):  # evita errores si es bool o None
                usos.extend(valor)

    # Eliminar duplicados
    usos = list(set(usos))  # <-- Aquí eliminamos repeticiones

    # Reunir los equipos seleccionados globalmente
    equipos = st.session_state.get("subusos_seleccionados", [])
    equipos = list(set(equipos))  # también eliminamos duplicados si los hubiera

    if not usos and not equipos:
        st.info("Selecciona primero los servicios o equipos en la pestaña anterior para ver los consejos.")
    else:
        # --- Consejos generales (por uso) ---
        if usos:
            st.subheader("🌎 Consejos Generales por Servicio")
            for uso in usos:
                clave_general = next(
                    (k for k in consejos.keys() if uso.lower() in k.lower() and "(consejos generales)" in k.lower()),
                    None
                )
                if clave_general:
                    with st.expander(f"{uso} — Consejos Generales", expanded=False):
                        for c in consejos[clave_general]:
                            st.markdown(f"- {c}")
            st.markdown("---")

        # --- Consejos específicos (por equipo) ---
        if equipos:
            st.subheader("⚙️ Consejos Específicos por Equipo")
            for eq in equipos:
                if eq in consejos:
                    with st.expander(f"{eq} — Consejos Específicos", expanded=False):
                        for c in consejos[eq]:
                            st.markdown(f"- {c}")

    # ------------------------
    # Limpiar subusos no seleccionados
    # ------------------------
    subusos_activos = []
    for key in st.session_state.keys():
        if key.startswith(("of_", "res_", "fu_")):
            valor = st.session_state.get(key)
            if valor:  # solo agregamos si hay datos
                nombre_equipo = key.split("_", 2)[-1]  # extrae el nombre del subuso
                subusos_activos.append(nombre_equipo)
    st.session_state["subusos_seleccionados"] = list(set(subusos_activos))  # <-- eliminar duplicados aquí también

    # ------------------------
    # Limpiar subusos no seleccionados
    # ------------------------
    subusos_activos = []
    for key in st.session_state.keys():
        if key.startswith(("of_", "res_", "fu_")):
            valor = st.session_state.get(key)
            if valor:  # solo agregamos si hay datos
                nombre_equipo = key.split("_", 2)[-1]  # extrae el nombre del subuso
                subusos_activos.append(nombre_equipo)
    st.session_state["subusos_seleccionados"] = subusos_activos

# ------------------------
# Resultados: Tabla resumen y Sankey (barra lateral con botones)
# ------------------------
st.sidebar.markdown("---")
st.sidebar.header("Resultados:")

# Inicializar flags si no existen
if "mostrar_tabla" not in st.session_state:
    st.session_state["mostrar_tabla"] = False
if "mostrar_sankey" not in st.session_state:
    st.session_state["mostrar_sankey"] = False
if "mostrar_pareto" not in st.session_state:
    st.session_state["mostrar_pareto"] = False

# ------------------------
# Botones para alternar tabla y Sankey
# ------------------------
if st.sidebar.button("📋 Mostrar / Ocultar tabla resumen"):
    st.session_state["mostrar_tabla"] = not st.session_state["mostrar_tabla"]

if st.sidebar.button("📊 Mostrar / Ocultar Sankey"):
    st.session_state["mostrar_sankey"] = not st.session_state["mostrar_sankey"]

if st.sidebar.button("📊 Mostrar / Ocultar Pareto"):
    st.session_state["mostrar_pareto"] = not st.session_state["mostrar_pareto"]

st.sidebar.divider()

if st.sidebar.button("📄 Generar reporte de resultados"):

    sankey_data = st.session_state.get("sankey_data", [])

    # =========================
    # VALIDACIÓN
    # =========================
    if not sankey_data:
        st.sidebar.warning("⚠️ No hay datos suficientes para generar el reporte.")
        st.stop()

    # =========================
    # DATAFRAME BASE
    # =========================
    df = pd.DataFrame(sankey_data)

    consumo_total = df["valor"].sum()

    # =========================
    # DETECTAR MODO
    # =========================
    tiene_pisos = "piso" in df.columns and df["piso"].notna().any()

    # =========================
    # SELECCIÓN DE PLANTILLA
    # =========================
    if tiene_pisos:
        plantilla = "templates/reporte_base_piso.docx"
        nombre_reporte = "Reporte_Diagnostico_Energetico_Por_Piso.docx"
    else:
        plantilla = "templates/reporte_base_global.docx"
        nombre_reporte = "Reporte_Diagnostico_Energetico_Global.docx"

    # =========================
    # ANÁLISIS GLOBAL (siempre)
    # =========================
    servicio_global_mayor = (
        df.groupby("uso")["valor"].sum().idxmax()
    )

    consumo_servicio_global_mayor = (
        df[df["uso"] == servicio_global_mayor]["valor"].sum()
    )

    equipo_global_mayor = (
        df.groupby("subuso")["valor"].sum().idxmax()
    )

    consumo_equipo_global_mayor = (
        df[df["subuso"] == equipo_global_mayor]["valor"].sum()
    )

    servicio_global_segundo = (
        df.groupby("uso")["valor"].sum()
        .sort_values(ascending=False)
        .index[1] if df["uso"].nunique() > 1 else "No aplica"
    )

    equipo_global_segundo = (
        df.groupby("subuso")["valor"].sum()
        .sort_values(ascending=False)
        .index[1] if df["subuso"].nunique() > 1 else "No aplica"
    )

    # =========================
    # ANÁLISIS POR PISO (solo si aplica)
    # =========================
    if tiene_pisos:
        consumo_por_piso = df.groupby("piso")["valor"].sum().sort_values(ascending=False)

        piso_mayor = consumo_por_piso.index[0]
        consumo_piso_mayor = consumo_por_piso.iloc[0]

        piso_segundo = consumo_por_piso.index[1] if len(consumo_por_piso) > 1 else "No aplica"
        consumo_piso_segundo = consumo_por_piso.iloc[1] if len(consumo_por_piso) > 1 else "No aplica"

        df_piso = df[df["piso"] == piso_mayor]

        servicio_piso_mayor = df_piso.groupby("uso")["valor"].sum().idxmax()
        consumo_servicio_piso_mayor = df_piso[df_piso["uso"] == servicio_piso_mayor]["valor"].sum()

        equipo_piso_mayor = df_piso.groupby("subuso")["valor"].sum().idxmax()
        consumo_equipo_piso_mayor = df_piso[df_piso["subuso"] == equipo_piso_mayor]["valor"].sum()
    else:
        piso_mayor = consumo_piso_mayor = "No aplica"
        piso_segundo = consumo_piso_segundo = "No aplica"
        servicio_piso_mayor = consumo_servicio_piso_mayor = "No aplica"
        equipo_piso_mayor = consumo_equipo_piso_mayor = "No aplica"

    # =========================
    # DATOS PARA WORD
    # =========================
    datos_reporte = {
        "INMUEBLE": st.session_state.get("nombre_inmueble", "No especificado"),
        "TIPO_INMUEBLE": st.session_state.get("tipo_inmueble", "No especificado"),
        "DEPENDENCIA": st.session_state.get("dependencia", "No especificado"),
        "FECHA_REPORTE": date.today().strftime("%d/%m/%Y"),
        "CONSUMO_TOTAL_KWH": f"{consumo_total:,.0f} kWh/mes",

        # Piso
        "PISO_MAYOR_CONSUMO": piso_mayor,
        "CONSUMO_PISO_MAYOR_CONSUMO_KWH": f"{consumo_piso_mayor:,.0f} kWh/mes" if piso_mayor != "No aplica" else "No aplica",
        "PISO_SEGUNDO_CONSUMO": piso_segundo,
        "CONSUMO_PISO_SEGUNDO_KWH": f"{consumo_piso_segundo:,.0f} kWh/mes" if piso_segundo != "No aplica" else "No aplica",

        "SERVICIO_PISO_MAYOR": servicio_piso_mayor,
        "CONSUMO_SERVICIO_PISO_MAYOR": f"{consumo_servicio_piso_mayor:,.0f} kWh/mes" if servicio_piso_mayor != "No aplica" else "No aplica",

        "EQUIPO_PISO_MAYOR": equipo_piso_mayor,
        "CONSUMO_EQUIPO_PISO_MAYOR": f"{consumo_equipo_piso_mayor:,.0f} kWh/mes" if equipo_piso_mayor != "No aplica" else "No aplica",

        # Global
        "SERVICIO_GLOBAL_MAYOR": servicio_global_mayor,
        "CONSUMO_SERVICIO_GLOBAL_MAYOR": f"{consumo_servicio_global_mayor:,.0f} kWh/mes",
        "EQUIPO_GLOBAL_MAYOR": equipo_global_mayor,
        "CONSUMO_EQUIPO_GLOBAL_MAYOR": f"{consumo_equipo_global_mayor:,.0f} kWh/mes",

        "SERVICIO_GLOBAL_SEGUNDO": servicio_global_segundo,
        "EQUIPO_GLOBAL_SEGUNDO": equipo_global_segundo,
    }

    # =========================
    # GENERAR WORD
    # =========================
    generar_reporte_word(datos_reporte, plantilla, "reporte_resultados.docx")

    st.sidebar.success("Reporte generado correctamente")

    with open("reporte_resultados.docx", "rb") as f:
        st.sidebar.download_button(
            "⬇️ Descargar reporte",
            data=f,
            file_name=nombre_reporte,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# ------------------------
# Mostrar tabla resumen
# ------------------------
if st.session_state["mostrar_tabla"]:
    sankey_data = st.session_state.get("sankey_data", [])
    if not sankey_data:
        st.sidebar.info("⚠️ No hay datos para generar Tabla.")
    else:
        df_sankey = pd.DataFrame(sankey_data)
        df_tabla = df_sankey.rename(columns={
            "uso": "Servicio",
            "subuso": "Equipo",
            "valor": "Consumo (kWh/mes)"
        })

        # ✅ Calcular total y porcentaje
        total = df_tabla["Consumo (kWh/mes)"].sum()
        df_tabla["% del consumo"] = (df_tabla["Consumo (kWh/mes)"] / total * 100).round(2)

        # ✅ Agregar fila final del total
        total_row = pd.DataFrame({
            "Servicio": ["TOTAL"],
            "Equipo": [""],
            "Consumo (kWh/mes)": [round(total, 2)],
            "% del consumo": [100.00]
        })
        df_tabla_total = pd.concat([df_tabla, total_row], ignore_index=True)

        st.subheader("📋 Tabla resumen (consumos calculados)")
        st.dataframe(df_tabla_total)

        st.markdown(f"**Consumo total (kWh/mes):** `{round(total,2)} kWh`")

        # ✅ Exportar Excel con la fila del total incluida
        buffer = BytesIO()
        df_tabla_total.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="💾 Descargar Excel (tabla resumen)",
            data=buffer.getvalue(),
            file_name="consumo_resumen.xlsx",
            mime="application/vnd.ms-excel"
        )

# ------------------------
# Mostrar Sankey (compatible con Global y Por piso)
# ------------------------
if st.session_state["mostrar_sankey"]:
    sankey_data = st.session_state.get("sankey_data", [])
    if not sankey_data:
        st.sidebar.info("⚠️ No hay datos para generar Sankey.")
    else:
        df = pd.DataFrame(sankey_data)

        # Verifica si hay pisos
        tiene_pisos = "piso" in df.columns and df["piso"].notna().any()

        if tiene_pisos:
            labels = ["Energía eléctrica"] \
                     + sorted(df["piso"].unique().tolist()) \
                     + sorted(df["uso"].unique().tolist()) \
                     + sorted(df["subuso"].unique().tolist())

            label_index = {l: i for i, l in enumerate(labels)}
            sources, targets, values = [], [], []

            for d in sankey_data:
                piso = d["piso"]
                uso = d["uso"]
                subuso = d["subuso"]

                # Energía → Piso
                sources.append(label_index["Energía eléctrica"])
                targets.append(label_index[piso])
                values.append(d["valor"])

                # Piso → Uso
                sources.append(label_index[piso])
                targets.append(label_index[uso])
                values.append(d["valor"])

                # Uso → Subuso
                sources.append(label_index[uso])
                targets.append(label_index[subuso])
                values.append(d["valor"])

        else:
            # Modo global (como ya lo tienes)
            labels = ["Energía eléctrica"] + sorted(df["uso"].unique().tolist()) + sorted(df["subuso"].unique().tolist())
            label_index = {l: i for i, l in enumerate(labels)}
            sources, targets, values = [], [], []
            for d in sankey_data:
                sources.append(label_index["Energía eléctrica"])
                targets.append(label_index[d["uso"]])
                values.append(d["valor"])
                sources.append(label_index[d["uso"]])
                targets.append(label_index[d["subuso"]])
                values.append(d["valor"])

        fig = go.Figure(data=[go.Sankey(
            node=dict(label=labels, pad=15, thickness=20),
            link=dict(source=sources, target=targets, value=values)
        )])
        fig.update_layout(title_text="🔌 Diagrama Sankey del consumo (kWh/mes)", font_size=12, height=600)
        st.plotly_chart(fig, use_container_width=True)
        
# ------------------------
# Mostrar gráfico de Pareto
# ------------------------
if st.session_state["mostrar_pareto"]:
    sankey_data = st.session_state.get("sankey_data", [])
    
    if not sankey_data:
        st.sidebar.info("⚠️ No hay datos para generar Gráfico.")
    else:
        df_sankey = pd.DataFrame(sankey_data)

        # Agrupar por subuso/equipo
        df_pareto = df_sankey.groupby("subuso")["valor"].sum().reset_index()
        df_pareto = df_pareto.rename(columns={"subuso": "Equipo", "valor": "Consumo (kWh/mes)"})

        # Ordenar de mayor a menor consumo
        df_pareto = df_pareto.sort_values(by="Consumo (kWh/mes)", ascending=False)
        df_pareto["% Acumulado"] = df_pareto["Consumo (kWh/mes)"].cumsum() / df_pareto["Consumo (kWh/mes)"].sum() * 100

        # Crear gráfico de Pareto usando Plotly
        fig_pareto = go.Figure()

        # Barras: Consumo de cada equipo
        fig_pareto.add_trace(go.Bar(
            x=df_pareto["Equipo"],
            y=df_pareto["Consumo (kWh/mes)"],
            name="Consumo (kWh/mes)",
            marker_color="steelblue"
        ))

        # Línea: % acumulado
        fig_pareto.add_trace(go.Scatter(
            x=df_pareto["Equipo"],
            y=df_pareto["% Acumulado"],
            name="% Acumulado",
            yaxis="y2",
            mode="lines+markers",
            marker_color="crimson"
        ))

        # Configurar doble eje Y
        fig_pareto.update_layout(
            title="📊 Gráfico de Pareto de consumo por equipo",
            xaxis_title="Equipo",
            yaxis_title="Consumo (kWh/mes)",
            yaxis2=dict(
                title="% Acumulado",
                overlaying="y",
                side="right",
                range=[0, 110]
            ),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )

        st.plotly_chart(fig_pareto, use_container_width=True)
# ------------------------
# Footer
# ------------------------
#st.markdown("---")
#st.markdown("App diseñada para calcular consumos eléctricos por servicio o equipo, introduce tus datos y usa la pestaña **Consejos** para ver recomendaciones enfocadas. Ajusta `dias de operación por semana` en la barra lateral para cambiar el factor mensual.")

MANUALCONSEJOS = "https://www.gob.mx/cms/uploads/article/main_image/143207/consejos_hogar.jpg"
MANUALERRORES = "https://drive.google.com/file/d/12ivfGNzWW15SsZxgnVKp9IUxNgWW5S9O/view?usp=drive_link" 
LINKME = "https://www.gob.mx/cms/uploads/attachment/file/1038494/Correccio_n_de_malas_pra_cticas_en_oficinas.pdf"
LINKMC = "https://www.conuee.gob.mx/transparencia/nuevaestrategia/docs/CONSEJOS_EE_HOGAR_2025.pdf"

with st.sidebar:
    st.markdown(
        f'<a href="{LINKMC}" target="_blank">'
        f'<img src="{MANUALCONSEJOS}" alt="CONUEE" style="width:100%;">'
        f'<a href="{LINKME}" target="_blank">'
        f'<img src="{MANUALErrores}" alt="CONUEE" style="width:100%;">'
        '</a>',
        unsafe_allow_html=True
    )





























