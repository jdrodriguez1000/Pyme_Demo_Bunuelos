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

# --- CONFIGURACIÓN DE INCOMPLETITUD ---
# (registros_faltantes%, campos_null%)
# Distribución: 30% registros faltantes, 70% campos NULL
INCOMPLETITUD = {
    'anual': (0.3, 0.7),          # usr_macro_anual: 0.3% faltantes + 0.7% NULL (total 1%)
    'mensual': (0.6, 1.4),        # usr_macro_mensual: 0.6% faltantes + 1.4% NULL (total 2%)
    'diario': (0.45, 2.55),       # usr_produccion, usr_macro_diario, usr_publicidad (total 3%)
    'horario': (0.9, 2.1)         # usr_clima, usr_ventas (total 3%)
}

# --- FUNCIONES DE UTILIDAD ---
def get_last_date_for_table(table_name, date_column='fecha'):
    """Obtiene la fecha del último registro en una tabla"""
    try:
        response = supabase.table(table_name).select(date_column).eq('pyme_id', PYME_ID).order(date_column, desc=True).limit(1).execute()
        if response.data:
            fecha_str = response.data[0][date_column]
            return pd.to_datetime(fecha_str).date()
        return None
    except:
        return None

def should_skip_record(incompletitud_type):
    """Decide si un registro debe omitirse (registros faltantes)"""
    pct_missing = INCOMPLETITUD[incompletitud_type][0]
    return np.random.rand() < (pct_missing / 100.0)

def should_null_field(incompletitud_type):
    """Decide si un campo específico debe ser NULL (campos incompletos)"""
    pct_null = INCOMPLETITUD[incompletitud_type][1]
    return np.random.rand() < (pct_null / 100.0)

def fetch_all_records(table_name, filters=None):
    """Obtiene todos los registros de una tabla con paginación (Supabase SDK limit es 1000)"""
    all_data = []
    page_size = 1000
    offset = 0

    while True:
        try:
            query = supabase.table(table_name).select("*")

            if filters:
                for filter_key, filter_val in filters.items():
                    if filter_key == 'eq':
                        for k, v in filter_val.items():
                            query = query.eq(k, v)
                    elif filter_key == 'gte':
                        for k, v in filter_val.items():
                            query = query.gte(k, v)
                    elif filter_key == 'lte':
                        for k, v in filter_val.items():
                            query = query.lte(k, v)

            response = query.offset(offset).limit(page_size).execute()

            if not response.data:
                break

            all_data.extend(response.data)
            offset += page_size

            if len(response.data) < page_size:
                break
        except Exception as e:
            print(f"Error fetching {table_name} at offset {offset}: {e}")
            break

    return all_data

