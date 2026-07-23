import os
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

# Carpeta donde están los archivos
carpeta = r"../resultados_set_large"

# Lista donde se almacenarán todas las filas
datos = []

# Recorrer archivos
for archivo in os.listdir(carpeta):

    if not archivo.endswith(".txt"):
        continue

    # Identificar el tipo de archivo
    if archivo.startswith("vns"):
        tipo_archivo = "vns"
    elif archivo.startswith("ga"):
        tipo_archivo = "ga"
    elif archivo.startswith("sa"):
        tipo_archivo = "sa"
    elif archivo.startswith("model"):
        tipo_archivo = "model"
    else:
        continue

    ruta = os.path.join(carpeta, archivo)

    with open(ruta, "r", encoding="utf-8") as f:

        for linea in f:

            linea = linea.strip()

            if linea == "":
                continue

            partes = linea.split()

            # Debe tener exactamente 8 columnas
            if len(partes) != 8:
                continue

            # Separar la información de la instancia
            tipo_instancia = partes[0].replace(".csv", "")
            distancia_urbana, n_nodos, bateria, velocidad = tipo_instancia.split("_")

            datos.append({
                "tipo_instancia": tipo_instancia,
                "distancia_urbana": int(distancia_urbana),
                "n_nodos": int(n_nodos),
                "bateria": int(bateria),
                "velocidad": int(velocidad),
                "tipo_archivo": tipo_archivo,
                "n_drones": int(partes[1]),
                "semilla": int(partes[2]),
                "resultado": float(partes[3]),
                "tiempo_ejec": float(partes[4]),
                "tiempo_vuelo": float(partes[5]),
                "nvl_serv": float(partes[6]),
                "tiempo_espera": float(partes[7])
            })

# Crear DataFrame
df = pd.DataFrame(datos)

# Mostrar las primeras filas
# print(df.head())

# (Opcional) Guardar en Excel
# df.to_excel("../resultados_set_large_raw.xlsx", index=False)


df_large = df[
    (
        ((df["distancia_urbana"] == 1010) & (df["n_nodos"].isin([80,100,150]))) |
        ((df["distancia_urbana"] == 2020) & (df["n_nodos"].isin([40,60,80]))) |
        ((df["distancia_urbana"] == 4040) & (df["n_nodos"].isin([15,30,40])))
    )
    &
    (df["tipo_archivo"].isin(["vns","sa", "ga"]))
].copy()
# print(df_large.head())

bks = (
    df_large
    .groupby([
        "distancia_urbana",
        "n_nodos",
        "bateria",
        "velocidad",
        "n_drones"
    ])["resultado"]
    .min()
    .reset_index(name="bks")
)
# print(bks)

df_large = df_large.merge(
    bks,
    on=[
        "distancia_urbana",
        "n_nodos",
        "bateria",
        "velocidad",
        "n_drones"
    ]
)
# print(df_large)

df_large["gap"] = (df_large["resultado"] - df_large["bks"]) / df_large["bks"]
# print(df_large.query("tipo_instancia == '1010_80_30_40' & n_drones == 1" ))
# print(df_large.query("distancia_urbana == 1010 & n_nodos == 80 & tipo_archivo == 'sa' " ))
# print(df_large.query("gap < 0" ))
# print(df_large.head())
# print(df_large.query("distancia_urbana== 4040 & tipo_archivo == 'vns' & n_nodos == 15 & "))
# print("-"*100)

df_large["hit_large"] = np.where(df_large["bks"] == df_large["resultado"], 1, 0)
# print(df_large.query("hit_large == 1"))
# print("-"*100)

# ============================================================
# Calcular estadísticas por configuración
# (cada configuración = bateria, velocidad, n_drones)
# ============================================================

aux = (
    df_large
    .groupby([
        "distancia_urbana",
        "n_nodos",
        "bateria",
        "velocidad",
        "n_drones",
        "tipo_archivo"
    ])
    .agg(
        resultado_prom=("resultado", "mean"),
        resultado_min=("resultado", "min"),
        bks=("bks", "first"),
        tiempo=("tiempo_ejec", "mean"),
        conteo=("resultado", "count")
        # resultado_std=("resultado","std"),    
    )
    .reset_index()
)

