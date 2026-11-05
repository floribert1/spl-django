from io import BytesIO

from django.utils import timezone
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def generer_ticket_pdf(paiement) -> bytes:
    """Construit le ticket d'un paiement au format PDF et renvoie son contenu."""
    compte = paiement.compte
    client = compte.proprietaire
    largeur, hauteur = A5
    tampon = BytesIO()
    pdf = canvas.Canvas(tampon, pagesize=A5)
    pdf.setTitle(f"Ticket paiement {paiement.pk}")

    # Bandeau
    pdf.setFillColor(HexColor("#1F4E79"))
    pdf.rect(0, hauteur - 30 * mm, largeur, 30 * mm, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(15 * mm, hauteur - 17 * mm, "SPL - Ticket de paiement")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(15 * mm, hauteur - 24 * mm, "Système de Paiement en Ligne")

    # Lignes du ticket
    date_locale = timezone.localtime(paiement.date)
    lignes = [
        ("Paiement n°", str(paiement.pk)),
        ("Date", date_locale.strftime("%d/%m/%Y %H:%M")),
        ("Client", f"{client.first_name} {client.last_name}".strip() or client.username),
        ("Email", client.email or "-"),
        ("Compte", compte.numero),
        ("Service", paiement.service),
        ("Montant", f"{paiement.montant:.2f} EUR"),
        ("Solde actuel du compte", f"{compte.solde:.2f} EUR"),
    ]
    y = hauteur - 45 * mm
    for libelle, valeur in lignes:
        pdf.setFillColor(HexColor("#555555"))
        pdf.setFont("Helvetica", 11)
        pdf.drawString(15 * mm, y, libelle)
        pdf.setFillColor(HexColor("#000000"))
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawRightString(largeur - 15 * mm, y, valeur)
        pdf.setStrokeColor(HexColor("#DDDDDD"))
        pdf.line(15 * mm, y - 3 * mm, largeur - 15 * mm, y - 3 * mm)
        y -= 11 * mm

    pdf.setFillColor(HexColor("#777777"))
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawCentredString(largeur / 2, 15 * mm, "Merci pour votre paiement.")
    pdf.showPage()
    pdf.save()
    return tampon.getvalue()
