import unittest

from src.domain.models import Socio, PlanMembresia
from src.domain.exceptions import ValidationError


class TestSocio(unittest.TestCase):

    def test_crear_socio_valido(self):
        socio = Socio(
            "S001", "Juan", "Perez",
            "12345678", "987654321", "juan@gmail.com"
        )

        self.assertEqual(socio.nombre, "Juan")
        self.assertEqual(socio.dni, "12345678")

    def test_rechazar_nombre_vacio(self):
        with self.assertRaises(ValidationError):
            Socio(
                "S001", "", "Perez",
                "12345678", "987654321", "juan@gmail.com"
            )

    def test_rechazar_dni_invalido(self):
        with self.assertRaises(ValidationError):
            Socio(
                "S001", "Juan", "Perez",
                "123", "987654321", "juan@gmail.com"
            )


class TestPlanMembresia(unittest.TestCase):

    def test_crear_plan_valido(self):
        plan = PlanMembresia("P001", "Premium", "120.50", 30)

        self.assertEqual(plan.nombre, "Premium")
        self.assertEqual(plan.duracion_dias, 30)

    def test_rechazar_precio_negativo(self):
        with self.assertRaises(ValidationError):
            PlanMembresia("P001", "Premium", -50, 30)

    def test_rechazar_duracion_cero(self):
        with self.assertRaises(ValidationError):
            PlanMembresia("P001", "Premium", 120, 0)


if __name__ == "__main__":
    unittest.main()