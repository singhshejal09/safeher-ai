/* Retrieval admits only reviewed, dated entries with a source URL and jurisdiction. */
window.SafeHerKnowledge = (() => {
  const entries = Array.isArray(window.SAFEHER_KNOWLEDGE) ? window.SAFEHER_KNOWLEDGE : [];
  const approved = entries.filter(entry => {
    if (!entry || entry.status !== 'verified' || !entry.title || !entry.summary || !entry.jurisdiction || !entry.reviewedAt || !entry.sourceName) return false;
    const reviewDate = Date.parse(entry.reviewedAt);
    if (!Number.isFinite(reviewDate) || reviewDate > Date.now()) return false;
    try { return new URL(entry.url).protocol === 'https:' && Array.isArray(entry.categories); } catch { return false; }
  });
  return {
    search(category, language) {
      return approved.filter(entry => (category === '*' || entry.categories?.includes(category)) && (!entry.language || entry.language === language || entry.language === 'en'))
        .map(entry => ({ title: entry.title, summary: entry.summary, sourceName: entry.sourceName, jurisdiction: entry.jurisdiction, reviewedAt: entry.reviewedAt, url: entry.url }));
    }
  };
})();
