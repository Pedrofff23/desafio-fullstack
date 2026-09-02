import { describe, expect, it } from 'vitest'

import {
  formatCepInput,
  formatContact,
  formatCurrency,
  formatPhone,
  formatPhoneInput,
  onlyDigits,
  toIsoDateTime,
} from '../formatters'

describe('formatters', () => {
  it('formata valores monetários em reais', () => {
    expect(formatCurrency(19.9)).toContain('19,90')
  })

  it('remove caracteres não numéricos', () => {
    expect(onlyDigits('(11) 99999-1234')).toBe('11999991234')
  })

  it('aplica máscaras de CEP e telefone (8 e 9 dígitos)', () => {
    expect(formatCepInput('01001000')).toBe('01001-000')
    // 8 dígitos (ex: 4444-4444)
    expect(formatPhone('44444444')).toBe('4444-4444')
    expect(formatPhoneInput('33221234')).toBe('3322-1234')
    // 9 dígitos (ex: 99999-9999)
    expect(formatPhone('999999999')).toBe('99999-9999')
    expect(formatPhoneInput('987654321')).toBe('98765-4321')
    // Com DDD completo
    expect(formatPhone('1144444444')).toBe('(11) 4444-4444')
    expect(formatPhone('11999999999')).toBe('(11) 99999-9999')
  })

  it('formata objeto de contato com DDD e máscara adequada', () => {
    expect(formatContact({ ddd: '11', numero: '44444444' })).toBe('(11) 4444-4444')
    expect(formatContact({ ddd: '11', numero: '999999999' })).toBe('(11) 99999-9999')
    expect(formatContact(null)).toBe('—')
    expect(formatContact({ ddd: '', numero: '' })).toBe('—')
  })

  it('mantém data vazia como nula para o backend aplicar o horário atual', () => {
    expect(toIsoDateTime('')).toBeNull()
  })
})
