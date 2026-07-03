   // Reset graph to default RDF
   function resetGraph() {
    localStorage.removeItem('rdfGraph');
    rdfInputElem.value = defaultRDF;
    parseAndSetGraph(defaultRDF);
    renderGraph();
}


/**************************************************
 * 6. Adding nodes, editing labels, etc.
 **************************************************/
// 6a) Add new node at position (x, y)
function addNewNode(x, y) {
  const newId = 'http://example.org/newNode-' + Date.now();
  currentNodes.push({
    id: newId,
    literal: false,
    classUri: null,
    label: 'New Node',
    // set initial coords so it appears where we clicked
    x, y,
    fx: x, fy: y
  });
  renderGraph();
}

// 6b) Double-click => prompt for new label
function handleNodeEdit(d) {
  const newLabel = prompt('Enter new label:', d.label || '');
  if (newLabel !== null) {
    d.label = newLabel;
    renderGraph();
  }
}

/**************************************************
 * 7. Serialize graph -> Turtle -> put in <textarea>
 **************************************************/
function syncEditorWithGraph() {
  // Build an rdflib store from currentNodes/currentLinks
  const store = $rdf.graph();

  // 7a) For each node that isn't a "literal" node, add:
  //       subject rdf:type classUri   (if classUri)
  //       subject rdfs:label "..."    (if label)
  currentNodes.forEach(node => {
    if (!node.literal) {
      const subj = $rdf.sym(node.id);
      if (node.classUri) {
        store.add(
          subj,
          $rdf.sym(RDF_TYPE),
          $rdf.sym(node.classUri)
        );
      }
      if (node.label) {
        store.add(
          subj,
          $rdf.sym(RDFS_LABEL),
          $rdf.literal(node.label)
        );
      }
    }
  });

  // 7b) For each link, add the triple
  //   if the target is a literal node => parse "subj::pred::obj"
  //   otherwise => subject => object is a named node
  currentLinks.forEach(link => {
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;

    // If target is a "literal node ID" => parse it
    const isLiteralNode = currentNodes.find(n => n.id === targetId && n.literal);

    if (!isLiteralNode) {
      // Normal triple
      store.add(
        $rdf.sym(sourceId),
        $rdf.sym(link.predicate),
        $rdf.sym(targetId)
      );
    } else {
      // Parse the "subj::pred::obj" pattern
      // e.g. "http://example.org/Alice::http://example.org/name::AliceName"
      // We assume this is how we originally created the literal node ID
      const [subjFull, predFull, literalVal] = targetId.split('::');
      // But the real subject is sourceId, the real predicate is link.predicate
      // Actually, we want to re-inject the literal as the triple object
      // The "subjFull" might differ from sourceId if user rearranged things,
      // but let's stay consistent with the link's actual subject/predicate
      // We'll store (sourceId, link.predicate, literalVal)
      store.add(
        $rdf.sym(sourceId),
        $rdf.sym(link.predicate),
        $rdf.literal(isLiteralNode.value)
      );
    }
  });

  // 7c) Serialize to Turtle
  const turtle = new $rdf.Serializer(store).toN3(store);

  // 7d) Put into the <textarea>
  rdfInputElem.value = turtle;
}

/**************************************************
 * 8. Shorten URIs
 **************************************************/
