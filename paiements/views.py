from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from io import BytesIO

from .forms import CompteForm, PaiementForm
from .models import Administrateur, Client, Paiement


def _client(request):
    return Client.objects.get(pk=request.user.pk)


def _admin(request):
    return Administrateur.objects.get(pk=request.user.pk)


@login_required
def accueil(request):
    """Après la connexion : chaque acteur arrive sur son espace."""
    if request.user.est_administrateur():
        return redirect("liste_paiements")
    return redirect("espace_client")


# ------------------------- CLIENT -------------------------
@login_required
def espace_client(request):
    if request.user.est_administrateur():
        return redirect("liste_paiements")
    client = _client(request)

    if request.method == "POST":
        form = PaiementForm(client, request.POST)
        if form.is_valid():
            try:
                paiement = client.effectuer_paiement(
                    form.cleaned_data["compte"], form.cleaned_data["montant"], form.cleaned_data["service"]
                )
                messages.success(request, f"Paiement n°{paiement.pk} effectué. Vous pouvez télécharger votre ticket.")
                return redirect("espace_client")
            except ValueError as erreur:
                messages.error(request, str(erreur))
    else:
        form = PaiementForm(client)

    paiements = Paiement.objects.filter(compte__proprietaire=client).select_related("compte")
    return render(request, "paiements/espace_client.html", {
        "client": client, "comptes": client.get_comptes(), "paiements": paiements, "form": form,
        "compte_form": CompteForm(),
    })


@login_required
@require_POST
def ajouter_compte(request):
    if request.user.est_administrateur():
        return HttpResponseForbidden("Réservé aux clients.")
    client = _client(request)
    form = CompteForm(request.POST)
    if form.is_valid():
        compte = client.ouvrir_compte(form.cleaned_data["solde_initial"])
        messages.success(request, f"Compte {compte.numero} ouvert avec un solde de {compte.solde:.2f} €.")
    else:
        messages.error(request, "Dépôt initial invalide : il doit être positif ou nul.")
    return redirect("espace_client")


@login_required
def ticket_pdf(request, pk):
    if request.user.est_administrateur():
        return HttpResponseForbidden("Réservé aux clients.")
    client = _client(request)
    paiement = get_object_or_404(Paiement, pk=pk, compte__proprietaire=client)
    contenu = client.editer_ticket(paiement)
    return FileResponse(BytesIO(contenu), as_attachment=True,
                        filename=f"ticket_paiement_{paiement.pk}.pdf", content_type="application/pdf")


# --------------------- ADMINISTRATEUR ---------------------
@login_required
def liste_paiements(request):
    if not request.user.est_administrateur():
        return HttpResponseForbidden("Réservé à l'administrateur.")
    paiements = _admin(request).consulter_paiements()
    total = sum(p.montant for p in paiements)
    return render(request, "paiements/liste_paiements.html", {"paiements": paiements, "total": total})


@login_required
@require_POST
def supprimer_paiement(request, pk):
    if not request.user.est_administrateur():
        return HttpResponseForbidden("Réservé à l'administrateur.")
    paiement = get_object_or_404(Paiement, pk=pk)
    _admin(request).supprimer_paiement(paiement)
    messages.success(request, f"Paiement n°{pk} supprimé, le compte {paiement.compte.numero} a été remboursé.")
    return redirect("liste_paiements")
