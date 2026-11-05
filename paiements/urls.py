from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", auth_views.LoginView.as_view(template_name="paiements/connexion.html",
                                                    redirect_authenticated_user=True), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("client/", views.espace_client, name="espace_client"),
    path("client/ticket/<int:pk>/", views.ticket_pdf, name="ticket_pdf"),
    path("administration/paiements/", views.liste_paiements, name="liste_paiements"),
    path("administration/paiements/<int:pk>/supprimer/", views.supprimer_paiement, name="supprimer_paiement"),
]