function shortenUri(uri) {
  const parts = uri.split(/[\/#]/);
  return parts[parts.length - 1] || uri;
}

/**************************************************
 * 9. D3 Drag Behavior
 **************************************************/
function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event, d) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

/**************************************************
 * 10. UI: parse & render on "Re-Parse" button
 **************************************************/
updateButton.addEventListener('click', () => {
  parseAndSetGraph(rdfInputElem.value);
  renderGraph();
  saveGraphToStorage(); // alert("saved")
});

/**************************************************
 * 11. Initial load
 **************************************************/
parseAndSetGraph(rdfInputElem.value);
renderGraph();


/**************************************************
 * 12. Suggestions
 **************************************************/
function getSuggestions() {
    // Collect all node IDs, labels, and literal values
    const suggestions = currentNodes.map(node => {

        if(node.literal) {
            return node.value
        } else {
            return "<"+node.id+">"
            // const idParts = node.id.split(/[#/]/);
            // return ":"+idParts[idParts.length - 1];
        }

    });
    return suggestions;
}

const autocompleteDropdown = document.createElement('div');
autocompleteDropdown.classList.add('autocomplete-dropdown');
document.body.appendChild(autocompleteDropdown);

// Listen for input events on the textarea
rdfInputElem.addEventListener('input', (event) => {
const query = getCurrentWord(rdfInputElem);
if (query.length > 1) {
showSuggestions(query);
} else {
hideSuggestions();
}
});

// Hide the dropdown on blur
rdfInputElem.addEventListener('blur', hideSuggestions);

rdfInputElem.addEventListener('keydown', (event) => {
// if (autocompleteDropdown.style.display === 'block' && event.key === 'Enter') {
//     event.preventDefault(); // Prevent new line
//     const selectedItem = autocompleteDropdown.querySelector('.autocomplete-item.selected');
//     if (selectedItem) {
//         insertSuggestion(selectedItem.textContent);
//     }
// } 
 if (event.key === 'ArrowDown' || event.key === 'ArrowUp' || ( event.key === 'Enter' && event.shiftKey) || event.key === 'Escape') {
handleAutocompleteNavigation(event);
}
});

// function getSuggestions() {
//   // Collect node IDs, labels, and literal values for suggestions
//   return currentNodes.map(node => node.literal ? node.value : node.id);// (node.label || node.id));
// }

function getCurrentWord(textarea) {
const text = textarea.value;
const cursorPos = textarea.selectionStart;
const textBeforeCursor = text.substring(0, cursorPos);
const words = textBeforeCursor.split(/[\s<>"]+/);
return words.pop();
}

function showSuggestions(query) {
console.log(query);
const suggestions = getSuggestions().filter(suggestion => suggestion.toLowerCase().includes(query.toLowerCase()));
if (suggestions.length === 0) {
hideSuggestions();
return;
}

// Clear previous suggestions
autocompleteDropdown.innerHTML = '';
autocompleteDropdown.style.display = 'block';

// Position the dropdown at the cursor
const { left, top } = getCursorCoordinates(rdfInputElem);
autocompleteDropdown.style.left = `${left}px`;
autocompleteDropdown.style.top = `${top}px`;
autocompleteDropdown.style.width = `${rdfInputElem.offsetWidth}px`;

// Populate suggestions
suggestions.forEach(suggestion => {
const item = document.createElement('div');
item.classList.add('autocomplete-item');
item.textContent = suggestion;
item.addEventListener('mousedown', () => insertSuggestion(suggestion));
autocompleteDropdown.appendChild(item);
});
}

function hideSuggestions() {
autocompleteDropdown.style.display = 'none';
autocompleteDropdown.querySelectorAll('.autocomplete-item').forEach(item => item.remove());

}

function insertSuggestion(suggestion) {
const text = rdfInputElem.value;
const cursorPos = rdfInputElem.selectionStart;
const query = getCurrentWord(rdfInputElem);

// Replace the query with the selected suggestion
rdfInputElem.value = text.substring(0, cursorPos - query.length) + suggestion +" "+ text.substring(cursorPos);
// no newline after suggestion

rdfInputElem.focus(); 

hideSuggestions();
}

function handleAutocompleteNavigation(event) {
const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');
if (items.length === 0) return;
console.log(items)

let index = Array.from(items).findIndex(item => item.classList.contains('selected'));
if (event.key === 'ArrowDown') {
index = (index + 1) % items.length;
} else if (event.key === 'ArrowUp') {
index = (index - 1 + items.length) % items.length;
} else if (event.key === 'Enter') {
if (index >= 0) {
  insertSuggestion(items[index].textContent);
  // reset suggestions
}
return;
} else if (event.key === 'Escape') {
hideSuggestions();
return;
}

items.forEach(item => item.classList.remove('selected'));
if (index >= 0) {
items[index].classList.add('selected');
}
}

function getCursorCoordinates(textarea) {
const text = textarea.value.substring(0, textarea.selectionStart);
const div = document.createElement('div');
div.style.position = 'absolute';
div.style.whiteSpace = 'pre-wrap';
div.style.visibility = 'hidden';
div.style.font = getComputedStyle(textarea).font;
div.textContent = text.replace(/\n$/, '\n\u200b'); // Ensure newline spacing

const span = document.createElement('span');
span.textContent = '\u200b'; // Zero-width space to represent the cursor
div.appendChild(span);

document.body.appendChild(div);
const { offsetLeft, offsetTop } = textarea;
const { left, top } = span.getBoundingClientRect();
document.body.removeChild(div);

return {
left: left + window.scrollX - offsetLeft,
top: top + window.scrollY - offsetTop + textarea.scrollTop
};
}