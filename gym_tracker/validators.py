from django.core.exceptions import ValidationError


def _is_number(value):
    # bool es subclase de int en Python: True no es un peso válido
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_series_data(value):
    """
    Series de un bloque de ejercicio: lista de {"repe": entero >= 1, "peso": número >= 0 (opcional)}.
    Ej: [{"repe": 12, "peso": 50}, {"repe": 10, "peso": 55}, {"repe": 15}]
    """
    if not isinstance(value, list):
        raise ValidationError("Las series tienen que ser una lista.")

    for number, serie in enumerate(value, start=1):
        if not isinstance(serie, dict) or set(serie) - {'repe', 'peso'}:
            raise ValidationError(f"Serie {number}: solo se permiten las claves 'repe' y 'peso'.")

        repe = serie.get('repe')
        if not isinstance(repe, int) or isinstance(repe, bool) or repe < 1:
            raise ValidationError(f"Serie {number}: 'repe' tiene que ser un entero mayor a 0.")

        peso = serie.get('peso')
        if peso is not None and (not _is_number(peso) or peso < 0):
            raise ValidationError(f"Serie {number}: 'peso' tiene que ser un número mayor o igual a 0.")