# aux["cv"] = (
#     aux["resultado_std"] /
#     aux["resultado_prom"]
# )

# Gap usando el promedio
aux["gap_avg"] = (
    aux["resultado_prom"] - aux["bks"]
) / aux["bks"]

# Gap usando el mínimo
aux["gap_min"] = (
    aux["resultado_min"] - aux["bks"]
) / aux["bks"]


aux["hit_large"] = np.where(aux["gap_min"] == 0, 1, 0)
# print(aux.agg(conteo_total=("conteo","sum")))

# ============================================================
# Resumen final
# ============================================================

resumen = (
    aux
    .groupby([
        "distancia_urbana",
        "n_nodos",
        "tipo_archivo"
    ])
    .agg(
        gap_avg=("gap_avg", "mean"),
        gap_min=("gap_min", "mean"),
        costo_prom=("resultado_prom", "mean"),
        bks=("bks", "max"),          # solo informativo
        tiempo=("tiempo", "mean"),
        conteo=("conteo", "sum"),
        hit_large=("hit_large", "sum"),
        # std=("resultado_std","mean"),
        gap_avg_std=("gap_avg", "std"),
        gap_min_std=("gap_min", "std")
    )
    .reset_index()
)

# print(resumen)
# print(resumen.query("hit_large > 30"))

resumen_final = (
    resumen
    .pivot(
        index=["distancia_urbana", "n_nodos"],
        columns="tipo_archivo"
    )
)

# Aplanar el MultiIndex de las columnas
resumen_final.columns = [
    f"{col}_{alg}"
    for col, alg in resumen_final.columns
]

# Volver las variables del índice a columnas
resumen_final = resumen_final.reset_index()

# (Opcional) Reordenar las columnas
resumen_final = resumen_final[
    [
        "distancia_urbana",
        "n_nodos",

        "gap_avg_vns",
        "gap_avg_sa",
        "gap_avg_ga",

        "gap_min_vns",
        "gap_min_sa",
        "gap_min_ga",

        # "costo_prom_vns",
        # "costo_prom_sa",

        # "bks_vns",
        # "bks_sa",

        "tiempo_vns",
        "tiempo_sa",
        "tiempo_ga",

        # "conteo_vns",
        # "conteo_sa",

        "hit_large_vns",
        "hit_large_sa",
        "hit_large_ga",

        "gap_avg_std_vns",
        "gap_avg_std_sa",
        "gap_avg_std_ga",

        "gap_min_std_vns",
        "gap_min_std_sa",
        "gap_min_std_ga"
    ]
]

print(resumen_final)

# (Opcional) Guardar en Excel
# resumen_final.to_excel("../resultados_set_large_dist_n_nodos.xlsx", index=False)

###################################################################################################
###################################################################################################
# ###### SET LARGE AGRUPADO POR DRONES ######
###################################################################################################
###################################################################################################

# ============================================================
# Resumen final
# ============================================================

resumen = (
    aux
    .groupby([
        "n_drones",
        "tipo_archivo"
    ])
    .agg(
        gap_avg=("gap_avg", "mean"),
        gap_min=("gap_min", "mean"),
        costo_prom=("resultado_prom", "mean"),
        bks=("bks", "max"),
        tiempo=("tiempo", "mean"),
        conteo=("conteo", "sum"),
        hit_large=("hit_large", "sum"),
        # std=("resultado_std","mean")
        gap_avg_std=("gap_avg", "std"),
        gap_min_std=("gap_min", "std")
    )
    .reset_index()
)

# print(resumen)
# print(resumen.query("hit_large > 30"))

resumen_final = (
    resumen
    .pivot(
        index="n_drones",
        columns="tipo_archivo"
    )
)

# Aplanar el MultiIndex de las columnas
resumen_final.columns = [
    f"{col}_{alg}"
    for col, alg in resumen_final.columns
]

resumen_final = resumen_final.reset_index()

# (Opcional) Reordenar las columnas
resumen_final = resumen_final[
    [
        "n_drones",

        "gap_avg_vns",
        "gap_avg_sa",
        "gap_avg_ga",

        "gap_min_vns",
        "gap_min_sa",
        "gap_min_ga",

        "tiempo_vns",
        "tiempo_sa",
        "tiempo_ga",

        "hit_large_vns",
        "hit_large_sa",
        "hit_large_ga",

        "gap_avg_std_vns",
        "gap_avg_std_sa",
        "gap_avg_std_ga",

        "gap_min_std_vns",
        "gap_min_std_sa",
        "gap_min_std_ga"
    ]
]

