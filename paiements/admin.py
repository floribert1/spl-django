from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Compte, Paiement, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rôle SPL", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Rôle SPL", {"fields": ("role",)}),)
    list_display = ("username", "email", "first_name", "last_name", "role")
    list_filter = ("role",)


@admin.register(Compte)
class CompteAdmin(admin.ModelAdmin):
    list_display = ("numero", "proprietaire", "solde")


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("id", "compte", "service", "montant", "date")
