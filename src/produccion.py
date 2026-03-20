import os
import pandas as pd

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, '..', 'datos')

ventas_path = os.path.join(DATOS_DIR, 'ventas.csv')
clima_path = os.path.join(DATOS_DIR, 'clima.csv')

def calcular_produccion():
    if not os.path.exists(ventas_path):
        print("Error: No se encontró ventas.csv")
        return

    df_v = pd.read_csv(ventas_path)
    df_v['fecha'] = pd.to_datetime(df_v['fecha_hora']).dt.date
    
    # Agrupar ventas diarias
    diario = df_v.groupby('fecha').agg({
        'total_unidades': 'sum',
        'unidades_pagas': 'sum'
    }).reset_index()
    
    # Simular capacidad de producción y quiebres
    # Capacidad base diaria 150 unidades
    capacidad_max = 200
    
    produccion = []
    
    for _, row in diario.iterrows():
        venta_total = row['total_unidades']
        
        # Se produce lo necesario + un pequeño margen del 10%
        unidades_producidas = int(min(capacidad_max, venta_total * 1.05))
        
        # Merma estimada
        merma = max(0, unidades_producidas - venta_total) if unidades_producidas > venta_total else 0
        
        produccion.append({
            'fecha': row['fecha'],
            'unidades_producidas': unidades_producidas,
            'unidades_vendidas': min(unidades_producidas, venta_total),
            'merma_unidades': merma,
            'capacidad_utilizada_pct': round((unidades_producidas / capacidad_max) * 100, 2)
            # COLUMNAS quiebre_stock Y clima_predominante ELIMINADAS POR REQUERIMIENTO
        })

    df_p = pd.DataFrame(produccion)
    output_path = os.path.join(DATOS_DIR, 'produccion.csv')
    df_p.to_csv(output_path, index=False)
    print(f"Generado {output_path} con {len(df_p)} días de producción (Limpio)")

if __name__ == "__main__":
    calcular_produccion()
