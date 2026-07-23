import os
import pandas as pd
import numpy as np


###################################################################################################
###################################################################################################
######### RESULTADOS SET SMALL #########
###################################################################################################
###################################################################################################
import os
import pandas as pd

# Carpeta donde están los archivos
carpeta_small = r"../resultados_set_small"

# Lista donde se almacenarán todas las filas
datos_small = []

# Recorrer archivos
for archivo in os.listdir(carpeta_small):

    if not archivo.endswith(".txt"):
        continue

    # Identificar el tipo de archivo
    if archivo.startswith("vns"):
        tipo_archivo = "vns"
    elif archivo.startswith("sa"):
        tipo_archivo = "sa"
    elif archivo.startswith("ga"):
        tipo_archivo = "ga"
    elif archivo.startswith("model"):
        tipo_archivo = "model"
    else:
        continue

    ruta = os.path.join(carpeta_small, archivo)

    with open(ruta, "r", encoding="utf-8") as f:

        for linea in f:

            linea = linea.strip()

            if linea == "":
                continue

            partes = linea.split()

            if len(partes) != 8:
                continue

            tipo_instancia = partes[0].replace(".csv", "")
            distancia_urbana, n_nodos, bateria, velocidad = tipo_instancia.split("_")

            # ==========================================================
            # MODEL
            # ==========================================================
            if tipo_archivo == "model":

                UB = float(partes[4])
                LB = float(partes[5])

                datos_small.append({

                    "tipo_instancia": tipo_instancia,
                    "distancia_urbana": int(distancia_urbana),
                    "n_nodos": int(n_nodos),
                    "bateria": int(bateria),
                    "velocidad": int(velocidad),

                    "tipo_archivo": tipo_archivo,
                    "n_drones": int(partes[1]),
                    "semilla": int(partes[2]),

                    # mantener esta columna para no romper el resto
                    "resultado": UB,

                    "tiempo_ejec": float(partes[3]),

                    "UB": UB,
                    "LB": LB,
                    "gap_milp": float(partes[6]),
                    "factible": int(partes[7]),

                    # columnas inexistentes para model
                    "tiempo_vuelo": np.nan,
                    "nvl_serv": np.nan,
                    "tiempo_espera": np.nan
                })

            # ==========================================================
            # METAHEURISTICAS
            # ==========================================================
            else:

                datos_small.append({

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
                    "tiempo_espera": float(partes[7]),

                    "UB": np.nan,
                    "LB": np.nan,
                    "gap_milp": np.nan,
                    "factible": np.nan
                })

# Crear DataFrame
df_set_small = pd.DataFrame(datos_small)
# print(df_set_small)

# # Mostrar las primeras filas
# # print(df_set_small.head())

# # (Opcional) Guardar en Excel
# df_set_small.to_excel("C../resultados_set_small_raw.xlsx", index=False)


df_small = df_set_small[
    (
        ((df_set_small["distancia_urbana"] == 1010) & (df_set_small["n_nodos"].isin([10,15,20]))) |
        ((df_set_small["distancia_urbana"] == 2020) & (df_set_small["n_nodos"].isin([10,15,20]))) |
        ((df_set_small["distancia_urbana"] == 4040) & (df_set_small["n_nodos"].isin([10,15,20])))
    )
    &
    (df_set_small["tipo_archivo"].isin(["vns","sa","model","ga"]))
].copy()


df_small["hit_opt_milp"] = np.where(
    round(df_small["gap_milp"],4) == 0,
    1,
    0
)

bks_small = (
    df_small
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

df_small = df_small.merge(
    bks_small,
    on=[
        "distancia_urbana",
        "n_nodos",
        "bateria",
        "velocidad",
        "n_drones"
    ]
)

df_small["gap"] = (
    df_small["resultado"] - df_small["bks"]
) / df_small["bks"]


# import numpy as np

df_small["hit_small"] = np.where(
    df_small["bks"] == df_small["resultado"],
    1,
    0
)

# print(df_small.query('tipo_instancia == "1010_10_30_40" & n_drones == 1'))

# ============================================================
# Estadísticas por configuración
# ============================================================

aux_small = (
    df_small
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
        conteo=("resultado", "count"),
        upper=("UB","max"),
        lower=("LB", "max"),
        gap_mdl=("gap_milp", "max"),
        hit_opt=("hit_opt_milp", "max")
        # resultado_std=("resultado","std")
        # gap_std=("gap", "std")

    )
    .reset_index()
)

# aux_small["cv"] = (
#     aux_small["resultado_std"] /
#     aux_small["resultado_prom"]
# )

# No se usa para el set samll
# aux_small["gap_avg"] = (
#     aux_small["resultado_prom"] - aux_small["bks"]
# ) / aux_small["bks"]


aux_small["gap_min"] = (
    aux_small["resultado_min"] - aux_small["bks"]
) / aux_small["bks"]


aux_small["hit_small"] = np.where(
    aux_small["gap_min"] == 0,
    1,
    0
)

# print(aux_small.query("distancia_urbana == 1010 & n_nodos == 10 & bateria == 30 & velocidad == 40 & n_drones == 1"))

# print(aux_small
#       .query("tipo_archivo == 'model' & distancia_urbana == 1010 & n_nodos == 10 & bateria == 30 & velocidad == 40 & n_drones == 1")
#       [["distancia_urbana", "n_nodos", "upper", "lower", "tiempo", "gap_mdl", "hit_opt"]])


