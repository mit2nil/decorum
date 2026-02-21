(() => {
  const ROOM_NAMES = ["Bathroom", "Bedroom", "Living Room", "Kitchen"];
  const ROOM_ICONS = ["🚿", "🛏️", "🛋️", "🍳"];
  const COLORS = {
    Red: "#FF6B6B",
    Yellow: "#FFD93D",
    Blue: "#6BCBFF",
    Green: "#6BCB77",
  };
  const STYLES = {
    Modern: "◆",
    Antique: "❖",
    Retro: "◈",
    Unusual: "✦",
  };
  const OBJECT_TYPES = [
    { key: "lamp", label: "Lamp", emoji: "💡" },
    { key: "wallHanging", label: "Wall Hanging", emoji: "🖼️" },
    { key: "curio", label: "Curio", emoji: "🏺" },
  ];
  const VALID_OBJECTS = {
    lamp: { Modern: "Blue", Antique: "Yellow", Retro: "Red", Unusual: "Green" },
    wallHanging: { Modern: "Red", Antique: "Green", Retro: "Blue", Unusual: "Yellow" },
    curio: { Modern: "Green", Antique: "Blue", Retro: "Yellow", Unusual: "Red" },
  };
  const MAX_HEART_TO_HEART = 3;

  const setupScreen = document.getElementById("setup-screen");
  const gameScreen = document.getElementById("game-screen");
  const houseGrid = document.getElementById("house-grid");
  const controlPanel = document.getElementById("control-panel");
  const roundInfo = document.getElementById("round-info");
  const heartInfo = document.getElementById("heart-info");
  const turnIndicator = document.getElementById("turn-indicator");
  const selectionInfo = document.getElementById("selection-info");
  const modal = document.getElementById("modal");
  const modalContent = document.querySelector(".modal-content");
  const fileInput = document.getElementById("scenario-file");

  const state = {
    players: ["Player 1", "Player 2"],
    rooms: [],
    currentPlayer: 0,
    turnCount: 0,
    actionTaken: false,
    selectedRoom: null,
    selectedSlot: null,
    lastAction: null,
    lastReactions: [null, null],
    heartToHeartUsed: 0,
    playerConditions: [[], []],
  };

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function shuffle(values) {
    const copy = [...values];
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function typeByKey(slotKey) {
    return OBJECT_TYPES.find((t) => t.key === slotKey);
  }

  function roomByIndex(roomIdx) {
    return state.rooms[roomIdx];
  }

  function getSlot(room, slotKey) {
    return room[slotKey];
  }

  function setSlot(room, slotKey, obj) {
    room[slotKey] = obj;
  }

  function normalizeTypeKey(value) {
    const normalized = String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[_\s-]+/g, "");
    if (normalized === "lamp") return "lamp";
    if (normalized === "wallhanging" || normalized === "painting") return "wallHanging";
    if (normalized === "curio") return "curio";
    return null;
  }

  function parseStyle(value) {
    const target = String(value || "").trim().toLowerCase();
    return Object.keys(STYLES).find((style) => style.toLowerCase() === target) || null;
  }

  function parseColor(value) {
    const target = String(value || "").trim().toLowerCase();
    return Object.keys(COLORS).find((color) => color.toLowerCase() === target) || null;
  }

  function makeRoom(index) {
    return {
      name: ROOM_NAMES[index],
      icon: ROOM_ICONS[index],
      wallColor: Object.keys(COLORS)[index],
      lamp: null,
      wallHanging: null,
      curio: null,
    };
  }

  function initHouse() {
    state.rooms = ROOM_NAMES.map((_, idx) => makeRoom(idx));
  }

  function resetGameState() {
    initHouse();
    state.currentPlayer = 0;
    state.turnCount = 0;
    state.actionTaken = false;
    state.selectedRoom = null;
    state.selectedSlot = null;
    state.lastAction = null;
    state.lastReactions = [null, null];
    state.heartToHeartUsed = 0;
  }

  function setPlayerNamesFromSetup() {
    const p1 = document.getElementById("p1-name").value.trim();
    const p2 = document.getElementById("p2-name").value.trim();
    state.players = [p1 || "Player 1", p2 || "Player 2"];
  }

  function allObjects() {
    return state.rooms.flatMap((room) => OBJECT_TYPES.map((t) => room[t.key]).filter(Boolean));
  }

  function countByColor(color) {
    return allObjects().filter((obj) => obj.color === color).length;
  }

  function countByStyle(style) {
    return allObjects().filter((obj) => obj.style === style).length;
  }

  function roomHasColor(roomIdx, color) {
    const room = roomByIndex(roomIdx);
    return OBJECT_TYPES.some((t) => room[t.key] && room[t.key].color === color);
  }

  function roomHasType(roomIdx, slotKey) {
    return !!getSlot(roomByIndex(roomIdx), slotKey);
  }

  function conditionText(condition) {
    switch (condition.kind) {
      case "MinObjectsOfColor":
        return `At least ${condition.count} ${condition.color} object(s)`;
      case "MinObjectsOfStyle":
        return `At least ${condition.count} ${condition.style} object(s)`;
      case "NoObjectsOfColor":
        return `No ${condition.color} objects in house`;
      case "RoomHasColor":
        return `${ROOM_NAMES[condition.roomIdx]}: needs ${condition.color} object`;
      case "RoomWallColor":
        return `${ROOM_NAMES[condition.roomIdx]}: walls must be ${condition.color}`;
      case "RoomHasObjectType":
        return `${ROOM_NAMES[condition.roomIdx]}: needs a ${typeByKey(condition.slotKey).label}`;
      case "EveryRoomHasType":
        return `Every room needs a ${typeByKey(condition.slotKey).label}`;
      case "AllStylesPresent":
        return "All 4 styles must be present";
      default:
        return "Unknown condition";
    }
  }

  function isConditionMet(condition) {
    switch (condition.kind) {
      case "MinObjectsOfColor":
        return countByColor(condition.color) >= condition.count;
      case "MinObjectsOfStyle":
        return countByStyle(condition.style) >= condition.count;
      case "NoObjectsOfColor":
        return countByColor(condition.color) === 0;
      case "RoomHasColor":
        return roomHasColor(condition.roomIdx, condition.color);
      case "RoomWallColor":
        return roomByIndex(condition.roomIdx).wallColor === condition.color;
      case "RoomHasObjectType":
        return roomHasType(condition.roomIdx, condition.slotKey);
      case "EveryRoomHasType":
        return state.rooms.every((room) => !!room[condition.slotKey]);
      case "AllStylesPresent":
        return Object.keys(STYLES).every((style) => countByStyle(style) > 0);
      default:
        return false;
    }
  }

  function generateRandomConditions() {
    const pool = [];
    Object.keys(COLORS).forEach((color) => {
      pool.push({ kind: "MinObjectsOfColor", color, count: randomInt(1, 3) });
      pool.push({ kind: "NoObjectsOfColor", color });
    });
    Object.keys(STYLES).forEach((style) => {
      pool.push({ kind: "MinObjectsOfStyle", style, count: randomInt(1, 2) });
    });
    ROOM_NAMES.forEach((_, roomIdx) => {
      Object.keys(COLORS).forEach((color) => {
        pool.push({ kind: "RoomHasColor", roomIdx, color });
        pool.push({ kind: "RoomWallColor", roomIdx, color });
      });
      OBJECT_TYPES.forEach((type) => {
        pool.push({ kind: "RoomHasObjectType", roomIdx, slotKey: type.key });
      });
    });
    OBJECT_TYPES.forEach((type) => pool.push({ kind: "EveryRoomHasType", slotKey: type.key }));
    pool.push({ kind: "AllStylesPresent" });
    const shuffled = shuffle(pool);
    return [shuffled.slice(0, 3), shuffled.slice(3, 6)];
  }

  function parseConditionText(text) {
    const raw = String(text || "").trim();
    if (!raw) return null;
    const lower = raw.toLowerCase();

    const roomMap = Object.fromEntries(ROOM_NAMES.map((name, idx) => [name.toLowerCase(), idx]));
    const colorMap = Object.fromEntries(Object.keys(COLORS).map((color) => [color.toLowerCase(), color]));
    const styleMap = Object.fromEntries(Object.keys(STYLES).map((style) => [style.toLowerCase(), style]));
    const typeMap = {
      lamp: "lamp",
      "wall hanging": "wallHanging",
      wall_hanging: "wallHanging",
      curio: "curio",
    };

    let match = lower.match(/at least\s+(\d+)\s+(\w+)\s+object/);
    if (match) {
      const count = Number(match[1]);
      const target = match[2];
      if (colorMap[target]) return { kind: "MinObjectsOfColor", color: colorMap[target], count };
      if (styleMap[target]) return { kind: "MinObjectsOfStyle", style: styleMap[target], count };
    }

    match = lower.match(/no\s+(\w+)\s+objects?\s+in\s+house/);
    if (match && colorMap[match[1]]) {
      return { kind: "NoObjectsOfColor", color: colorMap[match[1]] };
    }

    for (const [roomName, roomIdx] of Object.entries(roomMap)) {
      if (!lower.includes(roomName)) continue;
      for (const [colorLower, color] of Object.entries(colorMap)) {
        if (lower.includes(`must have a ${colorLower} object`)) {
          return { kind: "RoomHasColor", roomIdx, color };
        }
        if (lower.includes(`walls must be ${colorLower}`)) {
          return { kind: "RoomWallColor", roomIdx, color };
        }
      }
      for (const [typeName, slotKey] of Object.entries(typeMap)) {
        if (lower.includes(`must have a ${typeName}`)) {
          return { kind: "RoomHasObjectType", roomIdx, slotKey };
        }
      }
    }

    for (const [typeName, slotKey] of Object.entries(typeMap)) {
      if (lower.includes(`every room must have a ${typeName}`)) {
        return { kind: "EveryRoomHasType", slotKey };
      }
    }

    if (lower.includes("all 4 styles must be present")) {
      return { kind: "AllStylesPresent" };
    }

    return null;
  }

  function showGameScreen() {
    setupScreen.classList.add("hidden");
    gameScreen.classList.remove("hidden");
    renderAll();
  }

  function renderAll() {
    renderHeader();
    renderSelectionInfo();
    renderHouse();
    renderControls();
  }

  function renderHeader() {
    const round = Math.floor(state.turnCount / 2) + 1;
    roundInfo.textContent = `⏱ Round ${round} (Actions taken: ${state.turnCount})`;
    heartInfo.textContent = `Heart-to-Heart: ${"❤️".repeat(MAX_HEART_TO_HEART - state.heartToHeartUsed)}${"🤍".repeat(state.heartToHeartUsed)}`;
    const active = state.currentPlayer === 0 ? `🔴 ${state.players[0]}` : `🔵 ${state.players[1]}`;
    turnIndicator.textContent = `${active}'s Turn`;
    turnIndicator.style.background = state.currentPlayer === 0 ? "#ff8a80" : "#64b5f6";
  }

  function renderSelectionInfo() {
    if (state.selectedRoom == null) {
      selectionInfo.textContent = "Click a room or object slot to select it";
      return;
    }
    const room = roomByIndex(state.selectedRoom);
    let text = `${room.icon} ${room.name} • Walls: ${room.wallColor}`;
    if (state.selectedSlot) {
      const obj = getSlot(room, state.selectedSlot);
      const type = typeByKey(state.selectedSlot);
      text += ` • ${type.emoji} ${type.label}`;
      if (obj) text += ` (${obj.style} ${obj.color})`;
    }
    selectionInfo.textContent = text;
  }

  function renderHouse() {
    houseGrid.innerHTML = "";
    state.rooms.forEach((room, roomIdx) => {
      const card = document.createElement("div");
      card.className = "room-card" + (state.selectedRoom === roomIdx ? " selected" : "");
      card.style.borderColor = COLORS[room.wallColor];
      card.addEventListener("click", () => {
        if (state.actionTaken) return;
        state.selectedRoom = state.selectedRoom === roomIdx ? null : roomIdx;
        state.selectedSlot = null;
        renderAll();
      });

      const header = document.createElement("div");
      header.className = "room-header";
      header.style.background = COLORS[room.wallColor];
      header.innerHTML = `<span>${room.icon} ${room.name}</span><span>● ${room.wallColor}</span>`;

      const body = document.createElement("div");
      body.className = "room-body";
      body.appendChild(createSlotRow(roomIdx, "wallHanging"));
      body.appendChild(createSlotRow(roomIdx, "lamp"));
      body.appendChild(createSlotRow(roomIdx, "curio"));

      card.appendChild(header);
      card.appendChild(body);
      houseGrid.appendChild(card);
    });
  }

  function createSlotRow(roomIdx, slotKey) {
    const room = roomByIndex(roomIdx);
    const obj = getSlot(room, slotKey);
    const type = typeByKey(slotKey);

    const row = document.createElement("button");
    row.type = "button";
    row.className = "slot-row";
    if (state.selectedRoom === roomIdx && state.selectedSlot === slotKey) row.classList.add("selected");
    if (!obj) row.classList.add("empty");
    row.title = obj
      ? `${type.label}\n${obj.style} ${obj.color}`
      : `Empty ${type.label} slot`;

    const typeEl = document.createElement("span");
    typeEl.className = "slot-type";
    typeEl.textContent = `${type.emoji} ${type.label}`;

    const tile = document.createElement("span");
    tile.className = "slot-visual";
    if (obj) {
      tile.style.background = COLORS[obj.color];
      tile.style.color = "#fff";
      tile.textContent = STYLES[obj.style];
    } else {
      tile.classList.add("empty");
      tile.textContent = "+";
    }

    const meta = document.createElement("span");
    meta.className = "slot-meta";
    meta.textContent = obj ? `${obj.style} • ${obj.color}` : "Empty";

    row.appendChild(typeEl);
    row.appendChild(tile);
    row.appendChild(meta);

    row.addEventListener("click", (event) => {
      event.stopPropagation();
      if (state.actionTaken) return;
      state.selectedRoom = roomIdx;
      state.selectedSlot = slotKey;
      if (obj) {
        openSlotOptions(roomIdx, slotKey);
      } else {
        openObjectPicker(slotKey, (newObj) => doSetSlot(roomIdx, slotKey, newObj));
      }
      renderAll();
    });

    return row;
  }

  function button(label, className, onClick, disabled = false) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = className;
    btn.textContent = label;
    btn.disabled = disabled;
    btn.addEventListener("click", onClick);
    return btn;
  }

  function renderControls() {
    controlPanel.innerHTML = "";

    const selectedRoom = state.selectedRoom == null ? null : roomByIndex(state.selectedRoom);

    const selectCard = document.createElement("section");
    selectCard.className = "control-section";
    if (!selectedRoom) {
      selectCard.innerHTML = `<h3>Selection</h3><p>Click a room/slot to select.</p>`;
    } else {
      let selectedText = "";
      if (state.selectedSlot) {
        const type = typeByKey(state.selectedSlot);
        const obj = getSlot(selectedRoom, state.selectedSlot);
        selectedText = obj
          ? `${type.emoji} ${type.label} • ${obj.style} ${obj.color}`
          : `${type.emoji} ${type.label} • Empty`;
      }
      selectCard.innerHTML = `<h3>${selectedRoom.icon} ${selectedRoom.name}</h3><p>🎨 Walls: ${selectedRoom.wallColor}</p>${selectedText ? `<p>${selectedText}</p>` : ""}`;
    }

    const turnCard = document.createElement("section");
    turnCard.className = "control-section turn-actions";

    const endTurnBtn = button(
      state.actionTaken ? "⏭ End Turn (Done)" : "⏭ End Turn",
      "btn primary",
      endTurn,
      false
    );
    turnCard.appendChild(endTurnBtn);

    if (state.actionTaken && state.lastAction) {
      const undoBtn = button("↩ Undo Last Action", "btn rose", undoLastAction, false);
      turnCard.appendChild(undoBtn);
    }

    const actionsCard = document.createElement("section");
    actionsCard.className = "control-section";
    actionsCard.innerHTML = `<h3>Actions (pick 1)</h3>`;
    const actionsGrid = document.createElement("div");
    actionsGrid.className = "action-grid";

    actionsGrid.appendChild(button("➕ Add", "action-btn", actionAdd, state.actionTaken));
    actionsGrid.appendChild(button("➖ Remove", "action-btn", actionRemove, state.actionTaken));
    actionsGrid.appendChild(button("🔄 Swap", "action-btn", actionSwap, state.actionTaken));
    actionsGrid.appendChild(button("🎨 Paint", "action-btn", actionPaint, state.actionTaken));
    actionsCard.appendChild(actionsGrid);

    const gameCard = document.createElement("section");
    gameCard.className = "control-section";
    gameCard.innerHTML = `<h3>Game</h3>`;
    const gameButtons = document.createElement("div");
    gameButtons.className = "stack-buttons";
    gameButtons.appendChild(button("👁️ My Conditions", "action-btn", () => showConditionsDialog(state.currentPlayer, "My Conditions")));
    gameButtons.appendChild(button("✓ Check Conditions", "action-btn", checkCurrentPlayerConditions));
    gameButtons.appendChild(button("💕 Heart-to-Heart", "action-btn", useHeartToHeart));
    gameCard.appendChild(gameButtons);

    const reactionCard = document.createElement("section");
    reactionCard.className = "control-section";
    reactionCard.innerHTML = `<h3>Reactions</h3>`;
    const reactionRow = document.createElement("div");
    reactionRow.className = "reaction-row";

    ["😊", "😐", "😠"].forEach((emoji) => {
      const btn = button(emoji, "reaction-btn", () => {
        state.lastReactions[state.currentPlayer] = emoji;
        renderControls();
      }, !state.actionTaken);
      reactionRow.appendChild(btn);
    });
    reactionCard.appendChild(reactionRow);

    const partnerReaction = state.lastReactions[1 - state.currentPlayer];
    const reactionText = document.createElement("p");
    reactionText.className = "reaction-status";
    reactionText.textContent = partnerReaction ? `Partner reaction: ${partnerReaction}` : "Partner reaction: —";
    reactionCard.appendChild(reactionText);

    controlPanel.appendChild(selectCard);
    controlPanel.appendChild(turnCard);
    controlPanel.appendChild(actionsCard);
    controlPanel.appendChild(gameCard);
    controlPanel.appendChild(reactionCard);
  }

  function ensureSelectedSlot(requireFilled = null) {
    if (state.selectedRoom == null || !state.selectedSlot) {
      showToast("Select a room slot first.");
      return null;
    }
    const room = roomByIndex(state.selectedRoom);
    const obj = getSlot(room, state.selectedSlot);
    if (requireFilled === true && !obj) {
      showToast("That slot is empty.");
      return null;
    }
    if (requireFilled === false && obj) {
      showToast("That slot already has an object.");
      return null;
    }
    return { room, obj };
  }

  function doSetSlot(roomIdx, slotKey, obj) {
    const room = roomByIndex(roomIdx);
    const prev = clone(getSlot(room, slotKey));
    setSlot(room, slotKey, obj);
    state.lastAction = { kind: "setSlot", roomIdx, slotKey, prev };
    state.actionTaken = true;
    state.selectedRoom = null;
    state.selectedSlot = null;
    renderAll();
  }

  function actionAdd() {
    const selected = ensureSelectedSlot(false);
    if (!selected) return;
    openObjectPicker(state.selectedSlot, (obj) => doSetSlot(state.selectedRoom, state.selectedSlot, obj));
  }

  function actionRemove() {
    const selected = ensureSelectedSlot(true);
    if (!selected) return;
    doSetSlot(state.selectedRoom, state.selectedSlot, null);
  }

  function actionSwap() {
    const selected = ensureSelectedSlot(true);
    if (!selected) return;
    openObjectPicker(state.selectedSlot, (obj) => doSetSlot(state.selectedRoom, state.selectedSlot, obj));
  }

  function actionPaint() {
    if (state.selectedRoom == null) {
      showToast("Select a room first.");
      return;
    }
    openPaintDialog();
  }

  function endTurn() {
    state.currentPlayer = 1 - state.currentPlayer;
    state.turnCount += 1;
    state.actionTaken = false;
    state.lastAction = null;
    state.selectedRoom = null;
    state.selectedSlot = null;
    renderAll();
  }

  function undoLastAction() {
    if (!state.lastAction) return;
    const action = state.lastAction;
    if (action.kind === "paint") {
      state.rooms[action.roomIdx].wallColor = action.prev;
    } else if (action.kind === "setSlot") {
      setSlot(state.rooms[action.roomIdx], action.slotKey, action.prev || null);
    }
    state.lastAction = null;
    state.actionTaken = false;
    renderAll();
  }

  function openPaintDialog() {
    const roomIdx = state.selectedRoom;
    const room = roomByIndex(roomIdx);
    modalContent.innerHTML = "";

    const title = document.createElement("h3");
    title.textContent = `Paint ${room.name}`;
    modalContent.appendChild(title);

    const grid = document.createElement("div");
    grid.className = "color-grid";
    Object.keys(COLORS).forEach((color) => {
      const swatch = button(color, "color-btn", () => {
        const prev = room.wallColor;
        room.wallColor = color;
        state.lastAction = { kind: "paint", roomIdx, prev };
        state.actionTaken = true;
        state.selectedRoom = null;
        state.selectedSlot = null;
        closeModal();
        renderAll();
      });
      swatch.style.background = COLORS[color];
      swatch.style.color = "#fff";
      grid.appendChild(swatch);
    });

    modalContent.appendChild(grid);
    modalContent.appendChild(button("Cancel", "btn", closeModal));
    openModal();
  }

  function openObjectPicker(slotKey, onPick) {
    modalContent.innerHTML = "";
    const type = typeByKey(slotKey);

    const title = document.createElement("h3");
    title.textContent = `${type.emoji} Select ${type.label}`;
    modalContent.appendChild(title);

    const options = document.createElement("div");
    options.className = "picker-grid";

    Object.keys(STYLES).forEach((style) => {
      const color = VALID_OBJECTS[slotKey][style];
      const card = document.createElement("button");
      card.type = "button";
      card.className = "picker-card";
      card.style.background = COLORS[color];
      card.innerHTML = `<strong>${STYLES[style]}</strong><span>${style} ${color}</span>`;
      card.addEventListener("click", () => {
        onPick({ type: slotKey, style, color });
        closeModal();
      });
      options.appendChild(card);
    });

    modalContent.appendChild(options);
    modalContent.appendChild(button("Cancel", "btn", closeModal));
    openModal();
  }

  function openSlotOptions(roomIdx, slotKey) {
    const room = roomByIndex(roomIdx);
    const obj = getSlot(room, slotKey);
    if (!obj) return;

    modalContent.innerHTML = "";
    const type = typeByKey(slotKey);

    const title = document.createElement("h3");
    title.textContent = `${type.emoji} ${type.label}`;
    modalContent.appendChild(title);

    const summary = document.createElement("p");
    summary.textContent = `${obj.style} ${obj.color}`;
    modalContent.appendChild(summary);

    modalContent.appendChild(button("Swap with Different Object", "btn lavender", () => {
      closeModal();
      openObjectPicker(slotKey, (newObj) => doSetSlot(roomIdx, slotKey, newObj));
    }));

    modalContent.appendChild(button("Remove Object", "btn peach", () => {
      closeModal();
      doSetSlot(roomIdx, slotKey, null);
    }));

    modalContent.appendChild(button("Cancel", "btn", closeModal));
    openModal();
  }

  function showConditionsDialog(playerIdx, titleText) {
    const conditions = state.playerConditions[playerIdx] || [];
    const color = playerIdx === 0 ? "#ff8a80" : "#64b5f6";

    modalContent.innerHTML = "";
    const title = document.createElement("h3");
    title.textContent = `${playerIdx === 0 ? "🔴" : "🔵"} ${state.players[playerIdx]} — ${titleText}`;
    title.style.color = color;
    modalContent.appendChild(title);

    if (!conditions.length) {
      const p = document.createElement("p");
      p.textContent = "No conditions set.";
      modalContent.appendChild(p);
    } else {
      conditions.forEach((condition) => {
        const met = isConditionMet(condition);
        const row = document.createElement("div");
        row.className = "condition-row";
        row.textContent = `${met ? "✅" : "❌"} ${conditionText(condition)}`;
        row.style.color = met ? "#2e7d32" : "#c62828";
        modalContent.appendChild(row);
      });
    }

    modalContent.appendChild(button("Close", "btn", closeModal));
    openModal();
  }

  function checkCurrentPlayerConditions() {
    const playerIdx = state.currentPlayer;
    const conditions = state.playerConditions[playerIdx] || [];
    const met = conditions.filter((condition) => isConditionMet(condition)).length;

    modalContent.innerHTML = "";
    const title = document.createElement("h3");
    title.textContent = "Condition Check";
    modalContent.appendChild(title);

    const summary = document.createElement("p");
    summary.textContent = conditions.length
      ? `${state.players[playerIdx]}: ${met}/${conditions.length} conditions met`
      : `${state.players[playerIdx]} has no conditions set.`;
    modalContent.appendChild(summary);

    conditions.forEach((condition) => {
      const row = document.createElement("div");
      const ok = isConditionMet(condition);
      row.className = "condition-row";
      row.textContent = `${ok ? "✅" : "❌"} ${conditionText(condition)}`;
      row.style.color = ok ? "#2e7d32" : "#c62828";
      modalContent.appendChild(row);
    });

    modalContent.appendChild(button("Close", "btn", closeModal));
    openModal();
  }

  function useHeartToHeart() {
    if (state.heartToHeartUsed >= MAX_HEART_TO_HEART) {
      showToast("No Heart-to-Hearts left.");
      return;
    }
    state.heartToHeartUsed += 1;
    modalContent.innerHTML = "";
    const title = document.createElement("h3");
    title.textContent = "💕 Heart-to-Heart";
    modalContent.appendChild(title);
    const msg = document.createElement("p");
    const remaining = MAX_HEART_TO_HEART - state.heartToHeartUsed;
    msg.textContent = `Open discussion allowed. Remaining after this: ${remaining}`;
    modalContent.appendChild(msg);
    modalContent.appendChild(button("Close", "btn", () => {
      closeModal();
      renderHeader();
    }));
    openModal();
    renderHeader();
  }

  function showToast(message) {
    modalContent.innerHTML = "";
    const p = document.createElement("p");
    p.textContent = message;
    modalContent.appendChild(p);
    modalContent.appendChild(button("OK", "btn", closeModal));
    openModal();
  }

  function openCustomSetupDialog() {
    const draft = {
      conditions: [[], []],
      walls: state.rooms.map((room) => room.wallColor),
      slots: state.rooms.map(() => ({ lamp: null, wallHanging: null, curio: null })),
    };

    modalContent.innerHTML = "";
    const title = document.createElement("h3");
    title.textContent = "Guided Custom Setup";
    modalContent.appendChild(title);

    const wrapper = document.createElement("div");
    wrapper.className = "custom-setup";

    const playersSection = document.createElement("div");
    playersSection.className = "custom-players";

    [0, 1].forEach((playerIdx) => {
      const card = document.createElement("div");
      card.className = "setup-card";

      const heading = document.createElement("h4");
      heading.textContent = `${playerIdx === 0 ? "🔴" : "🔵"} ${state.players[playerIdx]} Conditions`;
      card.appendChild(heading);

      const list = document.createElement("div");
      list.className = "condition-list";
      card.appendChild(list);

      const redraw = () => {
        list.innerHTML = "";
        draft.conditions[playerIdx].forEach((condition, idx) => {
          const chip = document.createElement("div");
          chip.className = "condition-chip";
          chip.innerHTML = `<span>${conditionText(condition)}</span>`;
          const remove = document.createElement("button");
          remove.type = "button";
          remove.textContent = "✕";
          remove.addEventListener("click", () => {
            draft.conditions[playerIdx].splice(idx, 1);
            redraw();
          });
          chip.appendChild(remove);
          list.appendChild(chip);
        });
      };

      const controls = document.createElement("div");
      controls.className = "builder-grid";

      const roomSelect = selectFrom(ROOM_NAMES);
      const colorSelect = selectFrom(Object.keys(COLORS));
      const typeSelect = selectFrom(OBJECT_TYPES.map((t) => t.label));
      const styleSelect = selectFrom(Object.keys(STYLES));
      const countColor = selectFrom(["1", "2", "3"]);
      const countStyle = selectFrom(["1", "2"]);

      controls.appendChild(builderRow("Room has color", [roomSelect, colorSelect], () => {
        draft.conditions[playerIdx].push({
          kind: "RoomHasColor",
          roomIdx: ROOM_NAMES.indexOf(roomSelect.value),
          color: colorSelect.value,
        });
        redraw();
      }));

      controls.appendChild(builderRow("Room walls color", [roomSelect.cloneNode(true), colorSelect.cloneNode(true)], (elements) => {
        draft.conditions[playerIdx].push({
          kind: "RoomWallColor",
          roomIdx: ROOM_NAMES.indexOf(elements[0].value),
          color: elements[1].value,
        });
        redraw();
      }));

      controls.appendChild(builderRow("Room has type", [roomSelect.cloneNode(true), typeSelect], (elements) => {
        draft.conditions[playerIdx].push({
          kind: "RoomHasObjectType",
          roomIdx: ROOM_NAMES.indexOf(elements[0].value),
          slotKey: normalizeTypeKey(elements[1].value),
        });
        redraw();
      }));

      controls.appendChild(builderRow("At least N color", [countColor, colorSelect.cloneNode(true)], (elements) => {
        draft.conditions[playerIdx].push({
          kind: "MinObjectsOfColor",
          count: Number(elements[0].value),
          color: elements[1].value,
        });
        redraw();
      }));

      controls.appendChild(builderRow("At least N style", [countStyle, styleSelect], (elements) => {
        draft.conditions[playerIdx].push({
          kind: "MinObjectsOfStyle",
          count: Number(elements[0].value),
          style: elements[1].value,
        });
        redraw();
      }));

      controls.appendChild(builderRow("No color in house", [colorSelect.cloneNode(true)], (elements) => {
        draft.conditions[playerIdx].push({ kind: "NoObjectsOfColor", color: elements[0].value });
        redraw();
      }));

      controls.appendChild(builderRow("Every room has type", [typeSelect.cloneNode(true)], (elements) => {
        draft.conditions[playerIdx].push({ kind: "EveryRoomHasType", slotKey: normalizeTypeKey(elements[0].value) });
        redraw();
      }));

      const allStylesRow = document.createElement("div");
      allStylesRow.className = "builder-row";
      const allStylesBtn = button("Add: All styles present", "action-btn", () => {
        draft.conditions[playerIdx].push({ kind: "AllStylesPresent" });
        redraw();
      });
      allStylesBtn.style.width = "100%";
      allStylesRow.appendChild(allStylesBtn);
      controls.appendChild(allStylesRow);

      const utilityRow = document.createElement("div");
      utilityRow.className = "builder-row";
      utilityRow.appendChild(button("Clear", "action-btn", () => {
        draft.conditions[playerIdx] = [];
        redraw();
      }));
      utilityRow.appendChild(button("Add 3 Random", "action-btn", () => {
        draft.conditions[playerIdx].push(...generateRandomConditions()[playerIdx]);
        redraw();
      }));
      controls.appendChild(utilityRow);

      card.appendChild(controls);
      playersSection.appendChild(card);
      redraw();
    });

    const setupSection = document.createElement("div");
    setupSection.className = "setup-card";
    setupSection.innerHTML = `<h4>🏠 Starting House Setup</h4>`;

    const setupTable = document.createElement("table");
    setupTable.className = "setup-table";
    const headerRow = document.createElement("tr");
    headerRow.innerHTML = "<th>Room</th><th>Wall</th><th>Lamp</th><th>Wall Hanging</th><th>Curio</th>";
    setupTable.appendChild(headerRow);

    ROOM_NAMES.forEach((roomName, roomIdx) => {
      const row = document.createElement("tr");
      const wallSelect = selectFrom(Object.keys(COLORS), draft.walls[roomIdx]);
      wallSelect.addEventListener("change", () => {
        draft.walls[roomIdx] = wallSelect.value;
      });

      row.innerHTML = `<td>${ROOM_ICONS[roomIdx]} ${roomName}</td>`;
      const wallCell = document.createElement("td");
      wallCell.appendChild(wallSelect);
      row.appendChild(wallCell);

      ["lamp", "wallHanging", "curio"].forEach((slotKey) => {
        const options = ["Empty", ...Object.keys(STYLES)];
        const select = selectFrom(options, "Empty");
        select.addEventListener("change", () => {
          draft.slots[roomIdx][slotKey] = select.value === "Empty" ? null : select.value;
        });
        const cell = document.createElement("td");
        cell.appendChild(select);
        row.appendChild(cell);
      });

      setupTable.appendChild(row);
    });

    setupSection.appendChild(setupTable);

    wrapper.appendChild(playersSection);
    wrapper.appendChild(setupSection);
    modalContent.appendChild(wrapper);

    const actions = document.createElement("div");
    actions.className = "button-row";
    actions.appendChild(button("Start Game", "btn primary", () => {
      if (!draft.conditions[0].length || !draft.conditions[1].length) {
        window.alert("Please add at least one condition for each player.");
        return;
      }

      resetGameState();
      setPlayerNamesFromSetup();
      state.playerConditions = [clone(draft.conditions[0]), clone(draft.conditions[1])];

      state.rooms.forEach((room, roomIdx) => {
        room.wallColor = draft.walls[roomIdx];
        OBJECT_TYPES.forEach((type) => {
          const style = draft.slots[roomIdx][type.key];
          if (!style) {
            room[type.key] = null;
            return;
          }
          room[type.key] = {
            type: type.key,
            style,
            color: VALID_OBJECTS[type.key][style],
          };
        });
      });

      closeModal();
      showGameScreen();
    }));

    actions.appendChild(button("Cancel", "btn", closeModal));
    modalContent.appendChild(actions);

    openModal();
  }

  function selectFrom(values, selected = null) {
    const select = document.createElement("select");
    values.forEach((value) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = value;
      if (selected != null && value === selected) opt.selected = true;
      select.appendChild(opt);
    });
    return select;
  }

  function builderRow(labelText, inputs, onAdd) {
    const row = document.createElement("div");
    row.className = "builder-row";

    const label = document.createElement("span");
    label.className = "builder-label";
    label.textContent = labelText;
    row.appendChild(label);

    inputs.forEach((input) => row.appendChild(input));

    const addBtn = button("Add", "action-btn", () => onAdd(inputs));
    row.appendChild(addBtn);
    return row;
  }

  async function loadScenarioFromFile(file) {
    try {
      const text = await file.text();
      const data = JSON.parse(text);

      resetGameState();
      setPlayerNamesFromSetup();

      const p1 = [];
      const p2 = [];
      const skipped = [];

      (data.player1_conditions || []).forEach((line) => {
        const condition = parseConditionText(line);
        if (condition) p1.push(condition); else skipped.push(line);
      });
      (data.player2_conditions || []).forEach((line) => {
        const condition = parseConditionText(line);
        if (condition) p2.push(condition); else skipped.push(line);
      });

      state.playerConditions = [p1, p2];

      if (data.wall_colors && Array.isArray(data.wall_colors)) {
        data.wall_colors.forEach((color, roomIdx) => {
          const valid = parseColor(color);
          if (valid && state.rooms[roomIdx]) state.rooms[roomIdx].wallColor = valid;
        });
      }

      if (data.starting_walls && typeof data.starting_walls === "object") {
        Object.entries(data.starting_walls).forEach(([key, value]) => {
          const color = parseColor(value);
          if (!color) return;
          const idx = Number.isInteger(Number(key)) ? Number(key) : ROOM_NAMES.findIndex((name) => name.toLowerCase() === String(key).toLowerCase());
          if (idx >= 0 && idx < state.rooms.length) state.rooms[idx].wallColor = color;
        });
      }

      (data.starting_objects || []).forEach((entry) => {
        const roomIdx = Number(entry.room);
        const slotKey = normalizeTypeKey(entry.type);
        if (!Number.isInteger(roomIdx) || roomIdx < 0 || roomIdx >= state.rooms.length || !slotKey) return;

        let style = parseStyle(entry.style);
        let color = parseColor(entry.color);

        if (!style && color) {
          style = Object.keys(VALID_OBJECTS[slotKey]).find((s) => VALID_OBJECTS[slotKey][s] === color) || null;
        }
        if (!color && style) {
          color = VALID_OBJECTS[slotKey][style];
        }
        if (!style || !color) return;
        if (VALID_OBJECTS[slotKey][style] !== color) return;

        state.rooms[roomIdx][slotKey] = { type: slotKey, style, color };
      });

      showGameScreen();

      if (skipped.length) {
        showToast(`Loaded with ${skipped.length} unparsed condition(s).`);
      }
    } catch (error) {
      showToast(`Failed to load scenario: ${error.message}`);
    }
  }

  function openModal() {
    modal.classList.remove("hidden");
  }

  function closeModal() {
    modal.classList.add("hidden");
    modalContent.innerHTML = "";
  }

  function startRandomGame() {
    resetGameState();
    setPlayerNamesFromSetup();
    state.playerConditions = generateRandomConditions();
    showGameScreen();
  }

  function startCustomGame() {
    resetGameState();
    setPlayerNamesFromSetup();
    openCustomSetupDialog();
  }

  document.getElementById("btn-random").addEventListener("click", startRandomGame);
  document.getElementById("btn-custom").addEventListener("click", startCustomGame);
  document.getElementById("btn-file").addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", async () => {
    if (!fileInput.files || !fileInput.files.length) return;
    await loadScenarioFromFile(fileInput.files[0]);
    fileInput.value = "";
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeModal();
  });

  resetGameState();
})();
