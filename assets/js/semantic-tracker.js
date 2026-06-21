(function () {
  const start = Date.now();
  const page = window.location.href;

  function store(event, data = {}) {
    const payload = {
      page,
      event,
      timestamp: Date.now(),
      ...data
    };

    let existing = JSON.parse(localStorage.getItem("uh_events") || "[]");
    existing.push(payload);
    localStorage.setItem("uh_events", JSON.stringify(existing));
  }

  window.addEventListener("beforeunload", function () {
    store("dwell", { ms: Date.now() - start });
  });

  document.addEventListener("click", function (e) {
    const a = e.target.closest("a");
    if (!a) return;

    store("click", { to: a.href });
  });
})();
