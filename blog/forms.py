from django import forms

from .models import Feedback

FORM_TEXT = {
    "es": {
        "labels": {"name": "Nombre", "email": "Correo", "message": "Mensaje"},
        "name_placeholder": "Tu nombre (opcional)",
        "email_placeholder": "Tu correo (opcional, solo si quieres respuesta)",
        "message_placeholder": "Sugerencias, comentarios o errores que encontraste en el sitio...",
        "honeypot_error": "No se pudo enviar el mensaje.",
    },
    "en": {
        "labels": {"name": "Name", "email": "Email", "message": "Message"},
        "name_placeholder": "Your name (optional)",
        "email_placeholder": "Your email (optional, only if you want a reply)",
        "message_placeholder": "Suggestions, feedback, or errors you found on the site...",
        "honeypot_error": "The message could not be sent.",
    },
}


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

    def __init__(self, *args, lang="es", **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = lang if lang in FORM_TEXT else "es"
        text = FORM_TEXT[self._lang]
        for field_name, label in text["labels"].items():
            self.fields[field_name].label = label
        self.fields["name"].widget.attrs["placeholder"] = text["name_placeholder"]
        self.fields["email"].widget.attrs["placeholder"] = text["email_placeholder"]
        self.fields["message"].widget.attrs.update({"rows": 5, "placeholder": text["message_placeholder"]})

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise forms.ValidationError(FORM_TEXT[self._lang]["honeypot_error"])
        return value
