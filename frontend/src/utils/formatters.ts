export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

export function formatQuantity(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 }).format(value)
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value)
  const date = new Date(dateOnly ? `${value}T00:00:00` : value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('pt-BR')
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('pt-BR')
}

export function onlyDigits(value: string): string {
  return value.replace(/\D/g, '')
}

export function formatCepInput(value: string): string {
  const digits = onlyDigits(value).slice(0, 8)
  return digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits
}

export function formatPhone(value: string | null | undefined): string {
  if (!value) return ''
  const digits = onlyDigits(value).slice(0, 11)
  if (digits.length === 0) return ''
  if (digits.length <= 4) return digits
  if (digits.length === 8) {
    return `${digits.slice(0, 4)}-${digits.slice(4)}`
  }
  if (digits.length === 9) {
    return `${digits.slice(0, 5)}-${digits.slice(5)}`
  }
  if (digits.length === 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  }
  if (digits.length === 11) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
  }
  const split = digits.length > 8 ? digits.length - 4 : 4
  return `${digits.slice(0, split)}-${digits.slice(split)}`
}

export const formatPhoneInput = formatPhone

export function formatContact(
  contact:
    | { ddd?: string | null; numero?: string | null; codigo_pais?: string | null }
    | null
    | undefined,
): string {
  if (!contact || (!contact.ddd && !contact.numero)) return '—'
  const ddd = contact.ddd ? onlyDigits(contact.ddd) : ''
  const phone = contact.numero ? formatPhone(contact.numero) : ''
  if (ddd && phone) return `(${ddd}) ${phone}`
  return phone || '—'
}

export function toIsoDateTime(value: string): string | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.toISOString()
}
