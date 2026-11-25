/* Mirrors the published Solvronix theme tokens into Ugavi-owned public pages. */
(() => {
  if (
    !document.querySelector(".lokado-site, .ugavi-portal, .lokado-nav, .lokado-footer")
  ) {
    return;
  }

  const apply = (css) => {
    if (!css) return;
    const existing = document.getElementById("ugavi-solvronix-theme-bridge");
    const style = existing || document.createElement("style");
    style.id = "ugavi-solvronix-theme-bridge";
    style.textContent = css;
    if (!existing) document.head.appendChild(style);
  };

  try {
    apply(sessionStorage.getItem("ugavi:solvronix-theme-css"));
  } catch {
    // Storage is optional; static LOKADO tokens are already available.
  }

  fetch("/api/method/solvronix_desk.api.get_theme_css", {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  })
    .then((response) => (response.ok ? response.json() : null))
    .then((payload) => {
      if (!payload?.message) return;
      apply(payload.message);
      try {
        sessionStorage.setItem("ugavi:solvronix-theme-css", payload.message);
      } catch {
        // Ignore storage restrictions in hardened/private browser contexts.
      }
    })
    .catch(() => {
      // Static LOKADO tokens remain available when Theme Studio is unavailable.
    });
})();