print(resumen_final)

# (Opcional) Guardar en Excel
# resumen_final.to_excel("../resultados_set_large_n_drones.xlsx", index=False)


###################################################################################################
###################################################################################################
# ###### SET LARGE AGRUPADO PARA METRICAS DE SERVICIO ######
###################################################################################################
###################################################################################################

aux_area = (
    df_large
    .groupby([
        "distancia_urbana",
        "tipo_archivo"
    ])
    .agg(
        drone_delivery=("tiempo_vuelo", "mean"),
        service_lvl=("nvl_serv", "mean"),
        waiting_time=("tiempo_espera", "mean")
    )
    .reset_index()
)
# print(aux_area)
aux_area["service_lvl"] = 1 - aux_area["service_lvl"]

aux_area_final = (
    aux_area
    .pivot(
        index="distancia_urbana",
        columns="tipo_archivo"
    )
)
# print(aux_area_final)

# Aplanar el MultiIndex de las columnas
aux_area_final.columns = [
    f"{col}_{alg}"
    for col, alg in aux_area_final.columns
]

aux_area_final = aux_area_final.reset_index()

# (Opcional) Reordenar las columnas
aux_area_final = aux_area_final[
    [
        "distancia_urbana",

        "drone_delivery_vns",
        "drone_delivery_sa",
        "drone_delivery_ga",

        "service_lvl_vns",
        "service_lvl_sa",
        "service_lvl_ga",

        "waiting_time_vns",
        "waiting_time_sa",
        "waiting_time_ga"
    ]
]
# print(aux_area_final)


aux_nodos = (
    df_large
    .groupby([
        "n_nodos",
        "tipo_archivo"
    ])
    .agg(
        drone_delivery=("tiempo_vuelo", "mean"),
        service_lvl=("nvl_serv", "mean"),
        waiting_time=("tiempo_espera", "mean")
    )
    .reset_index()
)
aux_nodos["service_lvl"] = 1 - aux_nodos["service_lvl"]

aux_nodos_final = (
    aux_nodos
    .pivot(
        index="n_nodos",
        columns="tipo_archivo",
        values=["drone_delivery","service_lvl","waiting_time"]
    )
)

aux_nodos_final.columns = [
    f"{col}_{alg}"
    for col, alg in aux_nodos_final.columns
]

aux_nodos_final = aux_nodos_final.reset_index()

aux_drones = (
    df_large
    .groupby([
        "n_drones",
        "tipo_archivo"
    ])
    .agg(
        drone_delivery=("tiempo_vuelo", "mean"),
        service_lvl=("nvl_serv", "mean"),
        waiting_time=("tiempo_espera", "mean")
    )
    .reset_index()
)

# print(aux_drones[["service_lvl"]])
aux_drones["service_lvl"] = 1 - aux_drones["service_lvl"]
# print(aux_drones.query("tipo_archivo == 'vns'")[["n_drones", "service_lvl"]])
# print(aux_drones)

aux_drones_final = (
    aux_drones
    .pivot(
        index="n_drones",
        columns="tipo_archivo",
        values=["drone_delivery","service_lvl","waiting_time"]
    )
)

aux_drones_final.columns = [
    f"{col}_{alg}"
    for col, alg in aux_drones_final.columns
]

aux_drones_final = aux_drones_final.reset_index()

# print(aux_drones_final[["n_drones","service_lvl_vns"]])
# print(aux_drones_final)



# def plot_metric(df,
#                 llave,
#                 nombres,
#                 prefijo,
#                 porcentaje=True,
#                 ylabel="",
#                 una_fila=1):

#     etiquetas = ["MH", "SA", "GA"]
#     colores = ["steelblue", "lightgray", "darkgray"]

#     # Número de gráficos
#     n = len(nombres)

#     # Distribución de subplots
#     if una_fila == 1:
#         nrows = 1
#         ncols = n
#     else:
#         ncols = min(3, n)
#         nrows = math.ceil(n / 3)

