(() => {
  const search = document.querySelector('#catalog-search');
  const category = document.querySelector('#category-filter');
  const season = document.querySelector('#season-filter');
  const cards = [...document.querySelectorAll('.product-card')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#empty-state');
  const update = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of cards) {
      const matchesText = card.textContent.toLocaleLowerCase().includes(query);
      const matchesCategory = category.value === 'all' || card.dataset.category === category.value;
      const matchesSeason = season.value === 'all' || card.dataset.season.split(' ').includes(season.value);
      const show = matchesText && matchesCategory && matchesSeason;
      card.hidden = !show;
      visible += Number(show);
    }
    count.textContent = `Showing ${visible} demo ${visible === 1 ? 'product idea' : 'product ideas'}`;
    empty.hidden = visible !== 0;
  };
  search.addEventListener('input', update);
  category.addEventListener('change', update);
  season.addEventListener('change', update);
  document.querySelector('#clear-filters').addEventListener('click', () => {
    search.value = '';
    category.value = 'all';
    season.value = 'all';
    update();
    search.focus();
  });
})();
