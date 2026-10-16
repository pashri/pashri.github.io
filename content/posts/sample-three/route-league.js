/**
 * Draw a horizontal bar per route from the sample JSON.
 * @param {HTMLElement} mount Where the chart goes.
 * @param {string} dataUrl URL of a JSON list of {route, share}.
 * @returns {Promise<void>} Resolves once drawn.
 */
export default async function draw(mount, dataUrl) {
  const rows = await (await fetch(dataUrl)).json();
  const list = document.createElement("div");
  list.style.cssText = "display:grid;gap:6px;font:14px var(--sans)";
  list.append(...rows.map(bar));
  mount.replaceChildren(list);
}

/**
 * Build one labelled bar.
 * @param {{route: string, share: number}} row One route's value.
 * @returns {HTMLDivElement} The bar's row.
 */
function bar(row) {
  const line = document.createElement("div");
  line.style.cssText = "display:grid;grid-template-columns:5em 1fr;gap:8px";
  const width = `${Math.round(row.share * 100)}%`;
  line.innerHTML = `<span>${row.route}</span><span style="background:var(--muted);width:${width}">&nbsp;</span>`;
  return line;
}
