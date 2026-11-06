from decimal import Decimal

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models, transaction


# ==========================================================
#  UTILISATEUR : classe mère (connexion gérée par Django)
#  - se_connecter / se_deconnecter -> pages de connexion (views.py)
#  - le mot de passe est haché automatiquement par Django
# ==========================================================
class Utilisateur(AbstractUser):
    ROLES = [("client", "Client"), ("admin", "Administrateur")]
    role = models.CharField(max_length=10, choices=ROLES, default="client")

    def est_administrateur(self) -> bool:
        return self.role == "admin" or self.is_superuser

    # Noms de variables du TP
    @property
    def nom(self) -> str:
        return self.last_name

    @property
    def prenom(self) -> str:
        return self.first_name


# ==========================================================
#  COMPTE : compte bancaire appartenant à un Client
# ==========================================================
class Compte(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    solde = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    proprietaire = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="comptes",
        limit_choices_to={"role": "client"},
    )

    def deposer(self, montant) -> None:
        montant = Decimal(str(montant))
        if montant <= 0:
            raise ValueError("Le montant du dépôt doit être positif.")
        self.solde += montant
        self.save()

    def retirer(self, montant) -> None:
        montant = Decimal(str(montant))
        if montant <= 0:
            raise ValueError("Le montant du retrait doit être positif.")
        if montant > self.solde:
            raise ValueError("Solde insuffisant.")
        self.solde -= montant
        self.save()

    def get_numero(self) -> str:
        return self.numero

    def get_solde(self) -> Decimal:
        return self.solde

    @staticmethod
    def generer_numero() -> str:
        """Numéro unique du type FR003, FR004..."""
        n = Compte.objects.count() + 1
        while Compte.objects.filter(numero=f"FR{n:03d}").exists():
            n += 1
        return f"FR{n:03d}"

    # ----- Paiements -----
    @transaction.atomic
    def payer(self, montant, service: str) -> "Paiement":
        self.retirer(montant)  # vérifie montant > 0 et solde suffisant
        return Paiement.objects.create(compte=self, montant=Decimal(str(montant)), service=service)

    @transaction.atomic
    def supprimer_paiement(self, numero: int) -> None:
        try:
            paiement = self.paiements.get(pk=numero)
        except Paiement.DoesNotExist:
            raise ValueError(f"Paiement n°{numero} introuvable sur le compte {self.numero}.")
        self.deposer(paiement.montant)  # le client est remboursé
        paiement.delete()

    def __str__(self):
        return f"Compte {self.numero} : solde = {self.solde:.2f} €"


# ==========================================================
#  PAIEMENT : remplace le dictionnaire de la version Python
#  (une ligne de la table = un paiement enregistré dans SQLite)
# ==========================================================
class Paiement(models.Model):
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name="paiements")
    service = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    @property
    def numero(self) -> int:
        return self.pk

    def __str__(self):
        return f"Paiement n°{self.pk} - {self.service} - {self.montant} €"


# ==========================================================
#  CLIENT et ADMINISTRATEUR : héritent d'Utilisateur
#  (modèles « proxy » : même table, méthodes différentes)
# ==========================================================
class ClientManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role="client")


class Client(Utilisateur):
    objects = ClientManager()

    class Meta:
        proxy = True

    def ajouter_compte(self, compte: Compte) -> None:
        compte.proprietaire = self
        compte.save()

    def get_comptes(self):
        return self.comptes.all()

    def ouvrir_compte(self, solde_initial=0) -> Compte:
        solde_initial = Decimal(str(solde_initial))
        if solde_initial < 0:
            raise ValueError("Le dépôt initial ne peut pas être négatif.")
        compte = Compte(numero=Compte.generer_numero(), solde=solde_initial)
        self.ajouter_compte(compte)
        return compte

    def effectuer_paiement(self, compte: Compte, montant, service: str) -> Paiement:
        if compte.proprietaire_id != self.pk:
            raise ValueError("Ce compte n'appartient pas à ce client.")
        return compte.payer(montant, service)

    def editer_ticket(self, paiement: Paiement) -> bytes:
        if paiement.compte.proprietaire_id != self.pk:
            raise ValueError("Ce paiement n'appartient pas à ce client.")
        from .ticket import generer_ticket_pdf
        return generer_ticket_pdf(paiement)


class AdministrateurManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(models.Q(role="admin") | models.Q(is_superuser=True))


class Administrateur(Utilisateur):
    objects = AdministrateurManager()

    class Meta:
        proxy = True

    def consulter_paiements(self):
        return Paiement.objects.select_related("compte", "compte__proprietaire")

    def supprimer_paiement(self, paiement: Paiement) -> None:
        paiement.compte.supprimer_paiement(paiement.pk)
