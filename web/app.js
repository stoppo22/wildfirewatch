"use strict";

const map = L.map("map").setView([20.88, -156.67], 11);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

const eventList = document.querySelector("#event-list");
const eventDetails = document.querySelector("#event-details");

const priorityColors = {
  low: "#e9c46a",
  medium: "#f28c45",
  high: "#dc4c4c",
};

function createDetailLine(label, value) {
  const line = document.createElement("p");
  line.className = "detail-line";

  const labelElement = document.createElement("span");
  labelElement.className = "detail-label";
  labelElement.textContent = label;

  const valueElement = document.createElement("span");
  valueElement.textContent = value;

  line.append(labelElement, valueElement);

  return line;
}

function createDetailHeading(text) {
  const heading = document.createElement("h4");
  heading.className = "detail-heading";
  heading.textContent = text;

  return heading;
}

function formatUtcDate(timestamp) {
  const date = new Date(timestamp);

  return `${date.toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  })} UTC`;
}

async function loadEventDetails(eventId) {
  eventDetails.textContent = "Loading event details...";

  const response = await fetch(`/api/events/${eventId}`);

  if (!response.ok) {
    throw new Error(
      `Event request failed with status ${response.status}`
    );
  }

  const event = await response.json();

  const title = document.createElement("h3");
  title.textContent = `Event ${event.event_id}`;

  const priority = createDetailLine(
    "Priority",
    `${event.priority.level} (${event.priority.score.toFixed(1)})`
  );

  const priorityHeading = createDetailHeading("Priority evidence");

  const persistencePoints = createDetailLine(
    "Persistence points",
    event.priority.persistence_points.toFixed(1)
  );

  const frpTrendPoints = createDetailLine(
    "FRP trend points",
    event.priority.frp_trend_points.toFixed(1)
  );

  const spatialGrowthPoints = createDetailLine(
    "Spatial growth points",
    event.priority.spatial_growth_points.toFixed(1)
  );

  const detections = createDetailLine(
    "Detections",
    event.detection_count
  );

  const duration = createDetailLine(
    "Duration",
    `${event.duration_hours.toFixed(1)} hours`
  );

  const firstSeen = createDetailLine(
    "First seen",
    formatUtcDate(event.first_seen_utc)
  );

  const lastSeen = createDetailLine(
    "Last seen",
    formatUtcDate(event.last_seen_utc)
  );

  const landCover = createDetailLine(
    "Land cover",
    event.land_cover ?? "Unknown"
  );

  const evolutionHeading = createDetailHeading("Event evolution");

  const centroidPath = createDetailLine(
    "Centroid path",
    `${event.centroid_path_km.toFixed(2)} km`
  );

  const radiusChange = createDetailLine(
    "Radius change",
    `${event.radius_change_km.toFixed(2)} km`
  );

  const meanFrpChange = createDetailLine(
    "Mean FRP change",
    event.mean_frp_change.toFixed(2)
  );

  eventDetails.replaceChildren(
    title,
    priority,
    priorityHeading,
    persistencePoints,
    frpTrendPoints,
    spatialGrowthPoints,
    detections,
    duration,
    firstSeen,
    lastSeen,
    landCover,
    evolutionHeading,
    centroidPath,
    radiusChange,
    meanFrpChange
  );
}

function addEventToMap(event, button) {
  const position = [
    event.centroid_latitude,
    event.centroid_longitude,
  ];

  const marker = L.circleMarker(position, {
    radius: 9,
    color: priorityColors[event.priority.level],
    fillColor: priorityColors[event.priority.level],
    fillOpacity: 0.8,
    weight: 2,
  }).addTo(map);

  marker.bindTooltip(`Event ${event.event_id}`);

  button.addEventListener("click", () => {
    const selectedButton = eventList.querySelector(".is-selected");

    if (selectedButton !== null) {
      selectedButton.classList.remove("is-selected");
    }

    button.classList.add("is-selected");

    map.setView(position, 13);
    marker.openTooltip();

    loadEventDetails(event.event_id).catch((error) => {
      console.error("Could not load event details:", error);
      eventDetails.textContent = "Event details could not be loaded.";
    });
  });
}

async function loadEvents() {
  const response = await fetch("/api/events");

  if (!response.ok) {
    throw new Error(
      `Events request failed with status ${response.status}`
    );
  }

  const events = await response.json();
  eventList.replaceChildren();

  if (events.length === 0) {
    eventList.textContent = "No candidate events are stored.";
    return;
  }

  for (const event of events) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = "event-item";
    button.dataset.eventId = event.event_id;
    button.textContent =
      `Event ${event.event_id} | ${event.priority.level} priority`;

    eventList.append(button);
    addEventToMap(event, button);
  }
}

loadEvents().catch((error) => {
  console.error("Could not load candidate events:", error);
  eventList.textContent = "Candidate events could not be loaded.";
});
