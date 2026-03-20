import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# Intentar importar holidays para Colombia
try:
    import holidays
    co_holidays = holidays.Colombia()
except ImportError:
    co_holidays = []

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, '..', '.env')
load_dotenv(DOTENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
PYME_ID = '001_ABC'

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: No se encontraron las credenciales")
    exit()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_daily_weather():
    """Genera clima para ayer (X-1) siguiendo exactamente la lógica de clima.py"""
    today = datetime.now()
    yesterday_date = today - timedelta(days=1)
    yesterday_str = yesterday_date.strftime('%Y-%m-%d')
    try:
        response = supabase.table('usr_clima').select("fecha").eq('pyme_id', PYME_ID).gte('fecha', f"{yesterday_str} 06:00:00").lte('fecha', f"{yesterday_str} 18:00:00").execute()
        existing_hours = [pd.to_datetime(r['fecha']).hour for r in response.data]
    except: existing_hours = []

    states = ['Soleado', 'Frio', 'Lluvia Ligera', 'Lluvia Fuerte']
    month = yesterday_date.month
    probs = [0.70, 0.15, 0.10, 0.05] if month in [1, 2, 12] else ([0.30, 0.20, 0.35, 0.15] if month in [4, 5, 10, 11] else [0.50, 0.30, 0.15, 0.05])
    
    morning_state = np.random.choice(states, p=probs)
    midday_state = morning_state if np.random.rand() < 0.6 else np.random.choice(states, p=probs)
    afternoon_state = midday_state if np.random.rand() < 0.5 else np.random.choice(states, p=probs)
    
    clima_payload = [{'fecha': f"{yesterday_str} {h:02d}:00:00", 'estado_clima': morning_state if h <= 10 else (midday_state if h <= 14 else afternoon_state), 'pyme_id': PYME_ID} for h in range(6, 19) if h not in existing_hours]
    if clima_payload: supabase.table('usr_clima').insert(clima_payload).execute()
    max_res = supabase.table('usr_clima').select("fecha").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
    print(f"Se han agregado {len(clima_payload)} registros a 'usr_clima'. Tabla actualizada hasta la fecha: {max_res.data[0]['fecha'] if max_res.data else yesterday_str}")

def upload_annual_macro():
    """Actualiza la tabla usr_macro_anual"""
    today = datetime.now()
    target_year = today.year if not (today.month == 1 and today.day == 1) else today.year - 1
    anual_data = {2021: 908526, 2022: 1000000, 2023: 1160000, 2024: 1300000, 2025: 1417000, 2026: 1502000}
    try:
        response = supabase.table('usr_macro_anual').select("fecha").eq('pyme_id', PYME_ID).execute()
        existing_years = [pd.to_datetime(r['fecha']).year for r in response.data]
    except: existing_years = []
    macro_payload = [{'fecha': f"{year}-01-01", 'smmlv': anual_data.get(year, 1500000), 'pyme_id': PYME_ID} for year in range(2021, target_year + 1) if year not in existing_years]
    if macro_payload: supabase.table('usr_macro_anual').insert(macro_payload).execute()
    max_res = supabase.table('usr_macro_anual').select("fecha").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
    print(f"Se han agregado {len(macro_payload)} registros a 'usr_macro_anual'. Tabla actualizada hasta la fecha: {max_res.data[0]['fecha'] if max_res.data else 'Sin datos'}")

def upload_daily_macro():
    """Actualiza la tabla usr_macro_diario"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    try:
        last_rec = supabase.table('usr_macro_diario').select("fecha, trm").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
        if last_rec.data:
            start_date = pd.to_datetime(last_rec.data[0]['fecha']).date() + timedelta(days=1)
            current_trm = float(last_rec.data[0]['trm'])
        else:
            start_date, current_trm = pd.Timestamp(2021, 10, 1).date(), 3800.0
    except: start_date, current_trm = pd.Timestamp(2021, 10, 1).date(), 3800.0
    if start_date > yesterday:
        print(f"Se han agregado 0 registros a 'usr_macro_diario'. Tabla actualizada hasta la fecha: {yesterday}")
        return
    dates = pd.date_range(start=start_date, end=yesterday, freq='D')
    macro_payload = [{'fecha': day.strftime('%Y-%m-%d'), 'trm': round(current_trm := current_trm * 0.99 + (4300 if day < pd.Timestamp(2022, 11, 1) else (4800 if day < pd.Timestamp(2023, 7, 1) else (3900 if day < pd.Timestamp(2024, 6, 1) else 4100))) * 0.01 + np.random.normal(0, 15), 2), 'pyme_id': PYME_ID} for day in dates]
    if macro_payload:
        for i in range(0, len(macro_payload), 500): supabase.table('usr_macro_diario').insert(macro_payload[i:i+500]).execute()
    print(f"Se han agregado {len(macro_payload)} registros a 'usr_macro_diario'. Tabla actualizada hasta la fecha: {yesterday}")

def upload_monthly_macro():
    """Actualiza la tabla usr_macro_mensual"""
    today = datetime.now()
    target_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1) if today.day == 1 else today.replace(day=1)
    try:
        response = supabase.table('usr_macro_mensual').select("fecha").eq('pyme_id', PYME_ID).execute()
        existing_months = [pd.to_datetime(r['fecha']).strftime('%Y-%m-%d') for r in response.data]
    except: existing_months = []
    months = pd.date_range(start='2021-10-01', end=target_month, freq='MS')
    macro_payload = []
    for m in months:
        if m.strftime('%Y-%m-%d') not in existing_months:
            if m.year < 2022: infl, unemp = 5.6, 11.0
            elif m.year == 2022: infl, unemp = np.random.uniform(9.0, 13.1), 10.5
            elif m.year == 2023: infl, unemp = np.random.uniform(10.0, 13.3), 9.8
            elif m.year == 2024: infl, unemp = np.random.uniform(5.5, 9.0), 10.2
            else: infl, unemp = np.random.uniform(3.5, 5.5), 9.5
            macro_payload.append({'fecha': m.strftime('%Y-%m-%d'), 'inflacion_anual': round(infl, 2), 'desempleo': round(unemp, 2), 'pyme_id': PYME_ID})
    if macro_payload: supabase.table('usr_macro_mensual').insert(macro_payload).execute()
    max_res = supabase.table('usr_macro_mensual').select("fecha").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
    print(f"Se han agregado {len(macro_payload)} registros a 'usr_macro_mensual'. Tabla actualizada hasta la fecha: {max_res.data[0]['fecha'] if max_res.data else target_month.strftime('%Y-%m-%d')}")

def upload_daily_ventas():
    """Actualiza la tabla usr_ventas"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    try:
        last_rec = supabase.table('usr_ventas').select("fecha").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
        start_date = pd.to_datetime(last_rec.data[0]['fecha']).date() + timedelta(days=1) if last_rec.data else pd.Timestamp(2021, 10, 1).date()
    except: start_date = pd.Timestamp(2021, 10, 1).date()
    if start_date > yesterday:
        print(f"Se han agregado 0 registros a 'usr_ventas'. Tabla actualizada hasta la fecha: {yesterday}")
        return
    try:
        macro_res = supabase.table('usr_macro_anual').select("fecha, smmlv").eq('pyme_id', PYME_ID).execute()
        smmlv_dict = {pd.to_datetime(r['fecha']).year: float(r['smmlv']) for r in macro_res.data}
    except: smmlv_dict = {}
    dates = pd.date_range(start=start_date, end=yesterday, freq='D')
    ventas_payload = []
    for day_ts in dates:
        day = day_ts.date()
        day_mult = 1.3 if day.weekday() in [5, 6] else 1.0
        if day in co_holidays: day_mult = 1.5
        year_val = smmlv_dict.get(day.year, 1300000)
        macro_mult = (year_val / 877803) * 0.8 + 0.2
        try:
            clima_res = supabase.table('usr_clima').select("fecha, estado_clima").eq('pyme_id', PYME_ID).gte('fecha', f"{day} 00:00:00").lte('fecha', f"{day} 23:59:59").execute()
            clima_map = {pd.to_datetime(r['fecha']).hour: r['estado_clima'] for r in clima_res.data}
        except: clima_map = {}
        is_promo_period = (day.month == 5) or (day.month == 9 and day.day >= 15) or (day.month == 10 and day.day <= 15)
        for h in range(6, 19):
            weather_cond = clima_map.get(h, 'Soleado')
            weather_mult = 1.25 if 'Lluvia' in weather_cond else 1.0
            base_demand = 15 if (7 <= h <= 9 or 15 <= h <= 16) else 8
            total_sold = int(base_demand * day_mult * weather_mult * macro_mult)
            promocion = total_sold if is_promo_period else (int(total_sold * 0.1) if day.weekday() == 4 else 0)
            ventas_payload.append({'fecha': f"{day} {h:02d}:00:00", 'unidades_vendidas': total_sold + promocion, 'unidades_pagadas': total_sold, 'unidades_bonificadas': promocion, 'pyme_id': PYME_ID})
    if ventas_payload:
        for i in range(0, len(ventas_payload), 500): supabase.table('usr_ventas').insert(ventas_payload[i:i+500]).execute()
    print(f"Se han agregado {len(ventas_payload)} registros a 'usr_ventas'. Tabla actualizada hasta la fecha: {yesterday}")

def upload_daily_produccion():
    """Actualiza la tabla usr_produccion vinculada a las ventas diarias"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    try:
        last_rec = supabase.table('usr_produccion').select("fecha").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
        start_date = pd.to_datetime(last_rec.data[0]['fecha']).date() + timedelta(days=1) if last_rec.data else pd.Timestamp(2021, 10, 1).date()
    except: start_date = pd.Timestamp(2021, 10, 1).date()
    if start_date > yesterday:
        print(f"Se han agregado 0 registros a 'usr_produccion'. Tabla actualizada hasta la fecha: {yesterday}")
        return
    try:
        ventas_res = supabase.table('usr_ventas').select("fecha, unidades_vendidas").eq('pyme_id', PYME_ID).gte('fecha', f"{start_date} 00:00:00").execute()
        df_v = pd.DataFrame(ventas_res.data)
        df_v['fecha_dia'] = pd.to_datetime(df_v['fecha']).dt.date
        diario = df_v.groupby('fecha_dia')['unidades_vendidas'].sum().reset_index()
    except: diario = pd.DataFrame(columns=['fecha_dia', 'unidades_vendidas'])
    produccion_payload = []
    capacidad_max = 200
    for _, row in diario.iterrows():
        venta_total = row['unidades_vendidas']
        prod_estimada = int(min(capacidad_max, venta_total * 1.05))
        vendidas_reales = min(prod_estimada, venta_total)
        sobrantes = max(0, prod_estimada - venta_total)
        merma_pct = round((sobrantes / prod_estimada) * 100, 2) if prod_estimada > 0 else 0
        produccion_payload.append({'fecha': row['fecha_dia'].strftime('%Y-%m-%d'), 'unidades_vendidas': vendidas_reales, 'produccion_estimada': prod_estimada, 'unidades_sobrantes': sobrantes, 'porcentaje_merma': merma_pct, 'pyme_id': PYME_ID})
    if produccion_payload:
        for i in range(0, len(produccion_payload), 500): supabase.table('usr_produccion').insert(produccion_payload[i:i+500]).execute()
    print(f"Se han agregado {len(produccion_payload)} registros a 'usr_produccion'. Tabla actualizada hasta la fecha: {yesterday}")

def upload_daily_publicidad():
    """Actualiza la tabla usr_publicidad basada en las campañas de publicidad.py"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    try:
        response = supabase.table('usr_publicidad').select("fecha").eq('pyme_id', PYME_ID).execute()
        existing_dates = {pd.to_datetime(r['fecha']).date() for r in response.data}
    except: existing_dates = set()

    publicidad_payload = []
    fb_daily, ig_daily = 20000, 30000
    
    for year in range(2021, 2027):
        camp1_range = pd.date_range(pd.Timestamp(year, 4, 16), pd.Timestamp(year, 5, 31))
        camp2_range = pd.date_range(pd.Timestamp(year, 8, 31), pd.Timestamp(year, 10, 15))
        
        for camp_days, name, printed_total in [(camp1_range, 'Promo Mayo', 250000), (camp2_range, 'Promo Sept/Oct', 380000)]:
            duration = len(camp_days)
            daily_printed = round(printed_total / duration, 2)
            for day in camp_days:
                d = day.date()
                if d <= yesterday and d not in existing_dates:
                    total_diario = fb_daily + ig_daily + daily_printed
                    # Usando los nombres de columna correctos del SQL: campaña (con ñ)
                    publicidad_payload.append({
                        'fecha': str(d),
                        'campaña': name,
                        'pauta_facebook': fb_daily,
                        'pauta_instagram': ig_daily,
                        'volantes_impresos': daily_printed,
                        'total_diario': total_diario,
                        'pyme_id': PYME_ID
                    })

    if publicidad_payload:
        for i in range(0, len(publicidad_payload), 500):
            supabase.table('usr_publicidad').insert(publicidad_payload[i:i+500]).execute()

    print(f"Se han agregado {len(publicidad_payload)} registros a 'usr_publicidad'. Tabla sincronizada.")

if __name__ == "__main__":
    upload_daily_weather()
    upload_annual_macro()
    upload_daily_macro()
    upload_monthly_macro()
    upload_daily_ventas()
    upload_daily_produccion()
    upload_daily_publicidad()
