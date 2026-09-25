"""Vistas del dashboard de analytics para comercios."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q, F
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.orders.models import OrderItem
from apps.products.models import Product

from .mixins import ManagerRequiredMixin, RoleContextMixin


class AnalyticsView(RoleContextMixin, ManagerRequiredMixin, View):
    """Dashboard de analytics del comercio."""

    def get(self, request, *args, **kwargs):
        store = self.get_store()
        if not store:
            from django.http import Http404
            raise Http404()

        # ============================================================
        # Rango de fechas
        # - Por defecto: ultimos 30 dias
        # - Rango personalizado: con fecha_desde y fecha_hasta (GET)
        # ============================================================
        hoy = timezone.now()
        es_personalizado = False
        fecha_desde_str = request.GET.get('fecha_desde', '').strip()
        fecha_hasta_str = request.GET.get('fecha_hasta', '').strip()

        fecha_desde = None
        fecha_hasta = None

        if fecha_desde_str and fecha_hasta_str:
            try:
                from datetime import datetime as dt
                fecha_desde = dt.strptime(fecha_desde_str, '%Y-%m-%d')
                fecha_hasta = dt.strptime(fecha_hasta_str, '%Y-%m-%d')
                # Hacer aware si la zona horaria esta activa
                fecha_desde = timezone.make_aware(fecha_desde)
                # Incluir todo el dia hasta (23:59:59)
                fecha_hasta = timezone.make_aware(fecha_hasta) + timedelta(days=1)
                es_personalizado = True
                rango_dias = (fecha_hasta - fecha_desde).days
            except (ValueError, TypeError):
                es_personalizado = False

        if not es_personalizado:
            rango = request.GET.get('rango', '30')
            try:
                rango_dias = int(rango)
            except ValueError:
                rango_dias = 30
            fecha_desde = hoy - timedelta(days=rango_dias)
            fecha_hasta = hoy

        desde = fecha_desde
        desde_anterior = desde - (fecha_hasta - fecha_desde)

        # Base: items vendidos del comercio (status delivered o shipped)
        items_vendidos = OrderItem.objects.filter(
            store=store,
            status__in=['shipped', 'delivered'],
        )

        # ============================================================
        # Metricas del periodo actual
        # ============================================================
        periodo_actual = items_vendidos.filter(
            order__created_at__gte=desde,
            order__created_at__lt=fecha_hasta,
        )
        periodo_anterior = items_vendidos.filter(
            order__created_at__gte=desde_anterior,
            order__created_at__lt=desde,
        )

        def calcular_metricas(qs):
            agg = qs.aggregate(
                total=Sum(F('product_price') * F('quantity'), default=0),
                unidades=Sum('quantity', default=0),
                ordenes=Count('order', distinct=True),
                items=Count('id'),
            )
            total = agg['total'] or 0
            ordenes = agg['ordenes'] or 0
            ticket = (total / ordenes) if ordenes > 0 else 0
            return {
                'total': total,
                'unidades': agg['unidades'] or 0,
                'ordenes': ordenes,
                'items': agg['items'] or 0,
                'ticket': ticket,
            }

        metricas_actual = calcular_metricas(periodo_actual)
        metricas_anterior = calcular_metricas(periodo_anterior)

        # % de cambio
        def cambio_pct(actual, anterior):
            if anterior == 0:
                return None if actual == 0 else 100
            return round(((actual - anterior) / anterior) * 100, 1)

        cambio_ventas = cambio_pct(metricas_actual['total'], metricas_anterior['total'])
        cambio_ordenes = cambio_pct(metricas_actual['ordenes'], metricas_anterior['ordenes'])
        cambio_unidades = cambio_pct(metricas_actual['unidades'], metricas_anterior['unidades'])

        # ============================================================
        # Top 5 productos
        # ============================================================
        top_productos = (
            periodo_actual
            .values('product_name')
            .annotate(
                unidades=Sum('quantity'),
                ingresos=Sum(F('product_price') * F('quantity')),
            )
            .order_by('-unidades')[:5]
        )

        # ============================================================
        # Ventas por dia (para el grafico)
        # ============================================================
        # Agrupamos por fecha del pedido
        from django.db.models.functions import TruncDate
        por_dia = (
            periodo_actual
            .annotate(dia=TruncDate('order__created_at'))
            .values('dia')
            .annotate(
                total=Sum(F('product_price') * F('quantity')),
                ordenes=Count('order', distinct=True),
            )
            .order_by('dia')
        )

        # Rellenar dias sin ventas
        ventas_por_dia = []
        datos_dict = {item['dia']: item for item in por_dia if item['dia']}
        cursor = fecha_desde.date()
        fecha_fin = fecha_hasta.date()
        while cursor <= fecha_fin:
            item = datos_dict.get(cursor)
            ventas_por_dia.append({
                'fecha': cursor,
                'total': float(item['total']) if item else 0,
                'ordenes': item['ordenes'] if item else 0,
            })
            cursor += timedelta(days=1)

        # Maximo para escalar el grafico
        max_venta = max((v['total'] for v in ventas_por_dia), default=0) or 1

        # ============================================================
        # Estado de pedidos pendientes
        # ============================================================
        pendientes = OrderItem.objects.filter(
            store=store,
            status='pending',
        ).count()

        por_enviar = OrderItem.objects.filter(
            store=store,
            status='confirmed',
        ).count()

        en_camino = OrderItem.objects.filter(
            store=store,
            status='shipped',
        ).count()

        entregados_periodo = periodo_actual.filter(status='delivered').count()

        # ============================================================
        # Productos con bajo stock
        # ============================================================
        bajo_stock = Product.objects.filter(
            store=store,
            is_available=True,
            stock__lte=5,
        ).order_by('stock')[:10]

        # ============================================================
        # Contexto
        # ============================================================
        context = {
            'store': store,
            'rango': str(rango_dias),
            'rango_dias': rango_dias,
            'es_personalizado': es_personalizado,
            'fecha_desde': fecha_desde_str if es_personalizado else '',
            'fecha_hasta': fecha_hasta_str if es_personalizado else '',
            'hoy': hoy,
            'metricas': metricas_actual,
            'metricas_anterior': metricas_anterior,
            'cambio_ventas': cambio_ventas,
            'cambio_ordenes': cambio_ordenes,
            'cambio_unidades': cambio_unidades,
            'top_productos': top_productos,
            'ventas_por_dia': ventas_por_dia,
            'max_venta': max_venta,
            'pendientes': pendientes,
            'por_enviar': por_enviar,
            'en_camino': en_camino,
            'entregados_periodo': entregados_periodo,
            'bajo_stock': bajo_stock,
        }
        return render(request, 'stores/dashboard/analytics.html', context)
