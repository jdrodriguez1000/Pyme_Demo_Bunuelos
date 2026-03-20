# Reglas del Proyecto - Pyme Demo Buñuelos

Este archivo contiene las normas y directrices obligatorias para el desarrollo y mantenimiento de este proyecto.

## 1. Gestión de Control de Versiones (Git/GitHub)

- **Prohibición de Commits Directos a `main`:** Está estrictamente prohibido realizar commits directamente a la rama `main`.
- **Ramas de Trabajo:** Todo cambio, corrección o nueva funcionalidad debe implementarse en una rama de trabajo independiente (ej. `feature/nombre-tarea`, `fix/descripcion-error`).
- **Flujo de Trabajo:** Un cambio solo debe integrarse a `main` mediante un Pull Request (PR) o una vez que haya sido validado.

## 2. Ingesta de Datos y Supabase

- **Sincronización:** Los scripts de carga diaria (`upload_daily.py`) deben respetar estrictamente la lógica definida en los archivos de la carpeta `src/`.
- **Seguridad (RLS):** Toda tabla nueva en Supabase debe incluir políticas de seguridad de Row Level Security (RLS) basadas en `pyme_id`.
- **Prefijo Automático:** Todas las tablas de datos de usuario en Supabase deben llevar el prefijo `usr_`.

## 3. Calidad del Código

- **Documentación:** Cada script principal debe tener una breve descripción de su propósito.
- **Entorno Virtual:** Siempre utilizar el entorno virtual `.venv` para la ejecución y gestión de dependencias.
