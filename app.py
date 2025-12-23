import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

DATA_FILE = 'pedidos_mi_escondite.csv'

MENU = {
    "Hamburguesas": {"Italiana": 2.25, "Francesa": 3.00, "Española": 3.00, "Americana": 3.00, "4 Estaciones": 3.00,
        "Mexicana": 3.00, "Especial": 3.00, "Suprema": 3.50, "Papi Burguer": 2.50, "A su gusto (Jumbo)": 5.00,
        "Triple Burguer": 6.00, "Doble Burguer": 4.50},
    "Hot Dogs": {"Especial Mixto": 2.25, "Especial de Pollo": 2.25, "Hot Dog con salame": 2.25,
                 "Mix Dog - Jumbo": 2.25, "Champi Dog": 2.25, "Hot Dog con cebolla": 1.75},
    "Papas Fritas": {"Salchipapa (1.50)": 1.50, "Salchipapa (1.75)": 1.75, "Papi carne": 2.25, "Papi Pollo": 2.25,
                     "Salchipapa especial": 3.25, "Papa Mix": 3.25, "Papa Wlady": 5.00},
    "Sanduches": {"Cubano": 2.00, "Vegetariano": 2.00, "Sanduche de Pollo": 2.00},
    "Bebidas": {"Colas Pequeñas": 0.75, "Jugos": 1.50, "Batidos": 1.75, "Jamaica": 0.50},
    "Porciónes": {"Papas Fritas (0.50)": 0.50, "Papas Fritas (1.00)": 1.00, "Huevo Frito": 0.50, "Presa de Pollo": 1.50}
}

ESTADOS = ["En proceso", "Entregado", "Pagado", "Cancelado"]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'ID' not in df.columns:
            df['ID'] = range(1, len(df) + 1)
        if 'Nombre_Orden' not in df.columns:
            df['Nombre
