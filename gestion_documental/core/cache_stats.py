"""Caché de estadísticas (dashboards y conteos).

Estrategia: claves versionadas (`...:v<N>`). Cualquier escritura que altere
conteos llama a `bump_stats()` y las lecturas siguientes fallan caché de forma
automática. Sin borrados por patrón (LocMem no los soporta) y sin datos
obsoletos más allá del TTL de seguridad.
"""
from django.core.cache import cache

_CLAVE_VERSION = "sigea:stats:v1"
_TTL_VERSION = 86400


def version_stats():
    """Versión actual del ciclo de estadísticas."""
    try:
        return int(cache.get(_CLAVE_VERSION) or 0)
    except (TypeError, ValueError):
        return 0


def bump_stats():
    """Invalida todas las estadísticas cacheadas (llamar tras cada escritura)."""
    try:
        return cache.incr(_CLAVE_VERSION)
    except ValueError:
        cache.set(_CLAVE_VERSION, 1, timeout=_TTL_VERSION)
        return 1


def conteo_cacheado(clave, consulta, timeout=120):
    """Devuelve el dict de conteo cacheado bajo `clave:v<versión>`."""
    clave_versionada = f"{clave}:v{version_stats()}"
    valor = cache.get(clave_versionada)
    if valor is None:
        valor = consulta()
        cache.set(clave_versionada, valor, timeout=timeout)
    return valor
