// Mobile menu
const menuBtn = document.querySelector(".menu-btn");
const nav = document.getElementById("site-nav");
if (menuBtn && nav) {
  menuBtn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", open);
  });
}

// "Show all N authors" toggles
document.querySelectorAll(".more").forEach((btn) => {
  const label = btn.textContent;
  btn.addEventListener("click", () => {
    const list = btn.previousElementSibling;
    const collapsed = list.classList.toggle("collapsed");
    btn.textContent = collapsed ? label : "Show fewer authors";
    btn.setAttribute("aria-expanded", !collapsed);
  });
});

// Publications: search + paper/preprint filter
const search = document.getElementById("pub-search");
if (search) {
  const groups = document.querySelectorAll(".year-group");
  const highlighted = document.getElementById("highlighted");
  const empty = document.getElementById("no-results");
  const yearSelect = document.getElementById("year-select");
  let kind = "all";

  const apply = () => {
    const terms = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const year = yearSelect ? yearSelect.value : "";
    const filtering = terms.length > 0 || kind !== "all" || year !== "";
    let shown = 0;
    groups.forEach((group) => {
      let visible = 0;
      if (year && group.id !== year) {
        group.hidden = true;
        return;
      }
      group.querySelectorAll(".pub").forEach((li) => {
        const text = li.textContent.toLowerCase();
        const ok = (kind === "all" || li.dataset.kind === kind) && terms.every((t) => text.includes(t));
        li.hidden = !ok;
        if (ok) visible++;
      });
      group.hidden = visible === 0;
      shown += visible;
    });
    if (highlighted) highlighted.hidden = filtering;
    empty.hidden = shown > 0;
  };

  search.addEventListener("input", apply);
  if (yearSelect) yearSelect.addEventListener("change", () => { apply(); window.scrollTo({ top: 0 }); });
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("on", c === chip));
      kind = chip.dataset.filter;
      apply();
    });
  });

  // Highlight the year pill for the section currently on screen
  const pills = [...document.querySelectorAll(".year-nav a")];
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      pills.forEach((p) => {
        const on = p.getAttribute("href") === "#" + e.target.id;
        p.classList.toggle("active", on);
        if (on && p.parentElement.classList.contains("tabs")) p.scrollIntoView({ block: "nearest", inline: "nearest" });
      });
    });
  }, { rootMargin: "-90px 0px -70% 0px" });
  document.querySelectorAll("#highlighted, .year-group").forEach((s) => observer.observe(s));
}
