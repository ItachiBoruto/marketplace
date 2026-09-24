# Roadmap de Mi Marketplace

## Completado

### Infraestructura
- Deploy en Render con PostgreSQL
- Cloudinary para imagenes
- Sentry para monitoreo
- Crons externos (cron-job.org)

### Seguridad
- Argon2 para contrasenas
- django-axes (rate limiting login)
- CSRF, HTTPS, HSTS
- Redaccion de PII en logs
- Verificacion de email con token
- Doble autorizacion para cambios bancarios

### Features
- Registro y login (email o username)
- Recuperacion de contrasena
- Catalogo con busqueda
- Sistema de categorias (19 base)
  - Modelo Category con emoji, color, imagen
  - Modal con tarjetas horizontales
  - Filtro por categoria
  - Boton "Visitar pasillo" en perfil de comercio
- Carrito segmentado por comercio
- Orden por llegada (ultimo primero)
- Checkout con retiro/delivery
- Metodos de pago dinamicos por comercio:
  - Transferencia (datos protegidos)
  - Pago movil (banco receptor, telefono, cedula)
  - Toggles editables directo por el comercio
  - Datos criticos requieren doble autorizacion
- Reserva de stock con expiracion (30 min)
- Notificaciones in-app
- Horario por dia (delivery y retiro separados)
- Boton 24/7 + UI tipo alarma
- Panel superuser de pedidos
- Legal: Privacidad, Terminos, Cookies
- Favicon SVG + Open Graph

### Modularidad (jornada 2026-09-24)
- Header CSS consolidado en un bloque unico
- Header mobile optimizado (3 pills en fila)
- Perfil del comercio reorganizado en mobile
- Extraccion de CSS inline a externos:
  - checkout.css, cart.css, schedule.css
  - store_profile.css, product_detail.css
- Extraccion de JS inline a externos:
  - checkout.js, schedule.js, product_list.js
- .gitignore excluye backups
- Precios en dolares en verde

---

## Pendientes criticos (antes de invitar usuarios)

### 1. Dominio propio (~$10/ano)
- Comprar en Porkbun o Cloudflare Registrar
- Configurar DNS en Render
- Actualizar ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS

### 2. Emails funcionales
Render free bloquea SMTP. Opciones:
- A) Resend (gratis, requiere dominio, recomendado)
- B) Upgrade Render Starter ($7/mes, desbloquea SMTP)
- C) Seguir con notificaciones in-app solo

### 3. Datos reales de contacto
- BANK_INFO en .env y Render
- Email, telefono, RIF, cuenta real

### 4. Upgrade Render (antes del 12 oct)
- BD gratuita se borra a los 30 dias
- Web + DB aproximadamente $13/mes

---

## Mejoras importantes

### Deuda tecnica pendiente
- Eliminar !important del CSS (369 en checkout.css)
- Crear base.html comun (elimina duplicacion del header)
- Unificar modal de categorias (parcial + inline)
- Refactorizar ProductListAPI + StoreProductListAPI

### Visuales y UX
- Quitar redundancia en checkout:
  - "Registrar tu pago" + "Datos del pago" repiten info
  - "Como quieres pagar" debe aparecer una sola vez
  - Tarjetas con emojis arriba, formulario especifico despues
- Skeleton loaders mientras cargan productos
- Agrupar notificaciones por fecha
- Analiticas (Google Analytics o Plausible)
- Banner de cookies

### Backups
- django-dbbackup + Dropbox

---

## Nice-to-have
- Tests automatizados con pytest
- Alt text en imagenes
- Conectar Sentry con GitHub (auto-resolve)
- 2FA opcional
- Login con Google
- Exportar historial a PDF

---

## Futuro lejano
- Pasarela de pago (Stripe/MercadoPago/PayPal)
- Sistema de comisiones automaticas
- App movil (PWA primero)
- Multi-idioma
- Sistema de cupones
- Wishlist / favoritos
- Reviews de productos
- Chat comprador-vendedor
