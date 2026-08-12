from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    # Honeypot: campo invisible para humanos (oculto por CSS). Si un bot
    # lo rellena, la validación falla en silencio para el usuario real.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "hp-field",
            "tabindex": "-1",
            "autocomplete": "off",
        }),
    )

    class Meta:
        model = Feedback
        fields = ["name", "email", "message"]
        labels = {
            "name": "Nombre",
            "email": "Correo",
            "message": "Mensaje",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Tu nombre (opcional)"}),
            "email": forms.EmailInput(attrs={"placeholder": "Tu correo (opcional, solo si quieres respuesta)"}),
            "message": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Sugerencias, comentarios o errores que encontraste en el sitio...",
            }),
        }

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise forms.ValidationError("No se pudo enviar el mensaje.")
        return value
