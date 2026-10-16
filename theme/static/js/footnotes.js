/**
 * Show a footnote's text in a popup while the mouse is over its number.
 * Only on devices that can hover; elsewhere the number is a plain link.
 */
if (matchMedia("(hover: hover)").matches) {
  for (const ref of document.querySelectorAll("a.footnote-ref")) {
    attach(ref);
  }
}

/**
 * Add hover handlers that open and close the popup for one reference.
 * @param {HTMLAnchorElement} ref The footnote number link.
 * @returns {void}
 */
function attach(ref) {
  const note = document.getElementById(ref.hash.slice(1));
  let popup = null;
  ref.addEventListener("mouseenter", () => { popup = open(note, ref); });
  ref.addEventListener("mouseleave", () => popup?.remove());
}

/**
 * Create the popup beside a reference, without the note's back-link.
 * @param {HTMLElement} note The footnote list item.
 * @param {HTMLAnchorElement} ref The footnote number link.
 * @returns {HTMLDivElement} The popup, already in the page.
 */
function open(note, ref) {
  const popup = Object.assign(document.createElement("div"), {
    className: "fn-pop", innerHTML: note.innerHTML,
  });
  popup.querySelector(".footnote-backref")?.remove();
  document.body.append(popup);
  place(popup, ref.getBoundingClientRect());
  return popup;
}

/**
 * Position the popup under the reference, kept inside the window.
 * @param {HTMLDivElement} popup The popup element.
 * @param {DOMRect} box The reference's position on screen.
 * @returns {void}
 */
function place(popup, box) {
  const left = Math.min(box.left, innerWidth - popup.offsetWidth - 16);
  popup.style.left = `${Math.max(8, left) + scrollX}px`;
  popup.style.top = `${box.bottom + scrollY + 6}px`;
}
