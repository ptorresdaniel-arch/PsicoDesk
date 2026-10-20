
export function cleanRutInput(value: string): string {
  const cleaned = value
    .replace(/[^0-9kK]/g, '')
    .toUpperCase()
    .slice(0, 9)

  if (cleaned.length === 0) return ''

  const body = cleaned.slice(0, -1).replace(/K/g, '')
  const verifier = cleaned.slice(-1)

  return `${body}${verifier}`.slice(0, 9)
}

export function formatRut(
  value: string | null | undefined,
): string {
  const clean = cleanRutInput(value ?? '')

  if (clean.length < 2) return clean

  const body = clean.slice(0, -1)
  const verifier = clean.slice(-1)

  const formattedBody = body.replace(
    /\B(?=(\d{3})+(?!\d))/g,
    '.',
  )

  return `${formattedBody}-${verifier}`
}

export function isValidRut(
  value: string | null | undefined,
): boolean {
  const clean = cleanRutInput(value ?? '')

  const match = clean.match(/^(\d{1,8})([\dK])$/)

  if (!match) return false

  const body = match[1]
  const providedVerifier = match[2]

  let sum = 0
  let multiplier = 2

  for (let i = body.length - 1; i >= 0; i--) {
    sum += Number(body[i]) * multiplier

    multiplier = multiplier === 7 ? 2 : multiplier + 1
  }

  const remainder = 11 - (sum % 11)

  const expectedVerifier =
    remainder === 11
      ? '0'
      : remainder === 10
        ? 'K'
        : String(remainder)

  return providedVerifier === expectedVerifier
}
