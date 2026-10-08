from decimal import Decimal, InvalidOperation

from .exceptions import ValidationError


class Socio:
    """Representa a un socio registrado en el gimnasio."""

    def __init__(self, id_socio, nombre, apellido, dni, telefono, correo):
        self.__id_socio = self._validar_obligatorio(id_socio, "ID")
        self.__nombre = self._validar_obligatorio(nombre, "Nombre")
        self.__apellido = self._validar_obligatorio(apellido, "Apellido")
        self.__dni = self._validar_dni(dni)
        self.__telefono = self._validar_telefono(telefono)
        self.__correo = self._validar_correo(correo)

    @staticmethod
    def _validar_obligatorio(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValidationError(f"{campo} es obligatorio.")
        return valor.strip()

    @staticmethod
    def _validar_dni(dni):
        if not isinstance(dni, str) or len(dni) != 8 or not dni.isascii() or not dni.isdecimal():
            raise ValidationError("El DNI debe contener exactamente 8 dígitos.")
        return dni

    @staticmethod
    def _validar_telefono(telefono):
        if not isinstance(telefono, str) or len(telefono) != 9 or not telefono.isascii() or not telefono.isdecimal():
            raise ValidationError("El teléfono debe contener exactamente 9 dígitos.")
        return telefono

    @staticmethod
    def _validar_correo(correo):
        correo = Socio._validar_obligatorio(correo, "Correo")
        if correo.count("@") != 1:
            raise ValidationError("El correo debe tener un formato válido.")

        usuario, dominio = correo.split("@")
        if not usuario or "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
            raise ValidationError("El correo debe tener un formato válido.")

        return correo

    @property
    def id_socio(self):
        return self.__id_socio

    @property
    def nombre(self):
        return self.__nombre

    @property
    def apellido(self):
        return self.__apellido

    @property
    def dni(self):
        return self.__dni

    @property
    def telefono(self):
        return self.__telefono

    @property
    def correo(self):
        return self.__correo
    

class PlanMembresia:
    """Representa un plan de membresía del gimnasio."""

    def __init__(self, id_plan, nombre, precio, duracion_dias):
        self.__id_plan = self._validar_obligatorio(id_plan, "ID del plan")
        self.__nombre = self._validar_obligatorio(nombre, "Nombre del plan")
        self.__precio = self._validar_precio(precio)
        self.__duracion_dias = self._validar_duracion(duracion_dias)

    @staticmethod
    def _validar_obligatorio(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValidationError(f"{campo} es obligatorio.")
        return valor.strip()
    
    @staticmethod
    def _validar_precio(precio):
        try:
            valor = Decimal(str(precio))
        except (InvalidOperation, ValueError):
            raise ValidationError("El precio debe ser un número válido.")

        if not valor.is_finite() or valor <= 0:
            raise ValidationError("El precio debe ser mayor que cero.")

        return valor

    @staticmethod
    def _validar_duracion(duracion):
        if type(duracion) is not int or duracion <= 0:
            raise ValidationError("La duración debe ser un entero mayor que cero.")

        return duracion

    @property
    def id_plan(self):
        return self.__id_plan

    @property
    def nombre(self):
        return self.__nombre

    @property
    def precio(self):
        return self.__precio

    @property
    def duracion_dias(self):
        return self.__duracion_dias