#     fig, axes = plt.subplots(
#         nrows,
#         ncols,
#         figsize=(5.2 * ncols, 5.8 * nrows),
#         sharey=True,
#         constrained_layout=True
#     )

#     # Convertir axes en arreglo 1D
#     axes = np.atleast_1d(axes).flatten()

#     for ax, (valor, titulo) in zip(axes, nombres.items()):

#         fila = df[df[llave] == valor].iloc[0]

#         valores = [
#             fila[f"{prefijo}_vns"],
#             fila[f"{prefijo}_sa"],
#             fila[f"{prefijo}_ga"]
#         ]

#         barras = ax.bar(
#             etiquetas,
#             valores,
#             color=colores,
#             width=0.60
#         )

#         ax.set_title(
#             titulo,
#             fontsize=12,
#             fontweight="bold",
#             pad=12
#         )

#         if porcentaje:
#             ax.set_ylim(0, 1.08)
#             ax.set_yticks(np.arange(0, 1.01, 0.2))
#             ax.set_yticklabels(
#                 [f"{int(x*100)}%" for x in np.arange(0, 1.01, 0.2)]
#             )

#         ylim = ax.get_ylim()[1]

#         for barra, valor in zip(barras, valores):

#             texto = (
#                 f"{valor*100:.2f}%"
#                 if porcentaje
#                 else f"{valor:.2f}"
#             )

#             if valor >= 0.90 * ylim:
#                 y = valor - 0.04 * ylim
#                 va = "top"
#             else:
#                 y = valor + 0.02 * ylim
#                 va = "bottom"

#             ax.text(
#                 barra.get_x() + barra.get_width()/2,
#                 y,
#                 texto,
#                 ha="center",
#                 va=va,
#                 fontsize=9,
#                 fontweight="bold"
#             )

#         ax.tick_params(axis="x", labelsize=10)
#         ax.tick_params(axis="y", labelsize=10)

#     # Ocultar ejes sobrantes
#     for ax in axes[n:]:
#         ax.set_visible(False)

#     fig.supxlabel(
#         ylabel,
#         fontsize=12,
#         fontweight="bold",
#         y=0.02
#     )

#     fig.subplots_adjust(
#         hspace=0.45,
#         wspace=0.25,
#         bottom=0.12,
#         top=0.90
#     )

#     plt.show()

def plot_metric(df,
                llave,
                nombres,
                prefijo,
                porcentaje=True,
                ylabel="",
                una_fila=1):

    etiquetas = ["MH", "SA", "GA"]
    colores = ["steelblue", "lightgray", "darkgray"]

    # Número de gráficos
    n = len(nombres)

    # Distribución de subplots
    if una_fila == 1:
        nrows = 1
        ncols = n
    else:
        ncols = min(3, n)
        nrows = math.ceil(n / 3)

    # ---------------------------------------------------
    # Calcular límite superior común del eje Y
    # ---------------------------------------------------
    if porcentaje:
        max_valor = 0
        for valor in nombres.keys():
            fila = df[df[llave] == valor].iloc[0]
            max_valor = max(
                max_valor,
                fila[f"{prefijo}_vns"],
                fila[f"{prefijo}_sa"],
                fila[f"{prefijo}_ga"]
            )

        ylim_sup = max_valor * 1.12  # 12% de margen
        ylim_sup = min(1.0, ylim_sup) if max_valor > 0.9 else ylim_sup

        # Redondear hacia arriba a un múltiplo de 0.05
        ylim_sup = np.ceil(ylim_sup / 0.05) * 0.05

        # Generar 6 marcas equiespaciadas
        yticks = np.linspace(0, ylim_sup, 6)
    # ---------------------------------------------------

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(5.2 * ncols, 5.8 * nrows),
        sharey=True,
        constrained_layout=True
    )

    axes = np.atleast_1d(axes).flatten()

    for ax, (valor, titulo) in zip(axes, nombres.items()):

        fila = df[df[llave] == valor].iloc[0]

        valores = [
            fila[f"{prefijo}_vns"],
            fila[f"{prefijo}_sa"],
            fila[f"{prefijo}_ga"]
        ]

        barras = ax.bar(
            etiquetas,
            valores,
            color=colores,
            width=0.60
        )

        ax.set_title(
            titulo,
            fontsize=12,
            fontweight="bold",
            pad=12
        )

        if porcentaje:
            ax.set_ylim(0, ylim_sup)
            ax.set_yticks(yticks)
            ax.set_yticklabels([f"{x*100:.0f}%" for x in yticks])

        ylim = ax.get_ylim()[1]

        for barra, valor in zip(barras, valores):

            texto = (
                f"{valor*100:.2f}%"
                if porcentaje
                else f"{valor:.2f}"
            )

            # Si la barra está muy cerca del límite superior,
            # escribir la etiqueta dentro de la barra
            if valor >= 0.90 * ylim:
                y = valor - 0.04 * ylim
                va = "top"
            else:
                y = valor + 0.02 * ylim
                va = "bottom"

            ax.text(
                barra.get_x() + barra.get_width() / 2,
                y,
                texto,
                ha="center",
                va=va,
                fontsize=9,
                fontweight="bold"
            )

        ax.tick_params(axis="x", labelsize=10)
        ax.tick_params(axis="y", labelsize=10)

    # Ocultar ejes sobrantes
    for ax in axes[n:]:
        ax.set_visible(False)

    fig.supxlabel(
        ylabel,
        fontsize=12,
        fontweight="bold",
        y=0.02
    )

    fig.subplots_adjust(
        hspace=0.45,
        wspace=0.25,
        bottom=0.12,
        top=0.90
    )

    plt.show()


