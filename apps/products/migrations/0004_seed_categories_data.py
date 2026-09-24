# -*- coding: utf-8 -*-
"""
Migracion de datos: inserta las 19 categorias base del marketplace.
Es idempotente (usa get_or_create), asi que se puede correr varias veces sin duplicar.
"""
from django.db import migrations
from django.utils.text import slugify


CATEGORIES = [
    # (nombre, emoji, color hex, orden)
    # === ALIMENTOS ===
    ("Frutas y verduras",       "\U0001F966", "#27ae60", 10),
    ("Panaderia y cereales",    "\U0001F35E", "#d4a373", 20),
    ("Lacteos y huevos",        "\U0001F95B", "#f4d35e", 30),
    ("Carnes y pescados",       "\U0001F969", "#c0392b", 40),
    ("Legumbres y frutos secos","\U0001F95C", "#a0522d", 50),
    ("Dulces y snacks",         "\U0001F36C", "#e91e63", 60),
    ("Bebidas",                 "\U0001F964", "#3498db", 70),
    ("Condimentos y especias",  "\U0001F9C2", "#e67e22", 80),
    ("Comida preparada",        "\U0001F371", "#16a085", 90),
    # === NO ALIMENTOS ===
    ("Ferreteria",              "\U0001F527", "#7f8c8d", 100),
    ("Papeleria y escolares",   "\u270F\uFE0F", "#2980b9", 110),
    ("Aseo personal",           "\U0001F9F4", "#9b59b6", 120),
    ("Limpieza del hogar",      "\U0001F9FC", "#1abc9c", 130),
    ("Ropa y calzado",          "\U0001F455", "#e84393", 140),
    ("Hogar y decoracion",      "\U0001F3E0", "#8e44ad", 150),
    ("Farmacia y salud",        "\U0001F48A", "#2ecc71", 160),
    ("Tecnologia",              "\U0001F4F1", "#34495e", 170),
    ("Mascotas",                "\U0001F43E", "#f39c12", 180),
    ("Regalos y variedades",    "\U0001F381", "#e74c3c", 190),
]


def crear_categorias(apps, schema_editor):
    """Crea las categorias base del marketplace (idempotente)."""
    Category = apps.get_model("products", "Category")
    for name, emoji, color, order in CATEGORIES:
        slug = slugify(name)
        Category.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "emoji": emoji,
                "color": color,
                "order": order,
                "is_active": True,
            },
        )


def borrar_categorias(apps, schema_editor):
    """Revierte: elimina las categorias base del marketplace."""
    Category = apps.get_model("products", "Category")
    slugs = [slugify(name) for name, _, _, _ in CATEGORIES]
    Category.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_category_model"),
    ]

    operations = [
        migrations.RunPython(crear_categorias, borrar_categorias),
    ]
