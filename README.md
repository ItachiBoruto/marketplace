# Mi Marketplace

Marketplace multi-comercio para Venezuela.

## Stack
- Django 6.1, Python 3.13
- PostgreSQL (prod), SQLite (local)
- Render.com (deploy automatico desde GitHub)
- Cloudinary (imagenes)
- Sentry (monitoreo)

## Apps
- accounts: usuarios, verificacion email
- stores: comercios, horarios, pagos
- products: catalogo, categorias
- inventory: movimientos de stock
- cart: carrito segmentado
- orders: pedidos, checkout
- notifications: in-app
- audit: registro de acciones
- utils: helpers, validators

## Estructura static

css/
  style.css            -> globales
  checkout.css         -> checkout
  cart.css             -> carrito
  schedule.css         -> panel horarios
  store_profile.css    -> perfil comercio
  product_detail.css   -> ficha producto
js/
  cart-toast.js
  store_detail.js
  checkout.js
  schedule.js
  product_list.js
  category-modal.js
  notifications.js
  email-verify-banner.js

## Correr en local

    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_categories
    python manage.py runserver

## Deploy

    git add .
    git commit -m "tipo(area): descripcion"
    git push origin main

Render redeploya en ~2-3 min. Las migraciones corren solas.

## Variables de entorno (.env)

SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL,
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, SENTRY_DSN

## Comandos utiles

    python manage.py check                    # verificar antes de commit
    python manage.py seed_categories          # cargar categorias
    python manage.py seed_categories --dry-run
    python manage.py showmigrations           # ver migraciones

## Migraciones de datos

Para insertar datos que deben existir en produccion:
apps/products/migrations/0004_seed_categories_data.py

Regla: si vas a insertar datos que deben existir en TODAS las instancias,
usa migracion de datos (RunPython), no un comando manual.

## Flujo de pedidos

1. Cliente agrega productos al carrito
2. Carrito segmentado por comercio
3. Paga un comercio a la vez (?store=<id>)
4. Registra comprobante (transferencia o pago movil)
5. Admin verifica pago
6. Vendedor aprueba items
7. Vendedor marca enviado/entregado
8. Pedido completado

## Roles

- Superuser: control total
- Owner: dueno de un comercio
- Manager: gestiona productos y pedidos
- Viewer: solo lectura

## Enlaces

- Produccion: https://marketpla.onrender.com
- Admin: /admin/
- Panel superuser: /orders/panel/
- Dashboard comercio: /stores/dashboard/<id>/
