// Client-side filter for lists using data attributes
document.addEventListener('DOMContentLoaded', function () {
  const inputs = document.querySelectorAll('[data-filter-input]');

  inputs.forEach(input => {
    const listSelector = input.dataset.listSelector || '.paper-list';

    function getItems() {
      const list = document.querySelector(listSelector);
      return list ? list.querySelectorAll('.filter-item') : [];
    }

    function applyFilter() {
      const q = input.value.trim().toLowerCase();
      const items = getItems();

      items.forEach(item => {
        const title = (item.dataset.title || '').toLowerCase();
        const author = (item.dataset.author || '').toLowerCase();
        const text = item.textContent.toLowerCase();
        const searchText = [title, author, text].join(' ');

        if (!q || searchText.includes(q)) {
          item.classList.remove('hidden');
        } else {
          item.classList.add('hidden');
        }
      });
    }

    input.addEventListener('input', applyFilter);
    // Initialize on page load
    applyFilter();
  });
});
