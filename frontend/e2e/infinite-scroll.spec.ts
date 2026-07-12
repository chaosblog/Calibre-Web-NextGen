import { test, expect, Page } from '@playwright/test';
import { collectPageErrors, assertNoPageErrors } from './utils';

/*
 * Infinite scrolling on the library grid uses a sentinel to auto-load the next
 * page. A persistent "Load more" button is its reachability fallback when an
 * observer is unavailable or never delivers an intersecting entry.
 *
 * The tests hide the optional Discover carousel so the grid's book links have a
 * clean count. They assert both paths: the button works when IntersectionObserver
 * never fires, and scrolling the real sentinel still auto-appends a page.
 *
 * Needs more than one page of books. CI's E2E job seeds a single book, so this
 * skips there; it runs for real against any library with >24 books (the local
 * dev container is seeded past that). A CI paginated-seed is tracked as a
 * follow-up to the SPA test-harness gap.
 */

const PER_PAGE = 24;

async function totalBooks(page: Page): Promise<number> {
  const res = await page.request.get('/api/v1/books?per_page=1');
  if (!res.ok()) return 0;
  const body = await res.json();
  return body.total ?? 0;
}

function gridBookLinks(page: Page) {
  // Quick-edit links end in /edit; each card's primary link ends in /book/<id>.
  return page.locator('main a[href*="/book/"]:not([href$="/edit"])');
}

function gridBookHrefs(page: Page): Promise<string[]> {
  return gridBookLinks(page).evaluateAll((els) =>
    els.map((e) => (e as HTMLAnchorElement).getAttribute('href') || ''),
  );
}

test.describe('library infinite scroll', () => {
  test.beforeEach(async ({ page }) => {
    // Keep the optional Discover links out of the book-grid count.
    await page.addInitScript(() => localStorage.setItem('cwng_discover_hidden_v1', 'true'));
  });

  test('Load more reaches the full library when IntersectionObserver never fires (#704)', async ({ page }) => {
    await page.addInitScript(() => {
      class NeverIntersectingObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
        takeRecords() { return []; }
      }
      window.IntersectionObserver = NeverIntersectingObserver as unknown as typeof IntersectionObserver;
    });

    const errors = collectPageErrors(page);
    await page.goto('/app');
    await expect(gridBookLinks(page).first()).toBeVisible();

    const total = await totalBooks(page);
    test.skip(total <= PER_PAGE, `library has ${total} books (≤ one page) — nothing to paginate`);

    const loadMore = page.getByRole('button', { name: 'Load more' });
    await expect(loadMore).toBeEnabled();

    const firstPage = await gridBookHrefs(page);
    expect(firstPage.length, 'first render shows exactly one page of cards').toBe(PER_PAGE);

    // The stub never reports an intersection, so every page advance below is
    // evidence that the visible, keyboard-operable fallback requested it.
    let count = firstPage.length;
    for (let i = 0; i < Math.ceil(total / PER_PAGE) && count < total; i++) {
      await expect(loadMore).toBeEnabled();
      await loadMore.click();
      await expect
        .poll(async () => (await gridBookHrefs(page)).length, { timeout: 8_000 })
        .toBeGreaterThan(count);
      count = (await gridBookHrefs(page)).length;
      expect(count).toBeLessThanOrEqual(total);
    }

    const finalHrefs = await gridBookHrefs(page);
    expect(finalHrefs.length, 'every book loaded with the fallback').toBe(total);
    expect(new Set(finalHrefs).size, 'no book card is duplicated across pages').toBe(finalHrefs.length);

    assertNoPageErrors(errors);
  });

  test('scrolling the sentinel still auto-appends a page', async ({ page }) => {
    const errors = collectPageErrors(page);
    await page.goto('/app');
    await expect(gridBookLinks(page).first()).toBeVisible();

    const total = await totalBooks(page);
    test.skip(total <= PER_PAGE, `library has ${total} books (≤ one page) — nothing to paginate`);

    const before = (await gridBookHrefs(page)).length;
    expect(before, 'first render shows exactly one page of cards').toBe(PER_PAGE);

    // The button lives in the observer target; scroll its parent (the sentinel)
    // into view and let the real observer request the next page.
    await page.getByRole('button', { name: 'Load more' }).locator('xpath=..').scrollIntoViewIfNeeded();
    await expect
      .poll(async () => (await gridBookHrefs(page)).length, { timeout: 8_000 })
      .toBeGreaterThan(before);

    assertNoPageErrors(errors);
  });
});
