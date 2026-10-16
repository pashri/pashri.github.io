/**
 * Show a footnote's text in a popup while the mouse is over its number.
 * The popup stays open while the pointer is over it, so links inside it
 * can be clicked. Only on devices that can hover; elsewhere the number is
 * a plain link to the note.
 */
const CLOSE_DELAY_MS = 200;

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
  const state = { popup: null, timer: 0 };
  ref.addEventListener("mouseenter", () => {
    clearTimeout(state.timer);
    state.popup ??= open(note, ref, state);
  });
  ref.addEventListener("mouseleave", () => closeSoon(state));
}

/**
 * Close the popup after a short delay, unless the pointer comes back.
 * @param {{popup: HTMLDivElement | null, timer: number}} state The popup
 *   for one reference and its pending close timer.
 * @returns {void}
 */
function closeSoon(state) {
  clearTimeout(state.timer);
  state.timer = setTimeout(() => {
    state.popup?.remove();
    state.popup = null;
  }, CLOSE_DELAY_MS);
}

/**
 * Create the popup beside a reference, without the note's back-link.
 * @param {HTMLElement} note The footnote list item.
 * @param {HTMLAnchorElement} ref The footnote number link.
 * @param {{popup: HTMLDivElement | null, timer: number}} state The popup
 *   state shared with the reference's handlers.
 * @returns {HTMLDivElement} The popup, already in the page.
 */
function open(note, ref, state) {
  const popup = Object.assign(document.createElement("div"), {
    className: "fn-pop",
    innerHTML: note.innerHTML,
  });
  popup.querySelector(".footnote-backref")?.remove();
  keepOpenOnHover(popup, state);
  document.body.append(popup);
  place(popup, ref.getBoundingClientRect());
  return popup;
}

/**
 * Keep the popup open while the pointer is over it.
 * @param {HTMLDivElement} popup The popup element.
 * @param {{popup: HTMLDivElement | null, timer: number}} state The popup
 *   state shared with the reference's handlers.
 * @returns {void}
 */
function keepOpenOnHover(popup, state) {
  popup.addEventListener("mouseenter", () => clearTimeout(state.timer));
  popup.addEventListener("mouseleave", () => closeSoon(state));
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
