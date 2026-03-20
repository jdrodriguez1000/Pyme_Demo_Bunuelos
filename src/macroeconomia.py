import pandas as pd
import numpy as np
import os

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, '..', 'datos')
os.makedirs(DATOS_DIR, exist_ok=True)

def generate_macro_data(start_date, end_date):
    dates_daily = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # SALARIO MINIMO (Anual)
    anual_data = {'fecha': ['2021-01-01', '2022-01-01', '2023-01-01', '2024-01-01', '2025-01-01', '2026-01-01'],
                  'smmlv': [908526, 1000000, 1160000, 1300000, 1417000, 1502000]}
    df_anual = pd.DataFrame(anual_data)
    df_anual.to_csv(os.path.join(DATOS_DIR, 'macro_anual.csv'), index=False)
    
    # INFLACION Y DESEMPLEO (Mensual)
    months = pd.date_range(start='2021-10-01', end=end_date, freq='MS')
    mensual_rows = []
    for month in months:
        if month.year < 2022: infl, unemp = 5.6, 11.0
        elif month.year == 2022: infl, unemp = np.random.uniform(9.0, 13.1), 10.5
        elif month.year == 2023: infl, unemp = np.random.uniform(10.0, 13.3), 9.8
        elif month.year == 2024: infl, unemp = np.random.uniform(5.5, 9.0), 10.2
        else: infl, unemp = np.random.uniform(3.5, 5.5), 9.5
        mensual_rows.append({'fecha': month, 'inflacion_anual': round(infl,2), 'desempleo': round(unemp,2)})
    df_mensual = pd.DataFrame(mensual_rows)
    df_mensual.to_csv(os.path.join(DATOS_DIR, 'macro_mensual.csv'), index=False)
    
    # TRM (Diaria)
    diario_rows = []
    current_trm = 3800
    for day in dates_daily:
        target_trm = 4300 if day < pd.Timestamp(2022, 11, 1) else (4800 if day < pd.Timestamp(2023, 7, 1) else (3900 if day < pd.Timestamp(2024, 6, 1) else 4100))
        volatility = np.random.normal(0, 15)
        current_trm = current_trm * 0.99 + target_trm * 0.01 + volatility
        diario_rows.append({'fecha': day.date(), 'trm': round(current_trm, 2)})
    df_diario = pd.DataFrame(diario_rows)
    df_diario.to_csv(os.path.join(DATOS_DIR, 'macro_diario.csv'), index=False)
    
    print("Files macro_anual, macro_mensual, and macro_diario generated in datos/.")

if __name__ == "__main__":
    generate_macro_data("2021-10-01", "2026-03-19")
