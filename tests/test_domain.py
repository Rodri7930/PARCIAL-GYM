import unittest

from src.domain.exceptions import (
    DomainError,
    ValidationError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidMembershipError,
)


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


if __name__ == "__main__":
    unittest.main()