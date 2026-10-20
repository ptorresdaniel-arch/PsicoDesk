
import re


def normalize_rut(value: object) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError("El RUT debe ser texto.")

    raw = value.strip().upper()

    # El RUT es opcional.
    if not raw:
        return None

    # Solo se aceptan números, K, puntos y guiones.
    if not re.fullmatch(r"[0-9K.-]+", raw):
        raise ValueError("El RUT contiene caracteres no válidos.")

    clean = raw.replace(".", "").replace("-", "")

    match = re.fullmatch(r"(\d{1,8})([\dK])", clean)

    if not match:
        raise ValueError(
            "El RUT debe contener un número y un dígito verificador."
        )

    body = str(int(match.group(1)))
    provided_verifier = match.group(2)

    if int(body) == 0:
        raise ValueError("El número del RUT no es válido.")

    total = 0
    multiplier = 2

    for digit in reversed(body):
        total += int(digit) * multiplier
        multiplier = 2 if multiplier == 7 else multiplier + 1

    remainder = 11 - (total % 11)

    expected_verifier = (
        "0"
        if remainder == 11
        else "K"
        if remainder == 10
        else str(remainder)
    )

    if provided_verifier != expected_verifier:
        raise ValueError(
            "El dígito verificador del RUT no es válido."
        )

    formatted_body = f"{int(body):,}".replace(",", ".")

    return f"{formatted_body}-{expected_verifier}"
