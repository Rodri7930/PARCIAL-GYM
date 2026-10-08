import unittest

from src.domain.models import Socio, PlanMembresia
from src.domain.exceptions import (
    DomainError,
    ValidationError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidMembershipError,
)


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

    def test_rechazar_correos_invalidos(self):
        correos_invalidos = [
            "juan..perez@gmail.com",
            "juan@gmail..com",
            "juan perez@gmail.com",
        ]

        for correo in correos_invalidos:
            with self.subTest(correo=correo):
                with self.assertRaises(ValidationError):
                    Socio(
                        "S001", "Juan", "Perez",
                        "12345678", "987654321", correo
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


class TestDomainExceptions(unittest.TestCase):

    def test_validation_error_hereda_de_domain_error(self):
        self.assertTrue(issubclass(ValidationError, DomainError))

    def test_duplicate_entity_error_hereda_de_domain_error(self):
        self.assertTrue(issubclass(DuplicateEntityError, DomainError))

    def test_entity_not_found_error_hereda_de_domain_error(self):
        self.assertTrue(issubclass(EntityNotFoundError, DomainError))

    def test_invalid_membership_error_hereda_de_domain_error(self):
        self.assertTrue(issubclass(InvalidMembershipError, DomainError))

    def test_validation_error_puede_lanzarse(self):
        with self.assertRaises(ValidationError):
            raise ValidationError("Datos inválidos")
    
    def test_duplicate_entity_error_conserva_mensaje(self):
        error = DuplicateEntityError("El socio ya existe")
        self.assertEqual(str(error), "El socio ya existe")

    def test_entity_not_found_error_conserva_mensaje(self):
        error = EntityNotFoundError("Socio no encontrado")
        self.assertEqual(str(error), "Socio no encontrado")

    def test_invalid_membership_error_conserva_mensaje(self):
        error = InvalidMembershipError("Membresía inválida")
        self.assertEqual(str(error), "Membresía inválida")


if __name__ == "__main__":
    unittest.main() 