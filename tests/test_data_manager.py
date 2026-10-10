import pytest
from src.services.data_manager import DataManager


def test_save_and_load_data(tmp_path):
    manager = DataManager(data_folder=str(tmp_path))

    datos_prueba = [{"id": 1, "nombre": "Juan"}]
    manager.save_data("socios", datos_prueba)

    resultado = manager.load_data("socios")
    assert resultado == datos_prueba


def test_load_non_existent_file(tmp_path):
    manager = DataManager(data_folder=str(tmp_path))
    resultado = manager.load_data("archivo_que_no_existe")
    assert resultado == []

