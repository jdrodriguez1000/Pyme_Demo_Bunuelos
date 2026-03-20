# Resumen de Lógica de Datos - Pyme Buñuelos

Este documento detalla todas las reglas de negocio, multiplicadores y lógica aplicada para la generación del dataset sintético.

## Estructura del Proyecto
- `src/`: Contiene los scripts de Python (.py) para generar y procesar datos.
- `datos/`: Contiene los archivos finales (.csv) generados.

## 1. Archivos Generados en `/datos`

### 1.1 Ventas (`ventas.csv`)
- **Frecuencia:** Horaria (6:00 AM - 6:00 PM).
- **Columnas:** Fecha, Unidades Vendidas, Unidades Pagadas, Unidades Bonificadas, Clima.
- **Lógica 2x1 (desde 2022):** 
    - Mayo y Sept/Oct (15 sep - 15 oct).
    - `unidades_pagadas` = `unidades_vendidas / 2`.
- **Cierre por Quiebre de Stock:** 15% de probabilidad diaria de cerrar antes de las 6 PM por falta de producción.

### 1.2 Producción (`produccion.csv`)
- **Frecuencia:** Diaria.
- **Lógica:** La producción suele ser entre 2% y 15% superior a la venta, excepto en días de quiebre de stock donde la producción es igual a la venta total.

### 1.3 Clima (`clima.csv`)
- **Frecuencia:** Horaria.
- **Estados:** Soleado (1.0x), Frío (1.5x), Lluvia Ligera (1.25x), Lluvia Fuerte (0.6x).
- **Consistencia:** El clima se mantiene estable en 3 bloques (Mañana, Mediodía, Tarde).

### 1.4 Publicidad (`publicidad.csv`)
- **Canales:** Facebook ($20k/día), Instagram ($30k/día), Volantes (Amortizado).
- **Impacto:** Las campañas inician 15 días antes de cada promoción (Fase de Expectativa), generando un impulso del +5% en ventas.

### 1.5 Macroeconomía
- **`macro_anual.csv`**: Salario Mínimo (SMMLV) con impacto positivo en consumo.
- **`macro_mensual.csv`**: Inflación (IPC) y Desempleo. Inflación > 10% reduce demanda en 5%.
- **`macro_diario.csv`**: TRM (Dólar) para trazabilidad de volatilidad.

---

## 2. Multiplicadores de Demanda

| Factor | Multiplicador / Regla |
| :--- | :--- |
| **Domingos / Festivos Religiosos** | 2.5x |
| **Sábados / Lunes Festivos** | 1.8x |
| **Lunes** | 1.4x |
| **Meses Pico (Dic, Ene, Jun, Jul)** | 2.0x |
| **Meses Valle** | 0.7x |
| **Quincenas (15, 16, 30, 31)** | +5% a 8% |
| **Prima (20-21 Jun/Dic)** | +5% a 8% |
| **Novenas (16-24 Dic)** | +10% a 18% |
| **Promo Mayo** | 1.6x |
| **Promo Sept/Oct** | 2.1x |
| **Fase Expectativa Publicidad** | 1.05x |
| **Estado Frío** | 1.5x |
| **Lluvia Fuerte** | 0.6x (Negativo) |

---

## 3. Crecimiento Anual (Tendencia)
- **2021-2022:** +21%
- **2022-2023:** +12%
- **2024-2025:** +11% (Proyectado)
- **2025-2026:** Estable
