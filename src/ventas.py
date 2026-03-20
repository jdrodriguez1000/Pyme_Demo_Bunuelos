import os
import pandas as pd
from datetime import datetime, timedelta
import holidays

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, '..', 'datos')

if not os.path.exists(DATOS_DIR):
    os.makedirs(DATOS_DIR)

# Generación de fechas (2020 - Mayo 2024)
start_date = datetime(2020, 1, 1)
end_date = datetime(2024, 5, 20)
co_holidays = holidays.Colombia()

# Cargar datos externos
clima_path = os.path.join(DATOS_DIR, 'clima.csv')
macro_anual_path = os.path.join(DATOS_DIR, 'macro_anual.csv')
macro_mensual_path = os.path.join(DATOS_DIR, 'macro_mensual.csv')
macro_diario_path = os.path.join(DATOS_DIR, 'macro_diario.csv')

def load_data():
    clima = pd.read_csv(clima_path)
    clima['fecha_hora'] = pd.to_datetime(clima['fecha_hora'])
    m_anual = pd.read_csv(macro_anual_path)
    m_mensual = pd.read_csv(macro_mensual_path)
    m_diario = pd.read_csv(macro_diario_path)
    return clima, m_anual, m_mensual, m_diario

clima_df, m_anual, m_mensual, m_diario = load_data()

# Lógica de ventas
ventas = []
current = start_date

while current <= end_date:
    # Multiplicador día de la semana
    day_mult = 1.3 if current.weekday() in [5, 6] else 1.0 # Fin de semana
    if current in co_holidays: day_mult = 1.5
    
    # Factores Macro (Normalizados)
    year_val = m_anual[m_anual['anio'] == current.year]['smmlv_pesos'].values[0]
    macro_mult = (year_val / 877803) * 0.8 + 0.2 # Referencia 2020
    
    for hora in range(6, 17):
        # Clima en esta hora
        c_hora = clima_df[(clima_df['fecha_hora'].dt.date == current.date()) & (clima_df['fecha_hora'].dt.hour == hora)]
        weather_cond = c_hora['clima'].values[0] if not c_hora.empty else 'Despejado'
        
        # Multiplicador Clima
        weather_mult = 1.25 if weather_cond == 'Lluvioso' else 1.0 # Más buñuelos si llueve
        
        # Base de ventas aleatoria por hora
        base_demand = 15 if (7 <= hora <= 9 or 15 <= hora <= 16) else 8
        
        total_sold = int(base_demand * day_mult * weather_mult * macro_mult)
        
        # Promociones (Viernes 2x1 simulado)
        promocion = 0
        if current.weekday() == 4: # Viernes
            promocion = int(total_sold * 0.1)
            
        ventas.append({
            'fecha_hora': current.replace(hour=hora).strftime('%Y-%m-%d %H:%M:%S'),
            'total_unidades': total_sold + promocion,
            'unidades_pagas': total_sold,
            'unidades_bonificadas': promocion
        })
        
    current += timedelta(days=1)

df_ventas = pd.DataFrame(ventas)
output_path = os.path.join(DATOS_DIR, 'ventas.csv')
df_ventas.to_csv(output_path, index=False)

print(f"Generado {output_path} con {len(df_ventas)} registros")
