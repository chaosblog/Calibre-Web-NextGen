import { describe, expect, it } from 'vitest';
import { DEFAULT_THEME, resolveTheme, THEME_SLUGS } from './themes';

describe('theme registry', () => {
  it('resolves supported, unknown, and system theme slugs', () => {
    expect(resolveTheme('sepia')).toBe('sepia');
    expect(resolveTheme('bogus')).toBe('dark');
    expect(['light', 'dark']).toContain(resolveTheme('system'));
  });

  it('exposes every supported theme and a dark default', () => {
    expect(THEME_SLUGS).toEqual(expect.arrayContaining([
      'system', 'light', 'dark', 'sepia', 'high-contrast', 'midnight',
    ]));
    expect(DEFAULT_THEME).toBe('dark');
  });
});
