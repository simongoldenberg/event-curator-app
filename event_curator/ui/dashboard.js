(() => {
  "use strict";
  const payload = JSON.parse(document.getElementById("dashboard-data").textContent);
  const world = document.getElementById("map-world");
  const frame = document.getElementById("map-frame");
  const pins = document.getElementById("map-pins");
  const venueList = document.getElementById("venue-list");
  const popup = document.getElementById("map-popup");
  const cards = [...document.querySelectorAll(".event-card")];
  const search = document.getElementById("event-search");
  const resultCount = document.getElementById("result-count");
  const noResults = document.getElementById("no-results");
  const categoryButtons = [...document.querySelectorAll("[data-category-filter]")];
  const regionButtons = [...document.querySelectorAll("[data-region-filter]")];
  let activeCategory = "all";
  let activeRegion = "all";
  let scale = 1;
  let translateX = 0;
  let translateY = 0;
  let dragging = null;
  let selectedPin = null;

  function plain(value) {
    return String(value || "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }

  function projected(latitude, longitude) {
    return {
      x: ((longitude - 3) / 17.5) * 100,
      y: ((55.5 - latitude) / 10.5) * 100,
    };
  }

  function limitPan() {
    const width = frame.clientWidth;
    const height = frame.clientHeight;
    translateX = Math.min(0, Math.max(width * (1 - scale), translateX));
    translateY = Math.min(0, Math.max(height * (1 - scale), translateY));
  }

  function paintTransform() {
    limitPan();
    world.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
  }

  function zoom(next, pointX = frame.clientWidth / 2, pointY = frame.clientHeight / 2) {
    const bounded = Math.max(1, Math.min(4, next));
    const ratio = bounded / scale;
    translateX = pointX - (pointX - translateX) * ratio;
    translateY = pointY - (pointY - translateY) * ratio;
    scale = bounded;
    paintTransform();
  }

  function focusPoint(latitude, longitude, requestedScale = 2.4) {
    const point = projected(latitude, longitude);
    scale = requestedScale;
    translateX = frame.clientWidth / 2 - point.x * frame.clientWidth / 100 * scale;
    translateY = frame.clientHeight / 2 - point.y * frame.clientHeight / 100 * scale;
    paintTransform();
  }

  function visibleCards() {
    return cards.filter(card => !card.hidden);
  }

  function groupVenues() {
    const visible = new Set(visibleCards().map(card => card.id));
    const groups = new Map();
    for (const event of payload.events) {
      if (!visible.has(event.id) || event.latitude === null || event.longitude === null) continue;
      const key = `${event.venue || event.city}|${event.latitude.toFixed(3)}|${event.longitude.toFixed(3)}`;
      if (!groups.has(key)) groups.set(key, {
        name: event.venue || `Ort in ${event.city} nicht benannt`,
        city: event.city,
        latitude: event.latitude,
        longitude: event.longitude,
        events: [],
      });
      groups.get(key).events.push(event);
    }
    return [...groups.values()];
  }

  function showPopup(group, button) {
    if (selectedPin) selectedPin.classList.remove("active");
    selectedPin = button;
    button.classList.add("active");
    popup.hidden = false;
    popup.querySelector("strong").textContent = group.name;
    popup.querySelector("p").textContent = `${group.city} · ${group.events.length} ${group.events.length === 1 ? "Event" : "Events"}`;
    popup.querySelector("[data-open-event]").onclick = () => {
      const card = document.getElementById(group.events[0].id);
      if (card) card.scrollIntoView({ behavior: "smooth", block: "center" });
    };
  }

  function renderVenues() {
    const groups = groupVenues();
    pins.replaceChildren();
    venueList.replaceChildren();
    popup.hidden = true;
    selectedPin = null;
    for (const group of groups) {
      const point = projected(group.latitude, group.longitude);
      const pin = document.createElement("button");
      pin.type = "button";
      pin.className = "map-pin";
      pin.style.left = `${point.x}%`;
      pin.style.top = `${point.y}%`;
      pin.title = `${group.name}, ${group.city}`;
      pin.setAttribute("aria-label", `${group.name}, ${group.city}: ${group.events.length} Events`);
      const pinSymbol = document.createElement("span");
      pinSymbol.textContent = group.events.length > 1 ? String(group.events.length) : "•";
      pin.append(pinSymbol);
      pin.addEventListener("click", () => showPopup(group, pin));
      pins.append(pin);

      const item = document.createElement("button");
      item.type = "button";
      item.className = "venue-item";
      const dot = document.createElement("span");
      dot.className = "venue-symbol";
      dot.setAttribute("aria-hidden", "true");
      const text = document.createElement("span");
      const name = document.createElement("strong");
      name.textContent = group.name;
      const details = document.createElement("small");
      details.textContent = `${group.city} · ${group.events.length} ${group.events.length === 1 ? "Event" : "Events"}`;
      text.append(name, details);
      item.append(dot, text);
      item.addEventListener("click", () => {
        focusPoint(group.latitude, group.longitude);
        showPopup(group, pin);
      });
      venueList.append(item);
    }
    if (!groups.length) {
      const info = document.createElement("p");
      info.className = "event-meta";
      info.style.padding = "14px";
      info.textContent = "Für diese Auswahl sind keine Venues mit Koordinaten vorhanden.";
      venueList.append(info);
    }
    document.getElementById("venue-count").textContent = String(groups.length);
  }

  function filterEvents() {
    const query = plain(search.value.trim());
    for (const card of cards) {
      card.hidden = !(activeCategory === "all" || card.dataset.category === activeCategory)
        || !(activeRegion === "all" || card.dataset.region === activeRegion)
        || !plain(card.dataset.search).includes(query);
    }
    const count = visibleCards().length;
    resultCount.textContent = `${count} ${count === 1 ? "Event" : "Events"} sichtbar`;
    noResults.hidden = count !== 0;
    for (const section of document.querySelectorAll("[data-event-section]")) {
      const inSection = [...section.querySelectorAll(".event-card")].filter(card => !card.hidden).length;
      section.querySelector("[data-section-count]").textContent = String(inSection);
      section.querySelector(".section-empty").hidden = inSection !== 0;
    }
    renderVenues();
  }

  function press(buttons, selected, attribute) {
    for (const button of buttons) button.setAttribute("aria-pressed", String(button.dataset[attribute] === selected));
  }

  for (const button of categoryButtons) button.addEventListener("click", () => {
    activeCategory = button.dataset.categoryFilter;
    press(categoryButtons, activeCategory, "categoryFilter");
    filterEvents();
  });
  for (const button of regionButtons) button.addEventListener("click", () => {
    activeRegion = button.dataset.regionFilter;
    press(regionButtons, activeRegion, "regionFilter");
    filterEvents();
    const region = payload.regions.find(item => item.name === activeRegion);
    if (region) focusPoint(region.latitude, region.longitude, 2.2);
    else { scale = 1; translateX = 0; translateY = 0; paintTransform(); }
  });
  search.addEventListener("input", filterEvents);

  document.querySelectorAll("[data-map-event]").forEach(button => button.addEventListener("click", () => {
    const selected = payload.events.find(event => event.id === button.dataset.mapEvent);
    document.getElementById("karte").scrollIntoView({ behavior: "smooth" });
    if (!selected || selected.latitude === null || selected.longitude === null) return;
    focusPoint(selected.latitude, selected.longitude);
    const group = groupVenues().find(item => item.events.some(event => event.id === selected.id));
    const marker = [...pins.children].find(pin => pin.title === `${group?.name}, ${group?.city}`);
    if (group && marker) showPopup(group, marker);
  }));

  document.getElementById("zoom-in").addEventListener("click", () => zoom(scale * 1.4));
  document.getElementById("zoom-out").addEventListener("click", () => zoom(scale / 1.4));
  document.getElementById("zoom-reset").addEventListener("click", () => {
    scale = 1; translateX = 0; translateY = 0; paintTransform();
  });
  document.getElementById("popup-close").addEventListener("click", () => {
    popup.hidden = true;
    if (selectedPin) selectedPin.classList.remove("active");
  });
  frame.addEventListener("wheel", event => {
    event.preventDefault();
    const rect = frame.getBoundingClientRect();
    zoom(scale * (event.deltaY < 0 ? 1.15 : 1 / 1.15), event.clientX - rect.left, event.clientY - rect.top);
  }, { passive: false });
  frame.addEventListener("pointerdown", event => {
    if (event.target.closest("button")) return;
    dragging = { x: event.clientX, y: event.clientY };
    world.classList.add("dragging");
    frame.setPointerCapture(event.pointerId);
  });
  frame.addEventListener("pointermove", event => {
    if (!dragging) return;
    translateX += event.clientX - dragging.x;
    translateY += event.clientY - dragging.y;
    dragging = { x: event.clientX, y: event.clientY };
    paintTransform();
  });
  function finishDrag() { dragging = null; world.classList.remove("dragging"); }
  frame.addEventListener("pointerup", finishDrag);
  frame.addEventListener("pointercancel", finishDrag);
  window.addEventListener("resize", paintTransform);
  filterEvents();
})();
