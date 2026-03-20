import pandas as pd
import numpy as np
import os

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, '..', 'datos')
os.makedirs(DATOS_DIR, exist_ok=True)
FILE_PATH = os.path.join(DATOS_DIR, 'clima.csv')

def generate_clima_history(start, end, output_file):
    days = pd.date_range(start=start, end=end, freq='D')
    clima_rows = []
    states = ['Soleado', 'Frio', 'Lluvia Ligera', 'Lluvia Fuerte']
    
    for day in days:
        month = day.month
        if month in [1, 2, 12]: probs = [0.70, 0.15, 0.10, 0.05]
        elif month in [4, 5, 10, 11]: probs = [0.30, 0.20, 0.35, 0.15]
        else: probs = [0.50, 0.30, 0.15, 0.05]
        
        morning_state = np.random.choice(states, p=probs)
        midday_state = morning_state if np.random.rand() < 0.6 else np.random.choice(states, p=probs)
        afternoon_state = midday_state if np.random.rand() < 0.5 else np.random.choice(states, p=probs)
        
        for hour in range(6, 19):
            dt = day.replace(hour=hour)
            current_state = morning_state if hour <= 10 else (midday_state if hour <= 14 else afternoon_state)
            clima_rows.append({'fecha': dt, 'estado_clima': current_state})
    
    df_clima = pd.DataFrame(clima_rows)
    df_clima.to_csv(output_file, index=False)
    print(f"Generated {output_file} with blocks. Rows: {len(df_clima)}")

if __name__ == "__main__":
    generate_clima_history("2021-10-01", "2026-03-19", FILE_PATH)
