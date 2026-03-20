-- SCRIPT DE SEGURIDAD (RLS) - SUPABASE (TABLAS usr_)

-- ACTIVAR RLS
ALTER TABLE IF EXISTS public.usr_ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usr_produccion ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usr_clima ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usr_publicidad ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usr_macro_anual ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usr_macro_mensual ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.usr_macro_diario ENABLE ROW LEVEL SECURITY;

-- POLITICAS DE CRUD PARA USUARIOS AUTENTICADOS
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'usr_%'
    LOOP
        EXECUTE format('CREATE POLICY "Permitir lectura para autenticados" ON %I FOR SELECT TO authenticated USING (true);', t);
        EXECUTE format('CREATE POLICY "Permitir insercion para autenticados" ON %I FOR INSERT TO authenticated WITH CHECK (true);', t);
        EXECUTE format('CREATE POLICY "Permitir actualizacion para autenticados" ON %I FOR UPDATE TO authenticated USING (true) WITH CHECK (true);', t);
        EXECUTE format('CREATE POLICY "Permitir eliminacion para autenticados" ON %I FOR DELETE TO authenticated USING (true);', t);
    END LOOP;
END $$;