# --- GENERACIÓN DE CLIMA ---
def generate_clima():
    """Genera clima para las horas faltantes"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    last_date = get_last_date_for_table('usr_clima', 'fecha')
    if last_date and last_date >= yesterday:
        print(f"usr_clima ya está al día hasta {yesterday}")
        return

    start_date = pd.Timestamp(2021, 10, 1).date() if not last_date else last_date + timedelta(days=1)

    if start_date > yesterday:
        print(f"usr_clima ya está al día. No hay datos nuevos hasta {yesterday}")
        return

    states = ['Soleado', 'Frio', 'Lluvia Ligera', 'Lluvia Fuerte']
    clima_payload = []

    dates = pd.date_range(start=start_date, end=yesterday, freq='D')
    for day in dates:
        month = day.month
        if month in [1, 2, 12]: probs = [0.70, 0.15, 0.10, 0.05]
        elif month in [4, 5, 10, 11]: probs = [0.30, 0.20, 0.35, 0.15]
        else: probs = [0.50, 0.30, 0.15, 0.05]

        morning_state = np.random.choice(states, p=probs)
        midday_state = morning_state if np.random.rand() < 0.6 else np.random.choice(states, p=probs)
        afternoon_state = midday_state if np.random.rand() < 0.5 else np.random.choice(states, p=probs)

        for hour in range(6, 18):  # 6 a 17 (inclusive)
            # Aplicar incompletitud (registros faltantes)
            if should_skip_record('horario'):
                continue

            dt = day.replace(hour=hour)
            current_state = morning_state if hour <= 10 else (midday_state if hour <= 14 else afternoon_state)
            clima_payload.append({
                'fecha': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'estado_clima': current_state,
                'pyme_id': PYME_ID
            })

    if clima_payload:
        for i in range(0, len(clima_payload), 500):
            supabase.table('usr_clima').insert(clima_payload[i:i+500]).execute()

    print(f"Se han agregado {len(clima_payload)} registros a 'usr_clima' hasta {yesterday}")

# --- GENERACIÓN DE MACROECONOMÍA ---
def generate_macro_anual():
    """Genera datos de salario mínimo anual"""
    anual_data = {2021: 908526, 2022: 1000000, 2023: 1160000, 2024: 1300000, 2025: 1417000, 2026: 1502000}

    existing_years = set()
    try:
        response = supabase.table('usr_macro_anual').select("fecha").eq('pyme_id', PYME_ID).execute()
        existing_years = {pd.to_datetime(r['fecha']).year for r in response.data}
    except:
        pass

    macro_payload = []
    for year in range(2021, 2027):
        if year not in existing_years:
            # Aplicar incompletitud (registros faltantes)
            if should_skip_record('anual'):
                continue

            # Campo smmlv puede ser NULL
            smmlv = None if should_null_field('anual') else anual_data.get(year, 1500000)

            macro_payload.append({
                'fecha': f"{year}-01-01",
                'smmlv': smmlv,
                'pyme_id': PYME_ID
            })

    if macro_payload:
        supabase.table('usr_macro_anual').insert(macro_payload).execute()

    print(f"Se han agregado {len(macro_payload)} registros a 'usr_macro_anual'")

def generate_macro_mensual():
    """Genera datos de inflación y desempleo mensuales"""
    today = datetime.now()
    target_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1) if today.day == 1 else today.replace(day=1)

    existing_months = set()
    try:
        response = supabase.table('usr_macro_mensual').select("fecha").eq('pyme_id', PYME_ID).execute()
        existing_months = {pd.to_datetime(r['fecha']).strftime('%Y-%m') for r in response.data}
    except:
        pass

    months = pd.date_range(start='2021-10-01', end=target_month, freq='MS')
    macro_payload = []

    for m in months:
        if m.strftime('%Y-%m') not in existing_months:
            # Aplicar incompletitud (registros faltantes)
            if should_skip_record('mensual'):
                continue

            if m.year < 2022: infl, unemp = 5.6, 11.0
            elif m.year == 2022: infl, unemp = np.random.uniform(9.0, 13.1), 10.5
            elif m.year == 2023: infl, unemp = np.random.uniform(10.0, 13.3), 9.8
            elif m.year == 2024: infl, unemp = np.random.uniform(5.5, 9.0), 10.2
            else: infl, unemp = np.random.uniform(3.5, 5.5), 9.5

            # Campos inflacion_anual y desempleo pueden ser NULL
            infl = None if should_null_field('mensual') else round(infl, 2)
            unemp = None if should_null_field('mensual') else round(unemp, 2)

            macro_payload.append({
                'fecha': m.strftime('%Y-%m-%d'),
                'inflacion_anual': infl,
                'desempleo': unemp,
                'pyme_id': PYME_ID
            })

    if macro_payload:
        supabase.table('usr_macro_mensual').insert(macro_payload).execute()

    print(f"Se han agregado {len(macro_payload)} registros a 'usr_macro_mensual'")

def generate_macro_diario():
    """Genera datos de TRM diario"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    last_date = get_last_date_for_table('usr_macro_diario', 'fecha')
    if last_date and last_date >= yesterday:
        print(f"usr_macro_diario ya está al día hasta {yesterday}")
        return

    try:
        last_rec = supabase.table('usr_macro_diario').select("fecha, trm").eq('pyme_id', PYME_ID).order('fecha', desc=True).limit(1).execute()
        if last_rec.data:
            start_date = pd.to_datetime(last_rec.data[0]['fecha']).date() + timedelta(days=1)
            current_trm = float(last_rec.data[0]['trm'])
        else:
            start_date, current_trm = pd.Timestamp(2021, 10, 1).date(), 3800.0
    except:
        start_date, current_trm = pd.Timestamp(2021, 10, 1).date(), 3800.0

    if start_date > yesterday:
        print(f"usr_macro_diario ya está al día. No hay datos nuevos hasta {yesterday}")
        return

    dates = pd.date_range(start=start_date, end=yesterday, freq='D')
    macro_payload = []

    for day in dates:
        # Aplicar incompletitud (registros faltantes)
        if should_skip_record('diario'):
            continue

        target_trm = 4300 if day < pd.Timestamp(2022, 11, 1) else (4800 if day < pd.Timestamp(2023, 7, 1) else (3900 if day < pd.Timestamp(2024, 6, 1) else 4100))
        volatility = np.random.normal(0, 15)
        current_trm = current_trm * 0.99 + target_trm * 0.01 + volatility

        # Campo trm puede ser NULL
        trm = None if should_null_field('diario') else round(current_trm, 2)

        macro_payload.append({
            'fecha': day.strftime('%Y-%m-%d'),
            'trm': trm,
            'pyme_id': PYME_ID
        })

    if macro_payload:
        for i in range(0, len(macro_payload), 500):
            supabase.table('usr_macro_diario').insert(macro_payload[i:i+500]).execute()

    print(f"Se han agregado {len(macro_payload)} registros a 'usr_macro_diario' hasta {yesterday}")

