const MISTAKES_ALLOWED = 4;

let mistakes = 0;
let solvedGroups = new Set();
let selectedTiles = [];
let messageTimer = null;

const gridEl = document.getElementById("grid");
const submitBtn = document.getElementById("submit-btn");
const mistakesEl = document.getElementById("mistakes");
const messageEl = document.getElementById("message");

function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

function showMessage(text, { transient = false } = {}) {
  messageEl.textContent = text;
  if (messageTimer) clearTimeout(messageTimer);
  if (transient) {
    messageTimer = setTimeout(() => {
      messageEl.textContent = "";
    }, 2000);
  }
}

function buildTiles() {
  const tiles = [];
  PUZZLE.groups.forEach((group, groupIndex) => {
    group.members.forEach((value) => tiles.push({ value, groupIndex }));
  });
  shuffle(tiles);

  tiles.forEach((tile) => {
    const btn = document.createElement("button");
    btn.className = "tile";
    btn.textContent = tile.value;
    btn.dataset.group = tile.groupIndex;
    btn.addEventListener("click", () => onTileClick(btn));
    gridEl.appendChild(btn);
  });
}

function onTileClick(tile) {
  if (tile.classList.contains("solved")) return;

  if (selectedTiles.includes(tile)) {
    tile.classList.remove("selected");
    selectedTiles = selectedTiles.filter((t) => t !== tile);
  } else if (selectedTiles.length < 4) {
    tile.classList.add("selected");
    selectedTiles.push(tile);
  }

  submitBtn.disabled = selectedTiles.length !== 4;
}

function clearSelection() {
  selectedTiles.forEach((t) => t.classList.remove("selected"));
  selectedTiles = [];
  submitBtn.disabled = true;
}

function buildSolvedRow(groupIndex, { revealed = false } = {}) {
  const group = PUZZLE.groups[groupIndex];
  const members = [...group.members].sort((a, b) => a - b);

  const row = document.createElement("button");
  row.className = "tile solved-row";
  row.classList.add(revealed ? "revealed" : "solved");
  row.disabled = true;
  row.textContent = `${group.label}\n${members.join(", ")}`;
  return row;
}

function insertSolvedRow(groupIndex, options) {
  const row = buildSolvedRow(groupIndex, options);
  const firstUnsolvedTile = Array.from(gridEl.children).find(
    (el) => !el.classList.contains("solved-row")
  );
  if (firstUnsolvedTile) {
    gridEl.insertBefore(row, firstUnsolvedTile);
  } else {
    gridEl.appendChild(row);
  }
}

function endGame() {
  submitBtn.disabled = true;
  document.querySelectorAll(".tile").forEach((t) => {
    t.disabled = true;
  });
}

function revealRemainingGroups() {
  for (let g = 0; g < PUZZLE.groups.length; g++) {
    if (solvedGroups.has(g)) continue;
    document.querySelectorAll(`.tile[data-group="${g}"]`).forEach((t) => t.remove());
    insertSolvedRow(g, { revealed: true });
  }
}

function onSubmit() {
  const groupCounts = {};
  selectedTiles.forEach((tile) => {
    const g = tile.dataset.group;
    groupCounts[g] = (groupCounts[g] || 0) + 1;
  });
  const [bestGroup, bestCount] = Object.entries(groupCounts).sort((a, b) => b[1] - a[1])[0];

  if (bestCount === 4) {
    const groupIndex = Number(bestGroup);
    selectedTiles.forEach((tile) => tile.remove());
    solvedGroups.add(groupIndex);
    insertSolvedRow(groupIndex);
    selectedTiles = [];
    submitBtn.disabled = true;

    if (solvedGroups.size === PUZZLE.groups.length) {
      showMessage("You win!");
      endGame();
    }
    return;
  }

  mistakes++;
  mistakesEl.textContent = `Mistakes: ${mistakes}/${MISTAKES_ALLOWED}`;

  if (bestCount === 3) {
    showMessage("One away...", { transient: true });
  } else {
    showMessage("Not a match", { transient: true });
  }

  if (mistakes >= MISTAKES_ALLOWED) {
    showMessage("Out of guesses — here are the remaining groups.");
    revealRemainingGroups();
    endGame();
  }
}

buildTiles();
submitBtn.addEventListener("click", onSubmit);
