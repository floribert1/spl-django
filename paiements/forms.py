from decimal import Decimal

from django import forms

from .models import Compte


class PaiementForm(forms.Form):
    compte = forms.ModelChoiceField(queryset=Compte.objects.none(), label="Compte à débiter")
    service = forms.CharField(max_length=100, label="Service")
    montant = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"), label="Montant (€)")

    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["compte"].queryset = client.get_comptes()
        for champ in self.fields.values():
            champ.widget.attrs["class"] = "form-select" if isinstance(champ, forms.ModelChoiceField) else "form-control"
