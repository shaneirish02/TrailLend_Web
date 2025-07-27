window.modalEnabled = false;

let currentDate = new Date();
const blockedDates = {};
const savedTimeSlots = {};

function renderCalendar() {
  const monthYear = document.getElementById("calendar-month-year");
  const calendarBody = document.getElementById("calendar-body");
  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const today = new Date();

  monthYear.textContent = `${monthNames[month]} ${year}`;

  const firstDay = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();

  calendarBody.innerHTML = "";
  let row = document.createElement("tr");

  for (let i = 0; i < firstDay; i++) {
    row.appendChild(document.createElement("td"));
  }

  for (let day = 1; day <= lastDate; day++) {
    if (row.children.length === 7) {
      calendarBody.appendChild(row);
      row = document.createElement("tr");
    }

    const td = document.createElement("td");
    td.textContent = day;

    const fullDate = `${monthNames[month]} ${day}, ${year}`;
    const currentDayOfWeek = new Date(year, month, day).getDay();

    if (currentDayOfWeek === 0) {
      td.style.color = "#ccc";
      td.style.cursor = "default";
    } else {
      td.style.cursor = "pointer";
      td.onclick = () => {
        console.log("modalEnabled?", window.modalEnabled, "clicked date:", fullDate);
        if (window.modalEnabled) {
          openDateModal(fullDate);
        }
      };

      if (day === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
        td.style.fontWeight = "bold";
        td.style.color = "blue";
      }

      if (blockedDates[fullDate]) {
        td.style.backgroundColor = "rgba(255, 0, 0, 0.2)";
        td.style.borderRadius = "50%";
        td.style.color = "red";
      }
    }

    row.appendChild(td);
  }

  calendarBody.appendChild(row);
}

function prevMonth() {
  currentDate.setMonth(currentDate.getMonth() - 1);
  renderCalendar();
}

function nextMonth() {
  currentDate.setMonth(currentDate.getMonth() + 1);
  renderCalendar();
}

function openDateModal(date) {
  if (!window.modalEnabled) return;

  document.getElementById("selectedDateLabel").textContent = date;
  const container = document.getElementById("timeSlotContainer");
  container.innerHTML = "";

  let startHour = 7;
  const endHour = 18;
  const checkedSlots = savedTimeSlots[date] || [];

  while (startHour + 1.5 <= endHour) {
    const startTime = formatTime(startHour);
    const endTime = formatTime(startHour + 1.5);
    const label = `${startTime} - ${endTime}`;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "time_slot";
    checkbox.value = label;
    checkbox.checked = checkedSlots.includes(label);

    const labelElem = document.createElement("label");
    labelElem.appendChild(checkbox);
    labelElem.append(` ${label}`);

    container.appendChild(labelElem);
    startHour += 1.5;
  }

  document.getElementById("blockCheckbox").checked = blockedDates[date] || false;
  document.getElementById("dateModal").style.display = "block";
}

function formatTime(decimalHour) {
  const hours = Math.floor(decimalHour);
  const minutes = Math.round((decimalHour - hours) * 60);
  const suffix = hours >= 12 ? "PM" : "AM";
  const displayHour = ((hours + 11) % 12 + 1);
  const displayMin = minutes === 0 ? "00" : minutes.toString().padStart(2, "0");
  return `${displayHour}:${displayMin} ${suffix}`;
}

function closeModal() {
  document.getElementById("dateModal").style.display = "none";
}

function updateBlockedDatesInput() {
  const dates = Object.keys(blockedDates);
  console.log("🚩 Blocked dates saving:", dates);  // ✅ Added debug
  document.getElementById("blockedDatesInput").value = JSON.stringify(dates);
}

function saveDate() {
  const date = document.getElementById("selectedDateLabel").textContent;
  const isBlocked = document.getElementById("blockCheckbox").checked;
  const checkedSlots = Array.from(document.querySelectorAll("input[name='time_slot']:checked"))
    .map(i => i.value);

  if (isBlocked) {
    blockedDates[date] = true;
    delete savedTimeSlots[date];
  } else {
    delete blockedDates[date];
    if (checkedSlots.length > 0) {
      savedTimeSlots[date] = checkedSlots;
    } else {
      delete savedTimeSlots[date];
    }
  }

  updateBlockedDatesInput();
  renderCalendar();

  document.getElementById("saveSuccess").style.display = "block";
  setTimeout(() => {
    document.getElementById("saveSuccess").style.display = "none";
    closeModal();
  }, 2000);
}

// ✅ NEW: Load initial blocked dates passed from backend (from view_item.html)
if (typeof initialBlocked !== "undefined" && Array.isArray(initialBlocked)) {
  initialBlocked.forEach(date => {
    blockedDates[date] = true;
  });
}

window.onload = renderCalendar;
