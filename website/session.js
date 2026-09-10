(() => {
  const appBase = "https://app.parallellingvo.app";
  const links = document.querySelectorAll("[data-auth-link]");
  if (!links.length) return;

  fetch(`${appBase}/auth/session-profile`, { credentials: "include" })
    .then((response) => response.ok ? response.json() : null)
    .then((status) => {
      if (!status || !status.auth) return;
      links.forEach((link) => {
        link.textContent = "Log out";
        link.href = `${appBase}/auth/logout`;
        link.setAttribute("aria-label", "Log out from ParallelLingvo");
      });
    })
    .catch(() => {});
})();
