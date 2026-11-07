"""
Formularios del módulo de documentos.
"""
from django import forms
from django.conf import settings

from .models import Documento


class _OpcionesVaciasEnEspanol:
    """La opción vacía de cada lista dice qué elegir, en español."""
    VACIAS = {
        'programa': 'Elige el programa',
        'categoria': 'Elige la categoría',
        'factor_cna': 'Elige el factor CNA',
    }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        # M7: un docente con programa asignado solo sube o edita evidencias de su programa
        programa = getattr(usuario, 'programa_academico', None)
        if usuario is not None and getattr(usuario, 'rol', None) == 'DOCENTE_PLANTA' and programa and 'programa' in self.fields:
            self.fields['programa'].queryset = self.fields['programa'].queryset.filter(pk=programa.pk)
            self.fields['programa'].initial = programa.pk
            self.fields['programa'].empty_label = None
        for nombre, texto in self.VACIAS.items():
            campo = self.fields.get(nombre)
            if campo is None:
                continue
            if hasattr(campo, 'empty_label'):
                campo.empty_label = texto
                continue
            opciones = list(getattr(campo, 'choices', []))
            if opciones and opciones[0][0] in ('', None):
                campo.choices = [('', texto)] + opciones[1:]


class DocumentoForm(_OpcionesVaciasEnEspanol, forms.ModelForm):
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
            # Extensión, tamaño y firma real del contenido (una sola regla en todo SIGEA)
            from core.utils.helpers import validar_archivo_subido
            validar_archivo_subido(archivo)
        return archivo

class DocumentoEditForm(_OpcionesVaciasEnEspanol, forms.ModelForm):
    """Formulario para editar metadatos de documentos existentes (sin archivo)."""
    visibilidad = forms.ChoiceField(
        choices=[
            ('PROGRAMA', 'Por programa'),
            ('INSTITUCIONAL', 'Institucional'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'visibilidad-radio'}),
        label='Visibilidad'
    )

    class Meta:
        model = Documento
        fields = [
            'titulo', 'descripcion', 'programa', 'categoria',
            'factor_cna', 'fecha_vigencia', 'visibilidad', 'es_sensible'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del documento'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción'}),
            'programa': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'factor_cna': forms.Select(attrs={'class': 'form-control'}),
            'fecha_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'es_sensible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