# ============================================================
# Resumen final
# ============================================================

resumen_mdl = (
    aux_small
    .query("tipo_archivo == 'model'")
    .groupby([
        "distancia_urbana",
        "n_nodos"
    ])
    .agg(
        upper=("upper", "mean"),
        lower=("lower", "mean"),
        tiempo=("tiempo", "mean"),
        gap_mdl=("gap_mdl", "max"),
        hit_opt=("hit_opt", "sum"),

    )
    .reset_index()
)
# print(resumen_mdl)

resumen_small = (
    aux_small
    .groupby([
        "distancia_urbana",
        "n_nodos",
        "tipo_archivo"
    ])
    .agg(
        gap_min=("gap_min", "mean"),
        costo_prom=("resultado_prom", "mean"),
        bks=("bks", "max"),
        tiempo=("tiempo", "mean"),
        conteo=("conteo", "sum"),
        hit_small=("hit_small", "sum"),
        # std=("resultado_std","mean")
        gap_min_std=("gap_min", "std")
    )
    .reset_index()
)
# print(resumen_small)

resumen_small_final = (
    resumen_small
    .pivot(
        index=["distancia_urbana", "n_nodos"],
        columns="tipo_archivo"
    )
)
# print(resumen_small_final)
# print(resumen_small_final.columns)

resumen_small_final.columns = [
    f"{col}_{alg}"
    for col, alg in resumen_small_final.columns
]

resumen_small_final = resumen_small_final.reset_index()


resumen_small_final = resumen_small_final[
    [
        "distancia_urbana",
        "n_nodos",

        "gap_min_model",
        "gap_min_vns",
        "gap_min_sa",
        "gap_min_ga",

        # "costo_prom_vns",
        # "costo_prom_sa",
        # "costo_prom_model",

        # "bks_vns",
        # "bks_sa",
        # "bks_model",

        # "tiempo_vns",
        # "tiempo_model",
        # "tiempo_sa",
        # "tiempo_ga",

        # "conteo_vns",
        # "conteo_sa",
        # "conteo_model",

        "hit_small_model",
        "hit_small_vns",
        "hit_small_sa",
        "hit_small_ga",

        "gap_min_std_vns",
        "gap_min_std_sa",
        "gap_min_std_ga"
    ]
]

# print(resumen_small_final)

resumen_final = resumen_mdl.merge(
    resumen_small_final,
    on=["distancia_urbana", "n_nodos"],
    how="left"
)

print(resumen_final)

# # (Opcional) Guardar en Excel
# resumen_final.to_excel("../resultados_set_small_dist_n_nodos.xlsx", index=False)

##################################################################################################
##################################################################################################
###### SET SMALL AGRUPADO POR DRONES ######
##################################################################################################
##################################################################################################

# ============================================================
# Resumen final
# ============================================================

resumen_mdl = (
    aux_small
    .query("tipo_archivo == 'model'")
    .groupby([
        "n_drones"
    ])
    .agg(
        upper=("upper", "mean"),
        lower=("lower", "mean"),
        tiempo=("tiempo", "mean"),
        gap_mdl=("gap_mdl", "max"),
        hit_opt=("hit_opt", "sum")
    )
    .reset_index()
)
# print(resumen_mdl)

resumen_small = (
    aux_small
    .groupby([
        "n_drones",
        "tipo_archivo"
    ])
    .agg(
        gap_min=("gap_min", "mean"),
        costo_prom=("resultado_prom", "mean"),
        bks=("bks", "max"),
        tiempo=("tiempo", "mean"),
        conteo=("conteo", "sum"),
        hit_small=("hit_small", "sum"),
        # std=("resultado_std","mean")
        gap_min_std=("gap_min", "std")
    )
    .reset_index()
)
# print(resumen_small)

resumen_small_final = (
    resumen_small
    .pivot(
        index=["n_drones"],
        columns="tipo_archivo"
    )
)
# print(resumen_small_final)
# print(resumen_small_final.columns)

resumen_small_final.columns = [
    f"{col}_{alg}"
    for col, alg in resumen_small_final.columns
]

resumen_small_final = resumen_small_final.reset_index()

resumen_small_final = resumen_small_final[
    [
        "n_drones",

        "gap_min_model",
        "gap_min_vns",
        "gap_min_sa",
        "gap_min_ga",

        # "costo_prom_vns",
        # "costo_prom_sa",
        # "costo_prom_model",

        # "bks_vns",
        # "bks_sa",
        # "bks_model",

        # "tiempo_vns",
        # "tiempo_model",
        # "tiempo_sa",
        # "tiempo_ga",

        # "conteo_vns",
        # "conteo_sa",
        # "conteo_model",

        "hit_small_model",
        "hit_small_vns",
        "hit_small_sa",
        "hit_small_ga",

        "gap_min_std_vns",
        "gap_min_std_sa",
        "gap_min_std_ga"
    ]
]

# print(resumen_small_final)

resumen_final = resumen_mdl.merge(
    resumen_small_final,
    on=["n_drones"],
    how="left"
)
print(resumen_final)

# # # (Opcional) Guardar en Excel
# resumen_final.to_excel("../resultados_set_small_n_drones.xlsx", index=False)