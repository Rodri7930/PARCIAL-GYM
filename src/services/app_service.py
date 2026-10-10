from datetime import date, datetime, timedelta

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
        self._membresias = []
        self._entrenadores = []
        self._asistencias = []

    def fecha_actual(self):
        return date.today()

    def resumen(self):
        membresias = self.listar_membresias()

        return {
            "socios": len(self._socios),
            "vigentes": sum(
                1
                for membresia in membresias
                if membresia["estado"] == "VIGENTE"
            ),
            "asistencias_hoy": sum(
                1
                for asistencia in self._asistencias
                if asistencia["fecha_hora"].date() == date.today()
            ),
            "proximas": sum(
                1
                for membresia in membresias
                if membresia["proxima"]
            ),
            "planes": len(self._planes),
            "entrenadores": len(self._entrenadores),
        }

    # =====================================
    # GESTIÓN DE SOCIOS
    # =====================================

    def registrar_socio(
        self, nombre, apellido, documento, telefono="", correo=""
    ):
        """Registra un socio evitando identificadores y DNI duplicados."""

        id_socio = str(len(self._socios) + 1)
        dni = documento

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

        return [
            {
                "id": socio.id_socio,
                "nombre": socio.nombre,
                "apellido": socio.apellido,
                "documento": socio.dni,
                "telefono": socio.telefono,
                "correo": socio.correo,
            }
            for socio in self._socios.values()
        ]

    def buscar_socio(self, id_socio):
        """Busca un socio utilizando su identificador."""

        id_socio = str(id_socio)

        if id_socio not in self._socios:
            raise EntityNotFoundError(
                "El socio no se encuentra registrado."
            )

        return self._socios[id_socio]

    # =====================================
    # GESTIÓN DE PLANES
    # =====================================

    def registrar_plan(
        self, nombre, precio, duracion_dias
):
        """Registra un nuevo plan de membresía."""

        id_plan = str(len(self._planes) + 1)
        duracion_dias = int(duracion_dias)

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

        return [
            {
                "id": plan.id_plan,
                "nombre": plan.nombre,
                "precio": plan.precio,
                "duracion_dias": plan.duracion_dias,
            }
            for plan in self._planes.values()
        ]

    def buscar_plan(self, id_plan):
        """Busca un plan por identificador."""

        id_plan = str(id_plan)

        if id_plan not in self._planes:
            raise EntityNotFoundError(
                "El plan no se encuentra registrado."
            )

        return self._planes[id_plan]

    # =====================================
    # GESTIÓN DE MEMBRESÍAS
    # =====================================

    def registrar_membresia(
        self, socio_id, plan_id, fecha_inicio
    ):
        socio = self.buscar_socio(socio_id)
        plan = self.buscar_plan(plan_id)

        fecha_inicio = self._convertir_fecha(fecha_inicio)

        fecha_fin = fecha_inicio + timedelta(
            days=plan.duracion_dias
        )

        membresia = {
            "id": str(len(self._membresias) + 1),
            "socio_id": socio.id_socio,
            "plan_id": plan.id_plan,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        }

        self._membresias.append(membresia)

        return membresia

    def listar_membresias(self, filtro="TODAS"):
        resultado = []

        for membresia in self._membresias:
            socio = self.buscar_socio(
                membresia["socio_id"]
            )

            plan = self.buscar_plan(
                membresia["plan_id"]
            )

            estado = self._estado_membresia(membresia)

            proxima = (
                estado == "VIGENTE"
                and self.esta_proxima_a_vencer(
                    membresia["fecha_fin"],
                    date.today()
                )
            )

            fila = {
                "id": membresia["id"],
                "socio_id": socio.id_socio,
                "socio": f"{socio.nombre} {socio.apellido}",
                "documento": socio.dni,
                "plan_id": plan.id_plan,
                "plan": plan.nombre,
                "fecha_inicio": membresia["fecha_inicio"],
                "fecha_fin": membresia["fecha_fin"],
                "estado": estado,
                "proxima": proxima,
            }

            if filtro == "TODAS":
                resultado.append(fila)

            elif filtro == "PROXIMAS" and proxima:
                resultado.append(fila)

            elif filtro == estado:
                resultado.append(fila)

        return resultado

    def _estado_membresia(self, membresia):
        hoy = date.today()

        if hoy < membresia["fecha_inicio"]:
            return "PROGRAMADA"

        if hoy > membresia["fecha_fin"]:
            return "VENCIDA"

        return "VIGENTE"

    # =====================================
    # GESTIÓN DE ENTRENADORES
    # =====================================

    def registrar_entrenador(
        self, nombre, especialidad
    ):
        nombre = str(nombre).strip()
        especialidad = str(especialidad).strip()

        if not nombre:
            raise ValidationError(
                "El nombre del entrenador es obligatorio."
            )

        if not especialidad:
            raise ValidationError(
                "La especialidad es obligatoria."
            )

        for existente in self._entrenadores:
            if existente["nombre"].casefold() == nombre.casefold():
                raise DuplicateEntityError(
                    "Ya existe un entrenador con ese nombre."
                )

        entrenador = {
            "id": str(len(self._entrenadores) + 1),
            "nombre": nombre,
            "especialidad": especialidad,
        }

        self._entrenadores.append(entrenador)

        return entrenador

    def listar_entrenadores(self):
        return list(self._entrenadores)

    # =====================================
    # CONTROL DE ACCESO
    # =====================================

    def verificar_acceso(self, socio_id):
        socio = self.buscar_socio(socio_id)

        membresias = [
            membresia
            for membresia in self._membresias
            if membresia["socio_id"] == socio.id_socio
        ]

        nombre = f"{socio.nombre} {socio.apellido}"

        if not membresias:
            return {
                "permitido": False,
                "socio": nombre,
                "mensaje": "El socio no tiene una membresía registrada.",
            }

        for membresia in membresias:
            if self._estado_membresia(membresia) == "VIGENTE":
                return {
                    "permitido": True,
                    "socio": nombre,
                    "mensaje": "La membresía del socio se encuentra vigente.",
                }

        return {
            "permitido": False,
            "socio": nombre,
            "mensaje": "El socio no tiene una membresía vigente.",
        }

    # =====================================
    # GESTIÓN DE ASISTENCIAS
    # =====================================

    def registrar_asistencia(self, socio_id):
        acceso = self.verificar_acceso(socio_id)

        if not acceso["permitido"]:
            raise ValidationError(
                "No se puede registrar la asistencia porque el acceso está denegado."
            )

        socio = self.buscar_socio(socio_id)

        asistencia = {
            "id": str(len(self._asistencias) + 1),
            "socio_id": socio.id_socio,
            "fecha_hora": datetime.now(),
        }

        self._asistencias.append(asistencia)

        return asistencia

    def listar_asistencias(self, filtro=""):
        fecha_filtro = None

        if filtro:
            try:
                fecha_filtro = date.fromisoformat(str(filtro))
            except ValueError:
                raise ValidationError(
                    "La fecha debe tener el formato AAAA-MM-DD."
                )

        resultado = []

        for asistencia in self._asistencias:
            if (
                fecha_filtro is not None
                and asistencia["fecha_hora"].date() != fecha_filtro
            ):
                continue

            socio = self.buscar_socio(
                asistencia["socio_id"]
            )

            resultado.append(
                {
                    "socio": f"{socio.nombre} {socio.apellido}",
                    "documento": socio.dni,
                    "fecha_hora": asistencia[
                        "fecha_hora"
                    ].isoformat(timespec="minutes"),
                }
            )

        return resultado

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

        limite = fecha_actual + timedelta(
            days=self.DIAS_AVISO
        )

        return fecha_actual <= fecha_vencimiento <= limite

    def _convertir_fecha(self, valor):
        if type(valor) is date:
            return valor

        try:
            return date.fromisoformat(str(valor))
        except (ValueError, TypeError):
            raise ValidationError(
                "La fecha debe tener el formato AAAA-MM-DD."
            )