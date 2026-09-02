import { describe, expect, it } from 'vitest'

import {
  createAddressInput,
  createContactInput,
  normalizeAddressInput,
  normalizeContactInput,
} from '../formFields'

describe('form fields', () => {
  it('cria valores independentes para contato e endereço', () => {
    const firstContact = createContactInput()
    const secondContact = createContactInput()
    const firstAddress = createAddressInput()

    firstContact.ddd = '11'
    firstAddress.cep = '01001-000'

    expect(secondContact.ddd).toBe('')
    expect(createAddressInput().cep).toBe('')
  })

  it('normaliza telefone e CEP para o contrato da API', () => {
    expect(
      normalizeContactInput({ codigo_pais: '+55', ddd: '(11)', numero: '99999-1234' }),
    ).toEqual({ codigo_pais: '+55', ddd: '11', numero: '999991234' })

    expect(normalizeAddressInput(createAddressInput({ cep: '01001-000' })).cep).toBe('01001000')
  })
})
