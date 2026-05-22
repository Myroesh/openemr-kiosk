import re
from datetime import date, datetime

NEW_PATIENT_CONSULTATION_REASONS = (
    "Consulta Inicial",
)

EXISTING_PATIENT_CONSULTATION_REASONS = (
    "Sesión",
    "Revisión de resultados",
    "Test",
    "Entrevista con los padres",
)

ALLOWED_CONSULTATION_REASONS = (
    *NEW_PATIENT_CONSULTATION_REASONS,
    *EXISTING_PATIENT_CONSULTATION_REASONS,
)


def clean_spaces(value):
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def clean_name(value):
    value = clean_spaces(value)

    if not value:
        return ""

    return value.title()


def normalize_text(value):
    return clean_spaces(value)


def normalize_ci(value):
    value = clean_spaces(value)

    if not value:
        return ""

    return value.upper()


def validate_ci_optional(ci_documento):
    ci_documento = normalize_ci(ci_documento)

    if not ci_documento:
        return ci_documento, None

    if len(ci_documento) < 4:
        return ci_documento, "El CI/documento parece demasiado corto."

    if len(ci_documento) > 20:
        return ci_documento, "El CI/documento parece demasiado largo."

    if not re.fullmatch(r"[A-Z0-9\- ]+", ci_documento):
        return ci_documento, "El CI/documento contiene caracteres no válidos."

    return ci_documento, None


def normalize_bolivian_mobile(value):
    value = clean_spaces(value)

    if not value:
        return ""

    value = value.replace(" ", "")
    value = value.replace("-", "")
    value = value.replace("(", "")
    value = value.replace(")", "")

    if value.startswith("+591"):
        value = value[4:]

    elif value.startswith("591"):
        value = value[3:]

    return value


def validate_bolivian_mobile_required(value, field_label="Teléfono"):
    phone = normalize_bolivian_mobile(value)

    if not phone:
        return phone, f"{field_label} es obligatorio."

    if not phone.isdigit():
        return phone, f"{field_label} debe contener solo números."

    if len(phone) != 8:
        return phone, f"{field_label} debe tener 8 dígitos."

    if phone[0] not in ("6", "7"):
        return phone, f"{field_label} debe ser un celular boliviano válido, empezando en 6 o 7."

    return phone, None


def validate_bolivian_mobile_optional(value, field_label="Teléfono"):
    phone = normalize_bolivian_mobile(value)

    if not phone:
        return "", None

    if not phone.isdigit():
        return phone, f"{field_label} debe contener solo números."

    if len(phone) != 8:
        return phone, f"{field_label} debe tener 8 dígitos."

    if phone[0] not in ("6", "7"):
        return phone, f"{field_label} debe ser un celular boliviano válido, empezando en 6 o 7."

    return phone, None


def parse_birth_date(value):
    value = clean_spaces(value)

    if not value:
        return None, "La fecha de nacimiento es obligatoria."

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None, "La fecha de nacimiento no tiene un formato válido."

    today = date.today()

    if parsed > today:
        return parsed, "La fecha de nacimiento no puede estar en el futuro."

    age = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))

    if age < 0:
        return parsed, "La edad calculada no es válida."

    if age > 120:
        return parsed, "La fecha de nacimiento parece demasiado antigua."

    return parsed, None


