# Scripts de QA manual (heredados)

Recorren flujos completos contra la base de **desarrollo** y la modifican, por eso no están en `tests/`
(`manage.py test` no debe importarlos). No sustituyen las pruebas automatizadas de `tests/`.

Ejecutar desde `gestion_documental/`:

```bash
./venv/Scripts/python.exe manage.py shell -c "exec(open('scripts/qa/qa_accesos.py', encoding='utf-8').read())"
```

Los resultados JSON de `qa_test_part*.py` se escriben en `salidas/`, que git ignora.