# --- GENERACIÓN DE VENTAS ---
def generate_ventas():
    """Genera datos de ventas horarias con patrones correctos"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    last_date = get_last_date_for_table('usr_ventas', 'fecha')
    if last_date and last_date >= yesterday:
        print(f"usr_ventas ya está al día hasta {yesterday}")
        return

    start_date = pd.Timestamp(2021, 10, 1).date() if not last_date else last_date + timedelta(days=1)

    if start_date > yesterday:
        print(f"usr_ventas ya está al día. No hay datos nuevos hasta {yesterday}")
        return

    # Cargar clima con paginación
    try:
        all_clima = []
        offset = 0
        while True:
            response = supabase.table('usr_clima').select("fecha, estado_clima").eq('pyme_id', PYME_ID).gte('fecha', f"{start_date} 00:00:00").lte('fecha', f"{yesterday} 23:59:59").offset(offset).limit(1000).execute()
            if not response.data:
                break
            all_clima.extend(response.data)
            offset += 1000
            if len(response.data) < 1000:
                break

        clima_map = {}
        for r in all_clima:
            fecha_dt = pd.to_datetime(r['fecha'])
            key = (fecha_dt.date(), fecha_dt.hour)
            clima_map[key] = r['estado_clima']
    except Exception as e:
        print(f"   [WARNING] Clima no disponible: {e}")
        clima_map = {}

    try:
        all_macro = []
        offset = 0
        while True:
            response = supabase.table('usr_macro_anual').select("fecha, smmlv").eq('pyme_id', PYME_ID).offset(offset).limit(1000).execute()
            if not response.data:
                break
            all_macro.extend(response.data)
            offset += 1000
            if len(response.data) < 1000:
                break

        smmlv_dict = {pd.to_datetime(r['fecha']).year: float(r['smmlv']) if r['smmlv'] else 1300000 for r in all_macro}
    except Exception as e:
        print(f"   [WARNING] Macro anual no disponible: {e}")
        smmlv_dict = {}

    dates = pd.date_range(start=start_date, end=yesterday, freq='D')
    ventas_payload = []

    for day_ts in dates:
        day = day_ts.date()

        # Determinar si hay quiebre de stock
        has_stockout = np.random.rand() < 0.15  # 15% de probabilidad
        if has_stockout:
            # Distribuir hora del cierre: 60% hora 17, 30% hora 16, 10% hora 15
            rand = np.random.rand()
            if rand < 0.60:
                stockout_hour = 17
            elif rand < 0.90:
                stockout_hour = 16
            else:
                stockout_hour = 15
        else:
            stockout_hour = None

        # Multiplicadores del día
        day_mult = 1.3 if day.weekday() in [5, 6] else 1.0
        if day in co_holidays:
            day_mult = 1.5

        year_val = smmlv_dict.get(day.year, 1300000)
        macro_mult = (year_val / 877803) * 0.8 + 0.2

        # Determinar si es período de promoción
        is_promo_period = (day.month == 5) or (day.month == 9 and day.day >= 15) or (day.month == 10 and day.day <= 15)

        # Generar ventas por hora
        for h in range(6, 18):  # 6 a 17 (inclusive)
            # Aplicar incompletitud (registros faltantes)
            if should_skip_record('horario'):
                continue

            # Si hay quiebre de stock y estamos en o después de esa hora
            if stockout_hour is not None and h >= stockout_hour:
                total_sold = 0
                promocion = 0
            else:
                # Clima multiplicador (mejorado)
                weather_cond = clima_map.get((day, h), 'Soleado')
                if weather_cond == 'Lluvia Fuerte':
                    weather_mult = 0.6
                elif weather_cond == 'Lluvia Ligera':
                    weather_mult = 1.25
                elif weather_cond == 'Frio':
                    weather_mult = 1.5
                else:  # Soleado
                    weather_mult = 1.0

                # Base demanda
                base_demand = 15 if (7 <= h <= 9 or 15 <= h <= 16) else 8

                total_sold = int(base_demand * day_mult * weather_mult * macro_mult)

                # Promociones
                if is_promo_period:
                    # En período de promo: igual número de unidades bonificadas que pagadas
                    promocion = total_sold
                elif day.weekday() == 4:  # Viernes
                    # 10% de bonificadas
                    promocion = int(total_sold * 0.1)
                else:
                    promocion = 0

            ventas_payload.append({
                'fecha': f"{day} {h:02d}:00:00",
                'unidades_vendidas': total_sold + promocion,
                'unidades_pagadas': total_sold,
                'unidades_bonificadas': promocion,
                'pyme_id': PYME_ID
            })

    if ventas_payload:
        for i in range(0, len(ventas_payload), 500):
            supabase.table('usr_ventas').insert(ventas_payload[i:i+500]).execute()

    print(f"Se han agregado {len(ventas_payload)} registros a 'usr_ventas' hasta {yesterday}")

# --- GENERACIÓN DE PRODUCCIÓN ---
def generate_produccion():
    """Genera datos de producción diaria vinculada a ventas"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    last_date = get_last_date_for_table('usr_produccion', 'fecha')
    if last_date and last_date >= yesterday:
        print(f"usr_produccion ya está al día hasta {yesterday}")
        return

    start_date = pd.Timestamp(2021, 10, 1).date() if not last_date else last_date + timedelta(days=1)

    if start_date > yesterday:
        print(f"usr_produccion ya está al día. No hay datos nuevos hasta {yesterday}")
        return

    # Cargar ventas con paginación (Supabase SDK tiene límite de 1000)
    try:
        all_ventas = []
        offset = 0
        while True:
            query = supabase.table('usr_ventas').select("fecha, unidades_vendidas").eq('pyme_id', PYME_ID).gte('fecha', f"{start_date} 00:00:00").lte('fecha', f"{yesterday} 23:59:59").offset(offset).limit(1000)
            response = query.execute()
            if not response.data:
                break
            all_ventas.extend(response.data)
            offset += 1000
            if len(response.data) < 1000:
                break

        print(f"   [DEBUG] Total registros de ventas: {len(all_ventas)}")
        df_v = pd.DataFrame(all_ventas)
        df_v['fecha_dia'] = pd.to_datetime(df_v['fecha']).dt.date
        diario = df_v.groupby('fecha_dia')['unidades_vendidas'].sum().reset_index()
        print(f"   [DEBUG] Días únicos en ventas agrupadas: {len(diario)}")
    except Exception as e:
        print(f"   [ERROR] Carga de ventas falló: {e}")
        diario = pd.DataFrame(columns=['fecha_dia', 'unidades_vendidas'])

    produccion_payload = []
    capacidad_max = 200

    for _, row in diario.iterrows():
        # Aplicar incompletitud (registros faltantes)
        if should_skip_record('diario'):
            continue

        venta_total = row['unidades_vendidas']
        prod_estimada = int(min(capacidad_max, venta_total * 1.05))
        vendidas_reales = min(prod_estimada, venta_total)
        sobrantes = max(0, prod_estimada - venta_total)
        merma_pct = round((sobrantes / prod_estimada) * 100, 2) if prod_estimada > 0 else 0

        # Campo porcentaje_merma puede ser NULL
        merma_pct = None if should_null_field('diario') else merma_pct

        produccion_payload.append({
            'fecha': row['fecha_dia'].strftime('%Y-%m-%d'),
            'unidades_vendidas': vendidas_reales,
            'produccion_estimada': prod_estimada,
            'unidades_sobrantes': sobrantes,
            'porcentaje_merma': merma_pct,
            'pyme_id': PYME_ID
        })

    if produccion_payload:
        for i in range(0, len(produccion_payload), 500):
            supabase.table('usr_produccion').insert(produccion_payload[i:i+500]).execute()

    print(f"Se han agregado {len(produccion_payload)} registros a 'usr_produccion' hasta {yesterday}")

