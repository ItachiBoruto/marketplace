"""Panel global de pedidos para el superuser."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from apps.notifications.models import notify
from apps.stores.models import Store

from .models import Order, OrderItem
from .services import release_order_stock


def _superuser_only(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Http404("Solo el administrador puede acceder a esta sección.")


class SuperuserOrderListView(ListView):
    """Lista global de pedidos. Solo superuser."""
    template_name = "superadmin/orders.html"
    context_object_name = "orders"
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        _superuser_only(request)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Order.objects.select_related("user").prefetch_related("items__store")

        status_filter = self.request.GET.get("status", "all")
        if status_filter == "shipped_completed":
            qs = qs.filter(status__in=["shipped", "completed"])
        elif status_filter != "all":
            qs = qs.filter(status=status_filter)

        store_id = self.request.GET.get("store")
        if store_id:
            qs = qs.filter(items__store_id=store_id).distinct()

        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(
                Q(reference_code__icontains=search) |
                Q(user__username__icontains=search) |
                Q(payment_reference__icontains=search)
            )

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "all")
        context["current_store"] = self.request.GET.get("store", "")
        context["search"] = self.request.GET.get("q", "")

        base = Order.objects.all()
        context["count_all"] = base.count()
        context["count_payment_submitted"] = base.filter(status="payment_submitted").count()
        context["count_confirmed"] = base.filter(status="confirmed").count()
        context["count_shipped_completed"] = base.filter(status__in=["shipped", "completed"]).count()
        context["count_cancelled"] = base.filter(status="cancelled").count()

        context["stores"] = Store.objects.filter(is_active=True).order_by("name")

        # Resumen del día
        today = timezone.now().date()
        start_of_day = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        sales_today = base.filter(created_at__gte=start_of_day).aggregate(
            total=Sum("total"), count=Count("id")
        )
        context["sales_today_total"] = sales_today["total"] or 0
        context["sales_today_count"] = sales_today["count"] or 0

        return context


class SuperuserOrderDetailView(DetailView):
    """Detalle completo del pedido. Solo superuser."""
    template_name = "superadmin/order_detail.html"
    context_object_name = "order"
    pk_url_kwarg = "order_id"

    def dispatch(self, request, *args, **kwargs):
        _superuser_only(request)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Order.objects.select_related("user").prefetch_related("items__store", "items__product")


@login_required(login_url="login")
def superuser_confirm_payment(request, order_id):
    if not request.user.is_superuser:
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    order = get_object_or_404(Order, id=order_id)

    if order.status != "payment_submitted":
        messages.warning(request, "Este pedido ya fue procesado.")
        return redirect("orders:superuser_order_detail", order_id=order.pk)

    order.status = "confirmed"
    order.save(update_fields=["status"])

    notify(
        order.user,
        "payment_confirmed",
        f"Pago confirmado - Pedido {order.reference_code}",
        "Verificamos tu pago. Los comercios están preparando tu pedido.",
        link=f"/orders/{order.pk}/"
    )

    messages.success(request, f"Pago del pedido {order.reference_code} confirmado.")
    return redirect("orders:superuser_order_detail", order_id=order.pk)


@login_required(login_url="login")
def superuser_cancel_order(request, order_id):
    if not request.user.is_superuser:
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    order = get_object_or_404(Order, id=order_id)

    if order.status in ("cancelled", "completed"):
        messages.warning(request, "Este pedido ya fue procesado.")
        return redirect("orders:superuser_order_detail", order_id=order.pk)

    release_order_stock(order, reason="Cancelado por admin")
    order.status = "cancelled"
    order.save(update_fields=["status"])

    notify(
        order.user,
        "order_rejected",
        f"Pedido cancelado {order.reference_code}",
        "Tu pedido fue cancelado. Contacta con soporte si tienes dudas.",
        link=f"/orders/{order.pk}/"
    )

    messages.success(request, f"Pedido {order.reference_code} cancelado. Stock devuelto.")
    return redirect("orders:superuser_order_detail", order_id=order.pk)


@login_required(login_url="login")
def superuser_mark_delivered(request, order_id):
    """Marca un pedido completo como entregado. Solo superuser."""
    if not request.user.is_superuser:
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    order = get_object_or_404(Order, id=order_id)

    if order.status not in ("confirmed", "shipped"):
        messages.warning(request, "Este pedido no puede marcarse como entregado.")
        return redirect("orders:superuser_order_detail", order_id=order.pk)

    # Marcar todos los items como entregados
    order.items.update(status="delivered")
    order.status = "completed"
    order.save(update_fields=["status"])

    notify(
        order.user,
        "order_completed",
        f"Pedido entregado {order.reference_code}",
        "Tu pedido ha sido marcado como entregado. Gracias por tu compra.",
        link=f"/orders/{order.pk}/"
    )

    messages.success(request, f"Pedido {order.reference_code} marcado como entregado.")
    return redirect("orders:superuser_order_detail", order_id=order.pk)


@login_required(login_url="login")
def superuser_revert_delivery(request, order_id):
    """Revierte un pedido entregado a su estado anterior. Solo superuser."""
    if not request.user.is_superuser:
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    order = get_object_or_404(Order, id=order_id)

    if order.status != "completed":
        messages.warning(request, "Solo se pueden revertir pedidos completados.")
        return redirect("orders:superuser_order_detail", order_id=order.pk)

    # Determinar el estado anterior segun el metodo de envio
    if order.shipping_method == "pickup":
        new_order_status = "confirmed"
        new_item_status = "confirmed"
    else:
        new_order_status = "shipped"
        new_item_status = "shipped"

    # Revertir todos los items
    order.items.update(status=new_item_status)
    order.status = new_order_status
    order.save(update_fields=["status"])

    notify(
        order.user,
        "system",
        f"Pedido actualizado {order.reference_code}",
        "El estado de tu pedido fue actualizado.",
        link=f"/orders/{order.pk}/"
    )

    messages.success(
        request,
        f"Pedido {order.reference_code} revertido a estado '{order.get_status_display()}'."
    )
    return redirect("orders:superuser_order_detail", order_id=order.pk)


class SalesHistoryView(ListView):
    """Historial de ventas agrupado por dia. Superuser ve todo, owner ve su comercio."""
    template_name = "superadmin/sales_history.html"
    context_object_name = "orders"
    paginate_by = 100

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_superuser:
            raise Http404("Solo el administrador puede acceder a esta sección.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Order.objects.filter(
            status__in=["confirmed", "shipped", "completed"]
        ).select_related("user").prefetch_related("items__store")

        # Filtro por fecha
        period = self.request.GET.get("period", "today")
        today = timezone.now().date()

        if period == "today":
            start_date = today
            end_date = today
        elif period == "yesterday":
            start_date = today - timedelta(days=1)
            end_date = start_date
        elif period == "last_7":
            start_date = today - timedelta(days=6)
            end_date = today
        elif period == "this_month":
            start_date = today.replace(day=1)
            end_date = today
        elif period == "custom":
            try:
                from datetime import date
                start_date = date.fromisoformat(self.request.GET.get("start", ""))
                end_date = date.fromisoformat(self.request.GET.get("end", ""))
            except (ValueError, TypeError):
                start_date = today
                end_date = today
        else:
            start_date = today
            end_date = today

        # Convertir a datetime aware
        from datetime import datetime
        start_dt = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_dt = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time())
        )

        qs = qs.filter(created_at__gte=start_dt, created_at__lte=end_dt)

        # Filtro por comercio (opcional)
        store_id = self.request.GET.get("store")
        if store_id:
            qs = qs.filter(items__store_id=store_id).distinct()

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_period"] = self.request.GET.get("period", "today")
        context["current_store"] = self.request.GET.get("store", "")
        context["start_date"] = self.request.GET.get("start", "")
        context["end_date"] = self.request.GET.get("end", "")
        context["stores"] = Store.objects.filter(is_active=True).order_by("name")

        # Agrupar por dia
        from collections import OrderedDict
        from decimal import Decimal

        groups = OrderedDict()
        for order in self.object_list:
            day = order.created_at.date()
            if day not in groups:
                groups[day] = {
                    "date": day,
                    "orders": [],
                    "total_usd": Decimal("0"),
                    "count": 0,
                    "rates": [],
                }
            groups[day]["orders"].append(order)
            groups[day]["total_usd"] += order.grand_total or Decimal("0")
            groups[day]["count"] += 1
            if order.exchange_rate:
                groups[day]["rates"].append(float(order.exchange_rate))

        # Calcular tasa promedio del dia y total Bs
        for day_data in groups.values():
            if day_data["rates"]:
                avg = sum(day_data["rates"]) / len(day_data["rates"])
                day_data["avg_rate"] = avg
                day_data["total_bs"] = float(day_data["total_usd"]) * avg
            else:
                day_data["avg_rate"] = None
                day_data["total_bs"] = None

        context["day_groups"] = list(groups.values())

        # Total general
        grand_total_usd = sum(g["total_usd"] for g in groups.values())
        context["grand_total_usd"] = grand_total_usd
        context["grand_total_orders"] = sum(g["count"] for g in groups.values())

        return context
