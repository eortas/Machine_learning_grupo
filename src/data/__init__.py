"""Módulo de gestión de datos"""
from .data_manager import (
    cargar_registro,
    actualizar_registro,
    guardar_evaluacion,
    generar_hall_of_fame
)

__all__ = [
    'cargar_registro',
    'actualizar_registro',
    'guardar_evaluacion',
    'generar_hall_of_fame',
]
