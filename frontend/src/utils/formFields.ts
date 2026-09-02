import type { ContatoInput, EnderecoInput } from '@/types/api'

import { formatPhone, onlyDigits } from './formatters'

export function createContactInput(overrides: Partial<ContatoInput> = {}): ContatoInput {
  return {
    codigo_pais: overrides.codigo_pais ?? '+55',
    ddd: overrides.ddd ?? '',
    numero: overrides.numero ? formatPhone(overrides.numero) : '',
  }
}

export function createAddressInput(overrides: Partial<EnderecoInput> = {}): EnderecoInput {
  return {
    logradouro: overrides.logradouro ?? '',
    numero: overrides.numero ?? '',
    complemento: overrides.complemento ?? null,
    cep: overrides.cep ?? '',
    bairro: overrides.bairro ?? '',
    estado_id: overrides.estado_id ?? null,
    cidade_id: overrides.cidade_id ?? null,
  }
}

export function normalizeContactInput(contact: ContatoInput): ContatoInput {
  return {
    codigo_pais: contact.codigo_pais,
    ddd: onlyDigits(contact.ddd).slice(0, 2),
    numero: onlyDigits(contact.numero).slice(0, 11),
  }
}

export function normalizeAddressInput(address: EnderecoInput): EnderecoInput {
  return {
    ...address,
    cep: onlyDigits(address.cep).slice(0, 8),
  }
}
