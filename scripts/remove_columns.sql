-- LIMPIEZA DE COLUMNAS NO DESEADAS EN SUPABASE
-- Ejecuta este script en el editor SQL de Supabase antes de volver a cargar los datos.

-- 1. Tabla usr_ventas: Eliminar el campo clima
ALTER TABLE public.usr_ventas DROP COLUMN IF EXISTS clima;

-- 2. Tabla usr_produccion: Eliminar quiebre_stock y clima_predominante
ALTER TABLE public.usr_produccion DROP COLUMN IF EXISTS quiebre_stock;
ALTER TABLE public.usr_produccion DROP COLUMN IF EXISTS clima_predominante;
