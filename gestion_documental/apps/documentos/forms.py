"""
Formularios del módulo de documentos.
"""
from django import forms
from django.conf import settings

from .models import Documento


class DocumentoForm(forms.ModelForm):
    """Formulario para crear/editar documentos."""

    visibilidad = forms.ChoiceField(
        choices=[
            ('PROGRAMA', 'Por programa'),
            ('INSTITUCIONAL', 'Institucional'),
        ],
        initial='PROGRAMA',
        widget=forms.RadioSelect(attrs={'class': 'visibilidad-radio'}),
        label='Visibilidad'
    )

    class Meta:
        model = Documento
        fields = [
            'titulo', 'descripcion', 'archivo', 'programa', 'categoria',
            'factor_cna', 'fecha_vigencia', 'visibilidad', 'es_sensible'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del documento'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx,.xlsx,.pptx'}),
            'programa': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'factor_cna': forms.Select(attrs={'class': 'form-control'}),
            'fecha_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'es_sensible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_archivo(self):
        """Valida extensión y tamaño del archivo."""
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar extensión
            import os
            ext = os.path.splitext(archivo.name)[1].lower()
            if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
                raise forms.ValidationError(
                    f'Extensión no permitida. Extensiones válidas: {", ".join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}'
                )
            # Validar tamaño
            if archivo.size > settings.MAX_UPLOAD_SIZE:
                max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
                raise forms.ValidationError(f'El archivo excede el tamaño máximo de {max_mb}MB.')
        return archivo
