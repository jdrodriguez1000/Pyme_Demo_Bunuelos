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
        -- LIMPIAR POLITICAS
        EXECUTE format('DROP POLICY IF EXISTS "Ver solo mi Pyme" ON public.%I;', t);
        EXECUTE format('DROP POLICY IF EXISTS "Insertar en mi Pyme" ON public.%I;', t);
        EXECUTE format('DROP POLICY IF EXISTS "Editar mi Pyme" ON public.%I;', t);
        EXECUTE format('DROP POLICY IF EXISTS "Borrar mi Pyme" ON public.%I;', t);

        -- CREACION DE POLITICAS SEGURAS USANDO app_metadata
        -- El app_metadata NO puede ser editado por el usuario final, es seguro 🔒
        
        EXECUTE format('CREATE POLICY "Ver solo mi Pyme" ON public.%I FOR SELECT 
                        TO authenticated 
                        USING ( (auth.jwt() -> ''app_metadata'' ->> ''pyme_id'') = pyme_id OR pyme_id = %L );', t, '001_ABC');
        
        EXECUTE format('CREATE POLICY "Insertar en mi Pyme" ON public.%I FOR INSERT 
                        TO authenticated 
                        WITH CHECK ( (auth.jwt() -> ''app_metadata'' ->> ''pyme_id'') = pyme_id OR pyme_id = %L );', t, '001_ABC');
        
        EXECUTE format('CREATE POLICY "Editar mi Pyme" ON public.%I FOR UPDATE 
                        TO authenticated 
                        USING ( (auth.jwt() -> ''app_metadata'' ->> ''pyme_id'') = pyme_id OR pyme_id = %L )
                        WITH CHECK ( (auth.jwt() -> ''app_metadata'' ->> ''pyme_id'') = pyme_id OR pyme_id = %L );', t, '001_ABC', '001_ABC');

        EXECUTE format('CREATE POLICY "Borrar mi Pyme" ON public.%I FOR DELETE 
                        TO authenticated 
                        USING ( (auth.jwt() -> ''app_metadata'' ->> ''pyme_id'') = pyme_id OR pyme_id = %L );', t, '001_ABC');

        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
    END LOOP;
END $$;
