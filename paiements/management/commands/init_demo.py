from django.core.management.base import BaseCommand

from paiements.models import Client, Compte, Utilisateur


class Command(BaseCommand):
    help = "Crée un administrateur et un client de démonstration (si absents)."

    def handle(self, *args, **options):
        if not Utilisateur.objects.filter(username="admin").exists():
            Utilisateur.objects.create_superuser("admin", "admin@spl.fr", "Admin123!", role="admin")
            self.stdout.write("Administrateur créé : admin / Admin123!")

        if not Utilisateur.objects.filter(username="marie").exists():
            client = Client.objects.create_user(
                "marie", "marie.dupont@mail.fr", "Client123!",
                first_name="Marie", last_name="Dupont", role="client",
            )
            client.ajouter_compte(Compte(numero="FR001", solde=500))
            client.ajouter_compte(Compte(numero="FR002", solde=1000))
            self.stdout.write("Client créé : marie / Client123! (comptes FR001 et FR002)")

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
