import { api } from "../api/client";

const REVIEWER_PAGE_SIZE = 100;

export async function loadAllReviewerAssignments(authenticatedRequest) {
  const firstPage = await authenticatedRequest((token) =>
    api.listAssignments(token, { page: 1, page_size: REVIEWER_PAGE_SIZE }),
  );
  const totalPages = Math.max(Number(firstPage?.total_pages) || 1, 1);

  if (totalPages === 1) return firstPage?.items || [];

  const remainingPages = await Promise.all(
    Array.from({ length: totalPages - 1 }, (_, index) =>
      authenticatedRequest((token) =>
        api.listAssignments(token, {
          page: index + 2,
          page_size: REVIEWER_PAGE_SIZE,
        }),
      ),
    ),
  );

  return [firstPage, ...remainingPages].flatMap((page) => page?.items || []);
}
