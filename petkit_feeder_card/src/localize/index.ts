import zh from './zh.json';
import en from './en.json';

const LANGUAGES: Record<string, Record<string, string>> = {
  zh,
  en,
};

const DEFAULT_LANGUAGE = 'zh';

export function localize(
  key: string,
  language: string = DEFAULT_LANGUAGE,
  params?: Record<string, string | number>
): string {
  let text = LANGUAGES[language]?.[key] || LANGUAGES[DEFAULT_LANGUAGE]?.[key] || key;

  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(`{${k}}`, String(v));
    });
  }

  return text;
}

export function getLanguage(hass: { locale?: { language: string } }): string {
  const lang = hass?.locale?.language || DEFAULT_LANGUAGE;
  if (lang.startsWith('zh')) return 'zh';
  if (LANGUAGES[lang]) return lang;
  return DEFAULT_LANGUAGE;
}