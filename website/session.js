(() => {
  const appBase = "https://app.parallellingvo.app";
  const navigation = document.querySelector("nav");
  const signup = navigation && navigation.querySelector(".nav-signup");
  const openApp = navigation && navigation.querySelector(".btn-small");
  if (!signup || !openApp) return;

  openApp.hidden = true;
  const logout = document.createElement("a");
  logout.className = "btn btn-small";
  logout.href = `${appBase}/auth/logout`;
  logout.textContent = "Log out";
  logout.setAttribute("aria-label", "Log out from ParallelLingvo");
  logout.hidden = true;
  navigation.append(logout);

  fetch(`${appBase}/auth/session-profile`, { credentials: "include" })
    .then((response) => response.ok ? response.json() : null)
    .then((status) => {
      if (!status || !status.auth) return;
      signup.hidden = true;
      signup.setAttribute("aria-hidden", "true");
      openApp.hidden = false;
      logout.hidden = false;
    })
    .catch(() => {});
})();