def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def validate_new_patient_data(raw_data, professionals):
    errors = []

    data = {
        "flow_type": "nuevo",
        "nombres": clean_name(raw_data.get("nombres")),
        "apellidos": clean_name(raw_data.get("apellidos")),
        "fecha_nacimiento": clean_spaces(raw_data.get("fecha_nacimiento")),
        "sexo": clean_spaces(raw_data.get("sexo")),
        "ci_documento": normalize_ci(raw_data.get("ci_documento")),
        "telefono": normalize_bolivian_mobile(raw_data.get("telefono")),
        "direccion": normalize_text(raw_data.get("direccion")),
        "motivo_consulta": normalize_text(raw_data.get("motivo_consulta")),
        "profesional_area": clean_spaces(raw_data.get("profesional_area")),
        "es_menor": 0,
        "padre_nombre": clean_name(raw_data.get("padre_nombre")),
        "padre_ci": normalize_ci(raw_data.get("padre_ci")),
        "padre_telefono": normalize_bolivian_mobile(raw_data.get("padre_telefono")),
        "madre_nombre": clean_name(raw_data.get("madre_nombre")),
        "madre_ci": normalize_ci(raw_data.get("madre_ci")),
        "madre_telefono": normalize_bolivian_mobile(raw_data.get("madre_telefono")),
    }

    if not data["nombres"]:
        errors.append("El nombre es obligatorio.")

    if not data["apellidos"]:
        errors.append("El apellido es obligatorio.")

    birth_date, birth_error = parse_birth_date(data["fecha_nacimiento"])
    if birth_error:
        errors.append(birth_error)
    else:
        age = calculate_age(birth_date)
        data["es_menor"] = 1 if age < 18 else 0

    allowed_sex_values = ("Male", "Female", "Other")
    if not data["sexo"]:
        errors.append("Debe seleccionar el sexo del paciente.")
    elif data["sexo"] not in allowed_sex_values:
        errors.append("El sexo seleccionado no es válido.")

    data["ci_documento"], ci_error = validate_ci_optional(data["ci_documento"])
    if ci_error:
        errors.append(ci_error)

    data["telefono"], phone_error = validate_bolivian_mobile_required(data["telefono"], "El celular")
    if phone_error:
        errors.append(phone_error)

    data["motivo_consulta"] = "Consulta Inicial"

    if data["motivo_consulta"] not in NEW_PATIENT_CONSULTATION_REASONS:
        errors.append("Para paciente nuevo, el motivo debe ser Consulta Inicial.")

    if not data["profesional_area"]:
        errors.append("Debe seleccionar un profesional.")

    if data["profesional_area"] and data["profesional_area"] not in professionals:
        errors.append("El profesional seleccionado no es válido.")

    if data["es_menor"] and not data["padre_nombre"] and not data["madre_nombre"]:
        errors.append("Para menores de edad, registre al menos el nombre del padre o de la madre.")

    data["padre_ci"], padre_ci_error = validate_ci_optional(data["padre_ci"])
    if padre_ci_error:
        errors.append(f"CI del padre: {padre_ci_error}")

    data["madre_ci"], madre_ci_error = validate_ci_optional(data["madre_ci"])
    if madre_ci_error:
        errors.append(f"CI de la madre: {madre_ci_error}")

    data["padre_telefono"], padre_phone_error = validate_bolivian_mobile_optional(
        data["padre_telefono"],
        "Teléfono del padre",
    )
    if padre_phone_error:
        errors.append(padre_phone_error)

    data["madre_telefono"], madre_phone_error = validate_bolivian_mobile_optional(
        data["madre_telefono"],
        "Teléfono de la madre",
    )
    if madre_phone_error:
        errors.append(madre_phone_error)

    return data, errors


def validate_existing_patient_data(raw_data, professionals):
    errors = []

    data = {
        "flow_type": "antiguo",
        "nombre": clean_name(raw_data.get("nombre")),
        "telefono": normalize_bolivian_mobile(raw_data.get("telefono")),
        "profesional_area": clean_spaces(raw_data.get("profesional_area")),
        "motivo_consulta": normalize_text(raw_data.get("motivo_consulta")),
    }

    if not data["nombre"] and not data["telefono"]:
        errors.append("Debe ingresar nombre del paciente o teléfono.")

    if data["telefono"]:
        data["telefono"], phone_error = validate_bolivian_mobile_optional(data["telefono"], "Teléfono")
        if phone_error:
            errors.append(phone_error)

    if not data["profesional_area"]:
        errors.append("Debe seleccionar un profesional.")

    if data["profesional_area"] and data["profesional_area"] not in professionals:
        errors.append("El profesional seleccionado no es válido.")

    if not data["motivo_consulta"]:
        errors.append("Debe seleccionar el motivo de consulta.")
    elif data["motivo_consulta"] not in ALLOWED_CONSULTATION_REASONS:
        errors.append("El motivo de consulta seleccionado no es válido.")

    return data, errors