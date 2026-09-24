# Reglas del Proyecto Mi Marketplace

Reglas que cualquier asistente de IA (o colaborador) debe respetar.

## Idioma y comunicacion
- Castellano neutro con el usuario (sin voseo, sin regionalismos)
- Codigo en ingles (nombres de funciones, variables, clases)
- Textos visibles al usuario en espanol

## Stack innegociable
- Django 6.1
- Python 3.13 (Render), 3.14 (local)
- PostgreSQL en produccion, SQLite en local
- Cloudinary para imagenes (nunca MEDIA_ROOT)
- Render para deploy
- Sentry para monitoreo

## Convenciones de codigo
- Espanol para textos visibles al usuario
- Ingles para nombres de codigo
- Migraciones: nunca modificar migraciones ya aplicadas
- Si hay que mover modelos: usar SeparateDatabaseAndState
- Los STATUS_CHOICES no se cambian sin migracion
- Para datos que deben existir en produccion: usar migraciones de datos
  (RunPython, ejemplo en apps/products/migrations/0004_seed_categories_data.py)

## Estructura obligatoria
- Cada app: models.py, views.py, forms.py, urls.py, admin.py
- Vistas del dashboard: views_*.py
- Mixins: apps/stores/mixins.py
- Servicios en services.py (no en vistas)
- Senales en signals.py (cargadas desde apps.py::ready())
- CSS de templates: en static/css/<nombre>.css (no inline)
- JS de templates: en static/js/<nombre>.js (no inline)
- Si el JS necesita datos del servidor: usar json_script

## Reglas de seguridad
- NUNCA hardcodear credenciales
- SIEMPRE variables de entorno
- El .env NO se sube a git
- Modelos con User FK: usar settings.AUTH_USER_MODEL
- Campos bancarios requieren doble autorizacion
- Validar imagenes: tipo + tamano (max 5MB)
- El validador de imagenes debe usar isinstance(UploadedFile)
  para no romper en ediciones (archivo existente de Cloudinary
  no tiene extension)

## Comportamiento del asistente
- Preguntar antes de cambios grandes (>30 min)
- Verificar con python manage.py check despues de cada cambio
- Probar en local antes de decir "listo"
- NO usar except Exception: pass
- NO romper el CSS: verificar estructura HTML
- Si el cambio afecta produccion, avisar antes del push
- Usar scripts de Python para modificar archivos (no editar a mano)
- Backup antes de cambios masivos: Copy-Item archivo archivo.bak-FECHA
- Antes de escribir scripts grandes, chequear el tamano de la terminal
  (here-strings muy grandes pueden colgar la terminal)

## Cosas que NO hacer
- Enviar emails de forma sincrona (usar run_async)
- Envolver todo en try/except generico
- Tocar migraciones aplicadas sin SeparateDatabaseAndState
- Borrar usuarios con pedidos (tienen PROTECT)
- Cambiar settings.py sin verificar check
- Meter {% load %} antes de <!DOCTYPE html>
- Concatenar bloques CSS de multiples <style> sin verificar
  (puede romper visual)

## Cuando algo falla
1. Buscar en Sentry
2. Reproducir en local primero
3. Preguntar si no esta claro
4. No inventar soluciones que puedan romper mas
5. Rollback con el backup si algo se rompe

## Deploy
    python manage.py check
    git add .
    git commit -m "tipo(area): descripcion corta"
    git push origin main

Tipos: feat, fix, refactor, chore, docs, perf, security, style

## Como arrancar una sesion nueva
1. Leer agents.md (este archivo)
2. Leer README.md
3. Leer docs/ROADMAP.md
4. Leer docs/SESSION_LOG.md (ultimas sesiones)
5. Verificar: python manage.py check
6. Preguntar al usuario que quiere hacer

## Plantilla de inicio de sesion

    Hola. Seguimos con Mi Marketplace (Django, Render, PostgreSQL).
    Estabamos con [PENDIENTE]. El ultimo cambio fue [X].
    Pega un diagnostico antes de tocar nada.

## Enlaces
- Produccion: https://marketpla.onrender.com
- Repo: github.com/ItachiBoruto/marketplace
- Sentry: https://marketplace-am.sentry.io
