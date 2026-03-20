import pandas as pd
import numpy as np
import os

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, '..', 'datos')
os.makedirs(DATOS_DIR, exist_ok=True)
FILE_PATH = os.path.join(DATOS_DIR, 'publicidad.csv')

def generate_marketing_expenses(start_year, end_year, output_file):
    all_marketing_rows = []
    
    for year in range(start_year, end_year + 1):
        camp1_start, camp1_end = pd.Timestamp(year, 4, 16), pd.Timestamp(year, 5, 31)
        camp1_days = pd.date_range(camp1_start, camp1_end)
        camp1_duration = len(camp1_days)
        
        camp2_start, camp2_end = pd.Timestamp(year, 8, 31), pd.Timestamp(year, 10, 15)
        camp2_days = pd.date_range(camp2_start, camp2_end)
        camp2_duration = len(camp2_days)
        
        fb_daily, ig_daily = 20000, 30000
        printed_total_1, printed_total_2 = 250000, 380000
        
        for day in camp1_days:
            daily_printed = printed_total_1 / camp1_duration
            all_marketing_rows.append({'fecha': day.date(), 'campaña': 'Promo Mayo', 'pauta_facebook': fb_daily, 'pauta_instagram': ig_daily, 'volantes_impresos': round(daily_printed, 2), 'total_diario': fb_daily + ig_daily + round(daily_printed, 2)})
            
        for day in camp2_days:
            daily_printed = printed_total_2 / camp2_duration
            all_marketing_rows.append({'fecha': day.date(), 'campaña': 'Promo Sept/Oct', 'pauta_facebook': fb_daily, 'pauta_instagram': ig_daily, 'volantes_impresos': round(daily_printed, 2), 'total_diario': fb_daily + ig_daily + round(daily_printed, 2)})
            
    df_marketing = pd.DataFrame(all_marketing_rows)
    df_marketing.to_csv(output_file, index=False)
    print(f"Generated {output_file} from {start_year} to {end_year}.")

if __name__ == "__main__":
    generate_marketing_expenses(2022, 2026, FILE_PATH)
