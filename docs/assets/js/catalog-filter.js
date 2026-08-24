(function () {
  var inputs = document.querySelectorAll("[data-catalog-filter]");
  for (var i = 0; i < inputs.length; i++) {
    bindFilter(inputs[i]);
  }

  function bindFilter(input) {
    var table = document.getElementById(input.getAttribute("data-catalog-filter"));
    var empty = document.getElementById(input.getAttribute("data-catalog-empty"));
    var visibleEl = document.getElementById(input.getAttribute("data-catalog-visible"));
    if (!input || !table) {
      return;
    }

    var rows = table.tBodies[0] ? table.tBodies[0].rows : [];

    function filterRows() {
      var query = input.value.trim().toLowerCase();
      var visible = 0;
      for (var r = 0; r < rows.length; r++) {
        var row = rows[r];
        var show = !query || (row.textContent || row.innerText || "").toLowerCase().indexOf(query) !== -1;
        row.hidden = !show;
        if (show) {
          visible += 1;
        }
      }
      if (visibleEl) {
        visibleEl.textContent = String(visible);
      }
      if (empty) {
        empty.hidden = visible !== 0;
      }
    }

    input.addEventListener("input", filterRows);
  }
})();