# --- GENERACIÓN DE PUBLICIDAD ---
def generate_publicidad():
    """Genera datos de publicidad para campañas anuales"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    try:
        response = supabase.table('usr_publicidad').select("fecha").eq('pyme_id', PYME_ID).execute()
        existing_dates = {pd.to_datetime(r['fecha']).date() for r in response.data}
    except:
        existing_dates = set()

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
                    # Aplicar incompletitud (registros faltantes)
                    if should_skip_record('diario'):
                        continue

                    # Campos pueden ser NULL individualmente
                    campaña = None if should_null_field('diario') else name
                    pauta_facebook = None if should_null_field('diario') else fb_daily
                    pauta_instagram = None if should_null_field('diario') else ig_daily
                    volantes_impresos = None if should_null_field('diario') else daily_printed

                    # total_diario se calcula solo si hay al menos un valor
                    if pauta_facebook is not None or pauta_instagram is not None or volantes_impresos is not None:
                        total_diario = (pauta_facebook or 0) + (pauta_instagram or 0) + (volantes_impresos or 0)
                    else:
                        total_diario = None

                    publicidad_payload.append({
                        'fecha': str(d),
                        'campaña': campaña,
                        'pauta_facebook': pauta_facebook,
                        'pauta_instagram': pauta_instagram,
                        'volantes_impresos': volantes_impresos,
                        'total_diario': total_diario,
                        'pyme_id': PYME_ID
                    })

    if publicidad_payload:
        for i in range(0, len(publicidad_payload), 500):
            supabase.table('usr_publicidad').insert(publicidad_payload[i:i+500]).execute()

    print(f"Se han agregado {len(publicidad_payload)} registros a 'usr_publicidad'. Tabla sincronizada.")

# --- MAIN ---
if __name__ == "__main__":
    print("=== INICIANDO REGENERACIÓN COMPLETA DE DATOS ===\n")

    # Orden respetando dependencias
    generate_clima()
    print()
    generate_macro_anual()
    print()
    generate_macro_mensual()
    print()
    generate_macro_diario()
    print()
    generate_ventas()
    print()
    generate_produccion()
    print()
    generate_publicidad()

    print("\n=== PROCESO COMPLETADO ===")
