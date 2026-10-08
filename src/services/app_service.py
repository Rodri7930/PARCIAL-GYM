
from datetime import date, timedelta

from src.domain.models import Socio, PlanMembresia
from src.domain.exceptions import (
    ValidationError,
    DuplicateEntityError,
    EntityNotFoundError,
)


class AppService:
    """Coordina las operaciones del sistema de gimnasio."""

    DIAS_AVISO = 7

    def __init__(self):
        # Almacenamiento temporal mientras se integra DataManager.
        self._socios = {}
        self._planes = {}

    # =====================================
    # GESTIÓN DE SOCIOS
    # =====================================

    def registrar_socio(
        self, id_socio, nombre, apellido, dni, telefono, correo
    ):
        """Registra un socio evitando identificadores y DNI duplicados."""

        socio = Socio(
            id_socio, nombre, apellido, dni, telefono, correo
        )

        if socio.id_socio in self._socios:
            raise DuplicateEntityError(
                "Ya existe un socio con ese ID."
            )

        for existente in self._socios.values():
            if existente.dni == socio.dni:
                raise DuplicateEntityError(
                    "Ya existe un socio con ese DNI."
                )

        self._socios[socio.id_socio] = socio
        return socio

    def listar_socios(self):
        """Devuelve los socios registrados."""
        return list(self._socios.values())

    def buscar_socio(self, id_socio):
        """Busca un socio utilizando su identificador."""

        if id_socio not in self._socios:
            raise EntityNotFoundError(
                "El socio no se encuentra registrado."
            )

        return self._socios[id_socio]

    def buscar_socio_por_dni(self, dni):
        """Busca un socio registrado mediante su DNI."""

        for socio in self._socios.values():
            if socio.dni == dni:
                return socio

        raise EntityNotFoundError(
            "No existe un socio registrado con ese DNI."
        )

    # =====================================
    # GESTIÓN DE PLANES
    # =====================================

    def registrar_plan(
        self, id_plan, nombre, precio, duracion_dias
    ):
        """Registra un nuevo plan de membresía."""

        plan = PlanMembresia(
            id_plan, nombre, precio, duracion_dias
        )

        if plan.id_plan in self._planes:
            raise DuplicateEntityError(
                "Ya existe un plan con ese ID."
            )

        for existente in self._planes.values():
            if existente.nombre.casefold() == plan.nombre.casefold():
                raise DuplicateEntityError(
                    "Ya existe un plan con ese nombre."
                )

        self._planes[plan.id_plan] = plan
        return plan

    def listar_planes(self):
        """Devuelve los planes disponibles."""
        return list(self._planes.values())

    def buscar_plan(self, id_plan):
        """Busca un plan por identificador."""

        if id_plan not in self._planes:
            raise EntityNotFoundError(
                "El plan no se encuentra registrado."
            )

        return self._planes[id_plan]

    # =====================================
    # CONSULTAS DE VENCIMIENTO
    # =====================================

    def esta_proxima_a_vencer(
        self, fecha_vencimiento, fecha_actual
    ):
        """Comprueba si una fecha vence dentro de los próximos 7 días."""

        if type(fecha_vencimiento) is not date:
            raise ValidationError(
                "La fecha de vencimiento no es válida."
            )

        if type(fecha_actual) is not date:
            raise ValidationError(
                "La fecha actual no es válida."
            )

        limite = fecha_actual + timedelta(days=self.DIAS_AVISO)

        return fecha_actual <= fecha_vencimiento <= limite