areas = {
    1010:"Urban",
    2020:"Suburban",
    4040:"Rural"
}

# plot_metric(aux_area_final,
#             "distancia_urbana",
#             areas,
#             "drone_delivery",
#             porcentaje=True)

# plot_metric(aux_area_final,
#             "distancia_urbana",
#             areas,
#             "service_lvl",
#             porcentaje=True)

# plot_metric(aux_area_final,
#             "distancia_urbana",
#             areas,
#             "waiting_time",
#             porcentaje=True)

nodos = {
    15:"15",
    30:"30",
    40:"40",
    60:"60",
    80:"80",
    100:"100",
    150:"150"
}

# plot_metric(aux_nodos_final,
#             "n_nodos",
#             nodos,
#             "drone_delivery",
#             porcentaje=True)

# plot_metric(aux_nodos_final,
#             "n_nodos",
#             nodos,
#             "service_lvl",
#             porcentaje=True)

# plot_metric(aux_nodos_final,
#             "n_nodos",
#             nodos,
#             "waiting_time",
#             porcentaje=True)

drones = {
    1:"1",
    2:"2",
    3:"3",
    4:"4",
    5:"5"
}

# plot_metric(aux_drones_final,
#             "n_drones",
#             drones,
#             "drone_delivery",
#             porcentaje=True)

# plot_metric(aux_drones_final,
#             "n_drones",
#             drones,
#             "service_lvl",
#             porcentaje=True)

# plot_metric(aux_drones_final,
#             "n_drones",
#             drones,
#             "waiting_time",
#             porcentaje=True)

###################################################################################################
###################################################################################################
# ###### Test de Wilcoxon ######
###################################################################################################
###################################################################################################

# Cada fila corresponde a una ejecución (misma instancia y semilla)
tabla = (
    df_large
    .pivot_table(
        index=[
            "distancia_urbana",
            "n_nodos",
            "bateria",
            "velocidad",
            "n_drones",
            "semilla"
        ],
        columns="tipo_archivo",
        values="resultado"
    )
    .dropna()
)

# print(f"Número de observaciones: {len(tabla)}")

comparaciones = [
    ("vns", "sa"),
    ("vns", "ga"),
    ("sa", "ga")
]

for a1, a2 in comparaciones:

    estadistico, pvalor = wilcoxon(
        tabla[a1],
        tabla[a2],
        alternative="two-sided"
    )

    # print(f"\n{a1.upper()} vs {a2.upper()}")
    # print(f"Estadístico = {estadistico:.0f}")
    # print(f"p-value     = {pvalor:.6g}")

    # if pvalor < 0.05:
    #     print("=> Diferencia estadísticamente significativa.")
    # else:
    #     print("=> No se observa diferencia estadísticamente significativa.")