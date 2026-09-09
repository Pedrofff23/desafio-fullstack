import type { PaginatedResponse } from '@/types/api';

export async function listAllPages<T>(
  list: (params: { page: number; size: number }) => Promise<PaginatedResponse<T>>
): Promise<T[]> {
  const items: T[] = [];
  let page = 1;
  let pages: number;
  do {
    const response = await list({ page, size: 100 });
    items.push(...response.items);
    pages = response.pages;
    page += 1;
  } while (page <= pages);
  return items;
}
