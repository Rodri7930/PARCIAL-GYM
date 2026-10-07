class DomainError(Exception):
    """Excepción base para errores del dominio."""


class ValidationError(DomainError):
    """Error cuando los datos no cumplen las reglas de validación."""


class DuplicateEntityError(DomainError):
    """Error cuando se intenta registrar una entidad duplicada."""


class EntityNotFoundError(DomainError):
    """Error cuando no se encuentra una entidad."""


class InvalidMembershipError(DomainError):
    """Error cuando una membresía no cumple las reglas del dominio."""