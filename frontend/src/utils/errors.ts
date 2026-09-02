import axios from 'axios'

interface ValidationDetail {
  loc?: Array<string | number>
  msg?: string
}

export function getErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : 'Ocorreu um erro inesperado.'
  }

  const detail = error.response?.data?.detail as string | ValidationDetail[] | undefined
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = item.loc?.slice(1).join('.')
        return field ? `${field}: ${item.msg ?? 'valor inválido'}` : (item.msg ?? 'Valor inválido')
      })
      .join(' | ')
  }
  return 'Não foi possível concluir a operação.'
}
