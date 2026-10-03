# Checklist antes de push a main

## Siempre (10 seg)
- [ ] `python manage.py check` pasa
- [ ] `python manage.py makemigrations --check --dry-run` dice "No changes detected"
- [ ] `git status` no muestra `.env` ni archivos `.bak-*`

## Si tocaste JavaScript (30 seg)
- [ ] Verificar sintaxis: `node --check static/js/archivo.js`
- [ ] O al menos abrir el navegador con F12 → Console y verificar que no haya errores rojos

## Si tocaste CSS
- [ ] Verificar en el navegador (Ctrl+Shift+R para hard reload)
- [ ] Verificar en móvil (responsive)

## Si tocaste templates
- [ ] La página renderiza sin errores de `{% %}` mal cerrado
- [ ] Los elementos se ven correctamente

## Si tocaste modelos
- [ ] `python manage.py makemigrations` corrido
- [ ] `python manage.py migrate` aplicado
- [ ] Verificar en admin de Django

## Smoke test (2 min)
- [ ] Home carga en el navegador (F12 → Console sin errores rojos)
- [ ] Detalle de producto carga + agregar al carrito funciona
- [ ] Checkout carga + botones de método de pago responden
- [ ] Login funciona

## Después del push
- [ ] Esperar el deploy (~2-3 min)
- [ ] Verificar en producción
- [ ] Revisar Sentry por si aparecen errores nuevos

---

## Lecciones aprendidas

- **Oct 3, 2026:** Un `var` huérfano rompió el JS del checkout en producción. Detectado con F12 → Console. Lección: **SIEMPRE verificar la consola antes de pushear cuando se toca JS.**
