/* Iconen voor ingrediënten zonder AH-productfoto.
   Water, zout en peper zijn geen boodschappen, dus daar hoort geen pak bij —
   maar een leeg vakje zegt niets. Een getekend icoontje laat in één oogopslag
   zien waar het om gaat. */

const INGREDIENT_ICONEN = [
  { sleutel: 'water',    woorden: ['water', 'kraanwater', 'ijsblokjes'] },
  { sleutel: 'zout',     woorden: ['zout', 'zeezout', 'keukenzout'] },
  { sleutel: 'peper',    woorden: ['peper', 'pepervlokken', 'chilivlokken', 'chili'] },
  { sleutel: 'olie',     woorden: ['olie', 'olijfolie', 'zonnebloemolie', 'sesamolie'] },
  { sleutel: 'kruiden',  woorden: ['kruiden', 'oregano', 'tijm', 'basilicum', 'peterselie',
                                   'dille', 'bieslook', 'salie', 'dragon', 'rozemarijn',
                                   'za', 'paprikapoeder', 'komijn', 'kaneel', 'nootmuskaat'] },
  { sleutel: 'citroen',  woorden: ['citroen', 'limoen', 'citroensap'] },
  { sleutel: 'azijn',    woorden: ['azijn', 'balsamico'] },
  { sleutel: 'suiker',   woorden: ['suiker', 'honing', 'siroop', 'maple'] },
  { sleutel: 'bouillon', woorden: ['bouillon', 'bouillonblokje', 'bouillonpoeder'] },
  { sleutel: 'boter',    woorden: ['boter', 'roomboter', 'margarine'] },
];

const ICOON_PADEN = {
  water:    '<path d="M12 3.5c3.4 4 5.5 6.7 5.5 9.3a5.5 5.5 0 1 1-11 0c0-2.6 2.1-5.3 5.5-9.3z"/>',
  zout:     '<path d="M8.5 9h7l.8 10.5H7.7zM9.5 9V6.5a2.5 2.5 0 0 1 5 0V9"/><path d="M11 12.5h.01M13 14.5h.01"/>',
  peper:    '<path d="M9 8.5h6l.7 11H8.3z"/><path d="M9.5 8.5c0-1.6.5-3 2.5-3s2.5 1.4 2.5 3"/><path d="M11 12h.01M13 14h.01M11 16h.01"/>',
  olie:     '<path d="M10 4h4v2.4l3 4.1V20H7v-9.5l3-4.1z"/><path d="M7 14h10"/>',
  kruiden:  '<path d="M12 20V9"/><path d="M12 12c0-3.3 2.7-6 6-6 0 3.3-2.7 6-6 6z"/><path d="M12 15c0-2.8-2.2-5-5-5 0 2.8 2.2 5 5 5z"/>',
  citroen:  '<ellipse cx="12" cy="12" rx="8" ry="6" transform="rotate(-30 12 12)"/><path d="M12 12l4.5-2.6M12 12l-4.5 2.6M12 12l1.3 4.8M12 12l-1.3-4.8"/>',
  azijn:    '<path d="M10.5 3.5h3V7l2.5 3.5V20H8v-9.5L10.5 7z"/><path d="M8 13h8"/><path d="M11 3.5V2.5h2v1"/>',
  suiker:   '<path d="M5 9h14v10H5z"/><path d="M5 9l2.5-4h9L19 9"/><path d="M9.5 5v4M14.5 5v4"/>',
  bouillon: '<path d="M4.5 10h15a7.5 7.5 0 0 1-7.5 7.5A7.5 7.5 0 0 1 4.5 10z"/><path d="M9 6.5c0-1 1-1.2 1-2.2M13 6.5c0-1 1-1.2 1-2.2"/><path d="M3.5 20h17"/>',
  boter:    '<path d="M3.5 12.5l4-4h13v7h-13z"/><path d="M7.5 8.5v7"/><path d="M3.5 12.5v7h13v-4"/>',
};

/* Welk icoon past bij deze ingrediëntnaam? Null als we het niet weten. */
function ingredientIcoon(naam) {
  const woorden = String(naam).toLowerCase().split(/[^a-zà-ÿ]+/).filter(Boolean);
  for (const { sleutel, woorden: lijst } of INGREDIENT_ICONEN) {
    const raak = woorden.some(w => lijst.some(v =>
      w === v || w.startsWith(v) || (v.length >= 6 && w.includes(v))));
    if (raak) return sleutel;
  }
  return null;
}

/* Geeft het blokje links van een ingrediënt: productfoto, icoon, of leeg. */
function ingredientVakje(naam, product) {
  if (product && product.afbeelding) {
    return `<img class="ingredient-foto" src="${product.afbeelding}" alt="" loading="lazy">`;
  }
  const icoon = ingredientIcoon(naam);
  if (icoon) {
    return `<span class="ingredient-foto--icoon" aria-hidden="true">
      <svg viewBox="0 0 24 24">${ICOON_PADEN[icoon]}</svg></span>`;
  }
  return '<span class="ingredient-foto--leeg"></span>';
}
