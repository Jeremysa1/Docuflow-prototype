"""Mixins del admin: UX simplificada para personal no técnico.

- Oculta "Grabar y continuar editando" (el tag `submit_row` de Django lee
  `show_save_and_continue` del contexto y por defecto es True).
- Desactiva la ordenación por columnas (`sortable_by = ()`, hook documentado
  de `ModelAdmin.get_sortable_by`): sin flechas ni × en las cabeceras.
Se conservan: Grabar, Grabar y añadir otro, y Eliminar.
"""

_SIMPLE_SUBMIT_CONTEXT = {
    "show_save_and_continue": False,
}


class AdminSimpleSubmitMixin:
    sortable_by = ()

    def _contexto_simple(self, extra_context):
        contexto = dict(extra_context or {})
        contexto.update(_SIMPLE_SUBMIT_CONTEXT)
        return contexto

    def add_view(self, request, form_url="", extra_context=None):
        return super().add_view(
            request, form_url, extra_context=self._contexto_simple(extra_context)
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return super().change_view(
            request, object_id, form_url, extra_context=self._contexto_simple(extra_context)
        )
