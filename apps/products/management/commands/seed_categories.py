# -*- coding: utf-8 -*-
"""
Crea las categorias base del marketplace.
Idempotente: si el slug ya existe, no lo duplica.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.products.models import Category


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


class Command(BaseCommand):
    help = "Crea las categorias base del marketplace (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra que se crearia sin guardar nada",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        created = 0
        skipped = 0

        for name, emoji, color, order in CATEGORIES:
            slug = slugify(name)
            exists = Category.objects.filter(slug=slug).exists()
            if exists:
                skipped += 1
                self.stdout.write(f"  [SKIP] {emoji} {name} ({slug})")
                continue

            if dry:
                self.stdout.write(f"  [DRY]  {emoji} {name} ({slug})")
                created += 1
                continue

            Category.objects.create(
                name=name,
                slug=slug,
                emoji=emoji,
                color=color,
                order=order,
                is_active=True,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  [OK]   {emoji} {name} ({slug})"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"[DONE] Creadas: {created} | Omitidas (ya existian): {skipped}"
        ))
        if dry:
            self.stdout.write(self.style.WARNING("[DRY RUN] No se guardo nada."))
