import { createContext, useContext, useState, useEffect } from "react";
import { T } from "../i18n.js";

const LangContext = createContext({ lang: "ar", t: T.ar, setLang: () => {} });

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(
    () => localStorage.getItem("cj_lang") || "ar"
  );

  const t = T[lang] ?? T.ar;

  function setLang(l) {
    setLangState(l);
    localStorage.setItem("cj_lang", l);
  }

  // Keep <html> dir + lang in sync so RTL CSS and screen-readers work correctly
  useEffect(() => {
    document.documentElement.dir  = t.dir;
    document.documentElement.lang = t.lang;
  }, [t]);

  return (
    <LangContext.Provider value={{ lang, t, setLang }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
