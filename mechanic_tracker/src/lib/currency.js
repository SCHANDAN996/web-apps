export function getLocalCurrency() {
  const locale = navigator.language;
  
  // Direct locale mapping
  const currencyMap = {
      'en-US': 'USD',
      'en-GB': 'GBP',
      'en-IN': 'INR',
      'hi-IN': 'INR',
      'en-AU': 'AUD',
      'en-CA': 'CAD',
      'ja-JP': 'JPY',
      'de-DE': 'EUR',
      'fr-FR': 'EUR',
      'it-IT': 'EUR',
      'es-ES': 'EUR',
  };
  
  if (currencyMap[locale]) return currencyMap[locale];
  
  // Check by country code in locale (e.g., "en-IN" -> "IN")
  const countryMatch = locale.match(/-([A-Z]{2})/i);
  if (countryMatch) {
      const country = countryMatch[1].toUpperCase();
      if (country === 'IN') return 'INR';
      if (country === 'US') return 'USD';
      if (country === 'GB') return 'GBP';
      if (country === 'AU') return 'AUD';
      if (country === 'CA') return 'CAD';
      if (['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'IE', 'FI', 'GR'].includes(country)) return 'EUR';
  }
  
  // Try to guess from timezone as a last resort
  try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (tz.includes('Calcutta') || tz.includes('Kolkata')) return 'INR';
      if (tz.includes('London')) return 'GBP';
      if (tz.includes('Europe/')) return 'EUR';
      if (tz.includes('Australia/')) return 'AUD';
  } catch (e) {}

  return 'USD'; // Default fallback
}

export function formatCurrency(amount) {
  const currency = getLocalCurrency();
  return new Intl.NumberFormat(navigator.language, {
      style: 'currency',
      currency: currency,
  }).format(amount || 0);
}

export function getCurrencySymbol() {
  const currency = getLocalCurrency();
  const formatter = new Intl.NumberFormat(navigator.language, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
  });
  // Extract just the symbol
  const parts = formatter.formatToParts(0);
  const symbolPart = parts.find(p => p.type === 'currency');
  return symbolPart ? symbolPart.value : '$';
}
