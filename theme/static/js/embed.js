/**
 * Load each interactive figure's module and let it draw into its mount.
 * A module that fails to load shows the figure's fallback link instead.
 */
for (const figure of document.querySelectorAll("figure.embed")) {
  load(figure);
}

/**
 * Import one figure's module and call its default export.
 * @param {HTMLElement} figure The figure.embed element.
 * @returns {Promise<void>} Resolves once the module has drawn.
 */
async function load(figure) {
  const mount = figure.querySelector(".embed-mount");
  try {
    const module = await import(figure.dataset.src);
    await module.default(mount, figure.dataset.data);
  } catch (error) {
    figure.classList.add("embed-failed");
    console.error(error);
  }
}
