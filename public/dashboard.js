

const DATA_URL = "data/dashboard_data.json";

const SERIES_COLORS = {
  police_operations:    getCssVar("--series-ops"),
  living_sites_evicted: getCssVar("--series-sites"),
  people_evicted:       getCssVar("--series-people"),
};

const state = {
  payload: null,
  indicators: [],          // [{key, label}]
  regions: [],             // strings (incl. configured extras)
  legalCategories: [],     // strings (incl. configured extras)

  filters: {
    indicators: new Set(["police_operations", "living_sites_evicted", "people_evicted"]),
    regions: new Set(),
    legal: new Set(),
    dateStart: null,       // Date
    dateEnd: null,         // Date
  },
  aggregation: "weekly",   // "daily" | "weekly" | "monthly"
  pinned: null,            // pinned tooltip payload
};

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

window.addEventListener("DOMContentLoaded", () => {
  fetch(DATA_URL, { cache: "no-store" })
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status} loading ${DATA_URL}`);
      return r.json();
    })
    .then(init)
    .catch((err) => {
      const banner = document.getElementById("error-banner");
      banner.hidden = false;
      banner.textContent =
        "Could not load dashboard data. Run scripts/preprocess.py and make sure " +
        "you're serving this folder over HTTP. Details: " + err.message;
      console.error(err);
    });
});

function init(payload) {
  state.payload = payload;
  state.indicators = payload.indicators || [];
  state.regions = payload.regions || [];
  state.legalCategories = payload.legal_basis_categories || [];
  state.aggregation = payload.config?.default_aggregation || "weekly";

  // Refresh series colors after CSS has applied.
  SERIES_COLORS.police_operations    = getCssVar("--series-ops")    || SERIES_COLORS.police_operations;
  SERIES_COLORS.living_sites_evicted = getCssVar("--series-sites")  || SERIES_COLORS.living_sites_evicted;
  SERIES_COLORS.people_evicted       = getCssVar("--series-people") || SERIES_COLORS.people_evicted;

  // Default selections: everything on.
  state.filters.regions = new Set(state.regions);
  state.filters.legal = new Set(state.legalCategories);

  const min = payload.date_range?.min ? parseISO(payload.date_range.min) : null;
  const max = payload.date_range?.max ? parseISO(payload.date_range.max) : null;
  state.filters.dateStart = min;
  state.filters.dateEnd = max;

  buildRegionChecks();
  buildLegalChecklist();
  buildDateSlider(min, max);
  bindIndicatorChecks();
  bindAggregationRadios();
  bindTooltipDismiss();
  bindExplanationPanel();
  bindInfoIcons();

  setAggregationFromState();
  update();

  window.addEventListener("resize", () => {
    buildDateSlider(min, max);
    drawChart();
  });
}



function bindExplanationPanel() {
  const sections = document.querySelectorAll(".controls__section[data-section]");
  const target = document.getElementById("selection-explanation");
  if (!target) return;

  const defaultText = target.textContent.trim();

  function show(sec) {
    const text = sec?.dataset?.explanation;
    target.textContent = text || defaultText;
    sections.forEach((s) => s.removeAttribute("data-active"));
    if (sec) sec.setAttribute("data-active", "true");
  }

  sections.forEach((sec) => {
    if (sec.dataset.section === "explanation") return; // describing itself is silly
    sec.addEventListener("mouseenter", () => show(sec));
    sec.addEventListener("focusin",    () => show(sec));
    sec.addEventListener("change",     () => show(sec));
  });

  // When the cursor leaves the whole sidebar, reset to the default text.
  const sidebar = document.querySelector(".controls");
  if (sidebar) {
    sidebar.addEventListener("mouseleave", () => show(null));
  }
}

function bindInfoIcons() {
  const icons = document.querySelectorAll(".info-icon");
  icons.forEach((icon) => {
    const popover = icon.closest(".controls__heading")?.nextElementSibling;
    if (!popover || !popover.classList.contains("info-popover")) return;
    icon.addEventListener("click", () => {
      const isOpen = !popover.hidden;
      icons.forEach((other) => {
        other.setAttribute("aria-expanded", "false");
        const p = other.closest(".controls__heading")?.nextElementSibling;
        if (p && p.classList.contains("info-popover")) p.hidden = true;
      });
      if (!isOpen) {
        popover.hidden = false;
        icon.setAttribute("aria-expanded", "true");
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Filter widgets
// ---------------------------------------------------------------------------

function buildRegionChecks() {
  const host = document.getElementById("regions");
  host.innerHTML = "";
  state.regions.forEach((region) => {
    const label = document.createElement("label");
    label.className = "check";
    label.innerHTML = `
      <input type="checkbox" value="${escapeAttr(region)}" checked />
      <span>${escapeHtml(region)}</span>
    `;
    label.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) state.filters.regions.add(region);
      else state.filters.regions.delete(region);
      update();
    });
    host.appendChild(label);
  });
}

function buildLegalChecklist() {
  const host = document.getElementById("legal-basis");
  host.innerHTML = "";
  state.legalCategories.forEach((cat) => {
    const label = document.createElement("label");
    label.className = "check";
    label.innerHTML = `
      <input type="checkbox" value="${escapeAttr(cat)}" checked />
      <span>${escapeHtml(cat)}</span>
    `;
    label.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) state.filters.legal.add(cat);
      else state.filters.legal.delete(cat);
      update();
    });
    host.appendChild(label);
  });
}


function buildDateSlider(min, max) {
  const host = d3.select("#date-slider");
  host.selectAll("*").remove();

  const startInput = document.getElementById("slider-start");
  const endInput = document.getElementById("slider-end");
  if (!min || !max || min >= max) {
    if (startInput) { startInput.value = ""; startInput.disabled = true; }
    if (endInput) { endInput.value = ""; endInput.disabled = true; }
    return;
  }
  if (startInput) {
    startInput.disabled = false;
    startInput.min = isoDate(min);
    startInput.max = isoDate(max);
  }
  if (endInput) {
    endInput.disabled = false;
    endInput.min = isoDate(min);
    endInput.max = isoDate(max);
  }

  const width = host.node().getBoundingClientRect().width || 200;
  const height = 26;
  const handleSize = 16;
  const trackY = height / 2;
  const trackH = 5;
  const pad = handleSize / 2 + 1;
  const innerLeft = pad;
  const innerRight = width - pad;

  const xScale = d3.scaleTime()
    .domain([min, max])
    .range([innerLeft, innerRight])
    .clamp(true);

  const svg = host.append("svg").attr("width", width).attr("height", height);

  svg.append("rect")
    .attr("class", "slider-track")
    .attr("x", innerLeft)
    .attr("y", trackY - trackH / 2)
    .attr("width", innerRight - innerLeft)
    .attr("height", trackH);

  const active = svg.append("rect")
    .attr("class", "slider-active")
    .attr("y", trackY - trackH / 2)
    .attr("height", trackH);

  const startHandle = svg.append("rect")
    .attr("class", "slider-handle")
    .attr("width", handleSize)
    .attr("height", handleSize)
    .attr("y", trackY - handleSize / 2)
    .attr("rx", handleSize / 2)
    .attr("ry", handleSize / 2);

  const endHandle = svg.append("rect")
    .attr("class", "slider-handle")
    .attr("width", handleSize)
    .attr("height", handleSize)
    .attr("y", trackY - handleSize / 2)
    .attr("rx", handleSize / 2)
    .attr("ry", handleSize / 2);

  // Clamp current state into the slider domain in case the data shrank.
  if (state.filters.dateStart < min) state.filters.dateStart = min;
  if (state.filters.dateEnd > max)   state.filters.dateEnd   = max;
  if (state.filters.dateStart > state.filters.dateEnd) {
    state.filters.dateStart = min;
    state.filters.dateEnd = max;
  }

  function paint() {
    const x1 = xScale(state.filters.dateStart);
    const x2 = xScale(state.filters.dateEnd);
    startHandle.attr("x", x1 - handleSize / 2);
    endHandle.attr("x", x2 - handleSize / 2);
    active
      .attr("x", Math.min(x1, x2))
      .attr("width", Math.max(0, Math.abs(x2 - x1)));
    if (startInput) startInput.value = isoDate(state.filters.dateStart);
    if (endInput) endInput.value = isoDate(state.filters.dateEnd);
  }
  paint();

  // Throttle the live dashboard update to one redraw per animation frame
  // so continuous dragging stays smooth even on the larger chart.
  let rafPending = false;
  function liveUpdate() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      update();
    });
  }

  function makeDrag(which) {
    return d3.drag()
      .on("drag", (event) => {
        const d = xScale.invert(event.x);
        if (which === "start") {
          if (d <= state.filters.dateEnd) state.filters.dateStart = d;
          else state.filters.dateStart = state.filters.dateEnd;
        } else {
          if (d >= state.filters.dateStart) state.filters.dateEnd = d;
          else state.filters.dateEnd = state.filters.dateStart;
        }
        paint();
        liveUpdate();        // continuous: chart + totals follow the handle
      })
      .on("end", () => update());
  }

  startHandle.call(makeDrag("start"));
  endHandle.call(makeDrag("end"));

  function onTypedDate(which) {
    return (event) => {
      const d = parseISO(event.target.value);
      if (!d) return;
      if (which === "start") {
        state.filters.dateStart = d < min ? min : (d > state.filters.dateEnd ? state.filters.dateEnd : d);
      } else {
        state.filters.dateEnd = d > max ? max : (d < state.filters.dateStart ? state.filters.dateStart : d);
      }
      paint();
      update();
    };
  }
  if (startInput) startInput.addEventListener("change", onTypedDate("start"));
  if (endInput) endInput.addEventListener("change", onTypedDate("end"));
}

function bindIndicatorChecks() {
  document.querySelectorAll("#indicators input[type=checkbox]").forEach((cb) => {
    cb.addEventListener("change", () => {
      if (cb.checked) state.filters.indicators.add(cb.value);
      else state.filters.indicators.delete(cb.value);
      update();
    });
  });
}

function bindAggregationRadios() {
  document.querySelectorAll('input[name="agg"]').forEach((r) => {
    r.addEventListener("change", () => {
      if (r.checked) {
        state.aggregation = r.value;
        update();
      }
    });
  });
}

function setAggregationFromState() {
  document.querySelectorAll('input[name="agg"]').forEach((r) => {
    r.checked = (r.value === state.aggregation);
  });
}

// ---------------------------------------------------------------------------
// Update loop
// ---------------------------------------------------------------------------

function update() {
  const records = filteredRecords();
  const series = buildSeries(records, state.aggregation);
  drawChart(series);
  drawLegend(series);
  drawTotals(records);
}

function filteredRecords() {
  const { regions, legal, dateStart, dateEnd } = state.filters;
  const all = state.payload.cleaned_records || [];
  return all.filter((r) => {
    if (!regions.has(r.region)) return false;
    if (!legal.has(r.legal_basis)) return false;
    const d = parseISO(r.date);
    if (!d) return false;
    if (dateStart && d < startOfDay(dateStart)) return false;
    if (dateEnd && d > endOfDay(dateEnd)) return false;
    return true;
  });
}

// ---------------------------------------------------------------------------
// Aggregation
// ---------------------------------------------------------------------------

function periodBounds(d, agg) {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  if (agg === "daily") {
    return { start: x, end: x };
  }
  if (agg === "monthly") {
    const start = new Date(x.getFullYear(), x.getMonth(), 1);
    const end = new Date(x.getFullYear(), x.getMonth() + 1, 0);
    return { start, end };
  }
  // weekly (ISO: Monday start)
  const day = (x.getDay() + 6) % 7;            // 0 = Monday
  const start = new Date(x);
  start.setDate(x.getDate() - day);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return { start, end };
}

/** Given a period START date, return the START of the next period for `agg`. */
function nextPeriodStart(date, agg) {
  if (agg === "monthly") return new Date(date.getFullYear(), date.getMonth() + 1, 1);
  const step = agg === "daily" ? 1 : 7;
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + step);
}

/**
 * Build series for the chart. Returns:
 *   {
 *     periods: [{date, end, perInd}, ...]   // sorted unique periods
 *     byIndicator: {
 *       police_operations: {
 *         label, color, points: [{date, period_start, period_end, value,
 *                                  legal_breakdown:[{cat,value}], source_rows}]
 *       }, ...
 *     }
 *   }
 */
function buildSeries(records, agg) {
  const indicatorKeys = state.indicators.map((i) => i.key);
  const selected = indicatorKeys.filter((k) => state.filters.indicators.has(k));

  // periodKey -> { date, end, perInd: { key -> {value, source_rows, legal:Map} } }
  const buckets = new Map();

  records.forEach((r) => {
    const d = parseISO(r.date);
    if (!d) return;
    const { start, end } = periodBounds(d, agg);
    const key = start.toISOString().slice(0, 10);
    let b = buckets.get(key);
    if (!b) {
      b = { date: start, end, perInd: {} };
      indicatorKeys.forEach((k) => {
        b.perInd[k] = { value: 0, source_rows: 0, legal: new Map() };
      });
      buckets.set(key, b);
    }
    indicatorKeys.forEach((k) => {
      const v = r[k] || 0;
      b.perInd[k].value += v;
      b.perInd[k].source_rows += r.source_rows || 0;
      if (v > 0) {
        b.perInd[k].legal.set(r.legal_basis, (b.perInd[k].legal.get(r.legal_basis) || 0) + v);
      }
    });
  });

  // Fill empty periods between the first and last event with zero-value
  // buckets, so the line correctly returns to baseline on periods that had no
  // events. Without this, the chart interpolates straight across the gaps and
  // (in daily mode especially) falsely implies sustained activity that never
  // happened.
  if (buckets.size) {
    const dates = [...buckets.values()].map((b) => b.date);
    const minStart = new Date(Math.min(...dates));
    const maxStart = new Date(Math.max(...dates));
    let cur = new Date(minStart.getFullYear(), minStart.getMonth(), minStart.getDate());
    const last = new Date(maxStart.getFullYear(), maxStart.getMonth(), maxStart.getDate());
    while (cur <= last) {
      const { start, end } = periodBounds(cur, agg);
      const key = start.toISOString().slice(0, 10);
      if (!buckets.has(key)) {
        const b = { date: start, end, perInd: {} };
        indicatorKeys.forEach((k) => {
          b.perInd[k] = { value: 0, source_rows: 0, legal: new Map() };
        });
        buckets.set(key, b);
      }
      cur = nextPeriodStart(cur, agg);
    }
  }

  const periods = [...buckets.values()].sort((a, b) => a.date - b.date);

  const byIndicator = {};
  selected.forEach((k) => {
    const meta = state.indicators.find((i) => i.key === k);
    const points = periods.map((p) => ({
      date: p.date,
      period_start: isoDate(p.date),
      period_end: isoDate(p.end),
      value: p.perInd[k].value,
      source_rows: p.perInd[k].source_rows,
      legal_breakdown: [...p.perInd[k].legal.entries()]
        .sort((a, b) => b[1] - a[1])
        .map(([cat, value]) => ({ cat, value })),
    }));
    byIndicator[k] = {
      key: k,
      label: meta?.label || k,
      color: SERIES_COLORS[k] || "#000",
      points,
    };
  });

  return { periods, byIndicator };
}

// ---------------------------------------------------------------------------
// Chart drawing
// ---------------------------------------------------------------------------

let cached = { series: null };
let chartLayer = null; // { hoverLine, hoverDots } d3 selections for the current chart

function drawChart(maybeSeries) {
  if (maybeSeries) cached.series = maybeSeries;
  const series = cached.series;
  const container = document.getElementById("chart");
  container.innerHTML = "";

  if (!series || !series.periods.length || !Object.keys(series.byIndicator).length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No data for the current filters.";
    container.appendChild(empty);
    return;
  }

  const width = container.clientWidth;
  const height = container.clientHeight || 400;
  // Bottom + left have extra room for the year row and the "Period" / "Value"
  // axis labels.
  const margin = { top: 14, right: 18, bottom: 58, left: 54 };
  const innerW = Math.max(20, width - margin.left - margin.right);
  const innerH = Math.max(20, height - margin.top - margin.bottom);

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMinYMin meet");

  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const allPoints = Object.values(series.byIndicator).flatMap((s) => s.points);
  const xDomain = d3.extent(allPoints, (d) => d.date);
  const yMax = d3.max(allPoints, (d) => d.value) || 1;

  // No .nice() on x: the domain is the exact extent of the plotted periods so
  // the first and last points sit on the left/right plot edges with no
  // leading/trailing padding. Single-period guard keeps the line visible.
  if (xDomain[0] && xDomain[1] && +xDomain[0] === +xDomain[1]) {
    const pad = 12 * 60 * 60 * 1000;
    xDomain[0] = new Date(+xDomain[0] - pad);
    xDomain[1] = new Date(+xDomain[1] + pad);
  }
  const x = d3.scaleTime().domain(xDomain).range([0, innerW]);
  const y = d3.scaleLinear().domain([0, yMax]).range([innerH, 0]).nice();

  // Gridlines: few, solid, light.
  g.append("g")
    .attr("class", "grid")
    .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(() => ""));

  // Axes. Pick a tick cadence that keeps the x-axis uncluttered: month ticks
  // for any span over ~10 weeks (matching the monthly-style target), weekly
  // ticks for medium spans, otherwise a sensible count of daily ticks.
  const spanDays = (xDomain[1] - xDomain[0]) / 86400000;
  const xAxis = d3.axisBottom(x);
  if (state.aggregation === "monthly" || spanDays > 70) {
    xAxis.ticks(d3.timeMonth.every(1)).tickFormat(d3.timeFormat("%B"));
  } else if (spanDays > 21) {
    xAxis.ticks(d3.timeWeek.every(1)).tickFormat(d3.timeFormat("%d %b"));
  } else {
    xAxis
      .ticks(Math.min(8, Math.max(2, Math.floor(innerW / 90))))
      .tickFormat(axisDateFormat(state.aggregation));
  }
  g.append("g")
    .attr("class", "axis axis--x")
    .attr("transform", `translate(0,${innerH})`)
    .call(xAxis);

  // Year row: a label at each January 1st that falls within the plotted
  // range, marking where the new year begins on the axis.
  const yearLabels = [];
  for (let yr = xDomain[0].getFullYear(); yr <= xDomain[1].getFullYear(); yr++) {
    const jan1 = new Date(yr, 0, 1);
    if (jan1 >= xDomain[0] && jan1 <= xDomain[1]) {
      yearLabels.push({ year: yr, date: jan1 });
    }
  }

  g.append("g")
    .attr("class", "axis axis--year")
    .selectAll("text")
    .data(yearLabels)
    .enter()
    .append("text")
    .attr("x", (d) => x(d.date))
    .attr("y", innerH + 34)
    .attr("text-anchor", "middle")
    .text((d) => d.year);

  g.append("g")
    .attr("class", "axis axis--y")
    .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format("d")));

  // Axis labels: rotated "Value" on the left, "Period" centred at the bottom.
  g.append("text")
    .attr("class", "axis-label")
    .attr("text-anchor", "middle")
    .attr("transform", `translate(${-38},${innerH / 2}) rotate(-90)`)
    .text("Amount");

  g.append("text")
    .attr("class", "axis-label")
    .attr("text-anchor", "middle")
    .attr("x", innerW / 2)
    .attr("y", innerH + 52)
    .text("Period");

  // Lines
  const line = d3.line()
    .defined((d) => Number.isFinite(d.value))
    .x((d) => x(d.date))
    .y((d) => y(d.value))
    .curve(d3.curveMonotoneX);

  Object.values(series.byIndicator).forEach((s) => {
    g.append("path")
      .datum(s.points)
      .attr("class", "series-line")
      .attr("d", line)
      .attr("stroke", s.color);
  });

  // Interaction layer: a vertical guide + one highlight dot per visible series.
  // These are shown only when a point is *clicked* — there is no hover tooltip.
  const hoverLine = g.append("line")
    .attr("class", "hover-line")
    .attr("y1", 0).attr("y2", innerH)
    .style("display", "none");

  const hoverDots = g.append("g").attr("class", "hover-dots");

  // Transparent click target sized exactly to the plot area and placed INSIDE
  // the same <g> as the lines, so pointer coordinates share the line's
  // x-scale (no left-margin offset → the hitbox matches the rendered points).
  const overlay = g.append("rect")
    .attr("class", "interaction-overlay")
    .attr("x", 0).attr("y", 0)
    .attr("width", innerW).attr("height", innerH)
    .attr("fill", "transparent");

  // Permanent dot markers at each plotted point. Appended after the overlay
  // so they sit on top of it and can receive their own mouseenter/mouseleave
  // (otherwise the overlay would swallow the events first).
  Object.values(series.byIndicator).forEach((s) => {
    g.append("g")
      .attr("class", "series-dots")
      .selectAll("circle")
      .data(s.points.filter((d) => Number.isFinite(d.value)))
      .enter()
      .append("circle")
      .attr("class", "series-dot")
      .attr("cx", (d) => x(d.date))
      .attr("cy", (d) => y(d.value))
      .attr("r", 3)
      .attr("fill", s.color)
      .on("mouseenter", function () {
        d3.select(this).transition().duration(120).attr("r", 6);
      })
      .on("mouseleave", function () {
        d3.select(this).transition().duration(120).attr("r", 3);
      })
      .on("click", (event, d) => {
        event.stopPropagation();
        pinAt(d.date);
      });
  });

  // Expose this draw's guide/dots for the global dismiss handlers.
  chartLayer = { hoverLine, hoverDots };

  const tooltip = ensureTooltip();
  const periodDates = series.periods.map((p) => p.date);
  const bisectDate = d3.bisector((d) => d).left;

  function nearestPeriod(mx) {
    const t = x.invert(mx);
    const i = bisectDate(periodDates, t);
    const left = periodDates[i - 1];
    const right = periodDates[i];
    if (!left) return right;
    if (!right) return left;
    return (t - left) < (right - t) ? left : right;
  }

  // Convert a point given in <g> coordinates to viewport (client) coordinates,
  // accounting for any scaling between the SVG viewBox and its rendered size,
  // so the tooltip anchors to the actual on-screen point.
  function clientPointFor(gx, gy) {
    const r = svg.node().getBoundingClientRect();
    const sx = r.width / width;
    const sy = r.height / height;
    return {
      clientX: r.left + (margin.left + gx) * sx,
      clientY: r.top + (margin.top + gy) * sy,
    };
  }

  function pinAt(periodDate) {
    const periodKey = isoDate(periodDate);
    const dotData = [];
    const indicatorPoints = {};
    Object.values(series.byIndicator).forEach((s) => {
      const p = s.points.find((pt) => isoDate(pt.date) === periodKey);
      if (p) {
        dotData.push({ ...p, color: s.color, label: s.label, key: s.key });
        indicatorPoints[s.key] = p;
      }
    });
    if (!Object.keys(indicatorPoints).length) {
      clearPinnedTooltip();
      return;
    }

    hoverLine.style("display", null)
      .attr("x1", x(periodDate)).attr("x2", x(periodDate));

    const dots = hoverDots.selectAll("circle").data(dotData, (d) => d.key);
    dots.exit().remove();
    dots.enter().append("circle")
      .attr("class", "hover-dot")
      .attr("r", 4)
      .merge(dots)
      .attr("cx", (d) => x(d.date))
      .attr("cy", (d) => y(d.value))
      .attr("fill", (d) => d.color);

    // Anchor the tooltip to the top-most (highest value) clicked point.
    const topValue = d3.max(dotData, (d) => d.value);
    const anchor = clientPointFor(x(periodDate), y(topValue));
    state.pinned = { periodKey };
    showTooltip(tooltip, anchor, periodDate, indicatorPoints, true);
  }

  // Click / tap only. Hover does nothing but show the pointer cursor (CSS).
  overlay.on("click", (event) => {
    const [mx] = d3.pointer(event, g.node());
    const periodDate = nearestPeriod(mx);
    if (!periodDate) {
      clearPinnedTooltip();
      return;
    }
    pinAt(periodDate);
  });

  // Restore a tooltip pinned before this redraw (filter / aggregation / resize
  // change) so the guide + dots realign to the freshly drawn geometry.
  if (state.pinned) {
    const restore = series.periods.find((p) => isoDate(p.date) === state.pinned.periodKey);
    if (restore) pinAt(restore.date);
    else clearPinnedTooltip();
  }
}

/**
 * Hide and unpin the click tooltip from anywhere (overlay, document click,
 * Escape, close button). Uses the guide/dots captured by the latest drawChart.
 */
function clearPinnedTooltip() {
  state.pinned = null;
  if (chartLayer) {
    chartLayer.hoverLine.style("display", "none");
    chartLayer.hoverDots.selectAll("circle").remove();
  }
  const tt = document.querySelector(".tooltip");
  if (tt) tt.classList.remove("is-visible", "is-pinned");
}

function axisDateFormat(agg) {
  if (agg === "daily")  return d3.timeFormat("%d %b");
  if (agg === "monthly") return d3.timeFormat("%b %Y");
  return d3.timeFormat("%d %b");
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function ensureTooltip() {
  let el = document.querySelector(".tooltip");
  if (el) return el;
  el = document.createElement("div");
  el.className = "tooltip";
  document.body.appendChild(el);
  return el;
}

function bindTooltipDismiss() {
  // Click outside the chart / tooltip closes the pinned bubble. Clicks inside
  // the chart svg are handled by the overlay (which re-pins or clears).
  document.addEventListener("click", (e) => {
    if (!state.pinned) return;
    const tt = document.querySelector(".tooltip");
    if (tt && tt.contains(e.target)) return;
    if (e.target.closest("#chart svg")) return;
    clearPinnedTooltip();
  });

  // Escape closes the pinned bubble.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && state.pinned) clearPinnedTooltip();
  });
}

function showTooltip(el, event, periodDate, indicatorPoints, pinned) {
  if (!event) return;
  const period = formatPeriod(periodDate, state.aggregation, Object.values(indicatorPoints)[0]?.period_end);
  const regionCtx = filterContext(state.filters.regions, state.regions, "All regions");
  const legalCtx  = filterContext(state.filters.legal, state.legalCategories, "All categories");

  const rows = state.indicators
    .filter((ind) => state.filters.indicators.has(ind.key))
    .map((ind) => {
      const p = indicatorPoints[ind.key];
      if (!p) return "";
      const top = p.legal_breakdown.slice(0, 3)
        .map((lb) => `<li><span>${escapeHtml(lb.cat)}</span><span>${lb.value}</span></li>`)
        .join("");
      const sub = top
        ? `<div class="tooltip__sub"><h4>Top legal basis</h4><ul>${top}</ul></div>`
        : "";
      return `
        <div class="tooltip__row tooltip__row--ind">
          <span class="tooltip__label" style="color:${SERIES_COLORS[ind.key]}">${escapeHtml(ind.label)}</span>
          <span class="tooltip__value">${p.value}</span>
        </div>
        <div class="tooltip__row"><span class="tooltip__label">Source rows</span><span class="tooltip__value">${p.source_rows}</span></div>
        ${sub}
      `;
    })
    .join("");

  const reportLinks = pinned ? buildReportLinksHtml(periodDate) : "";

  el.innerHTML = `
    ${pinned ? '<button class="tooltip__close" aria-label="Close">×</button>' : ""}
    <div class="tooltip__period">${period}</div>
    <div class="tooltip__row"><span class="tooltip__label">Regions</span><span class="tooltip__value">${escapeHtml(regionCtx)}</span></div>
    <div class="tooltip__row"><span class="tooltip__label">Legal basis</span><span class="tooltip__value">${escapeHtml(legalCtx)}</span></div>
    ${rows || '<div class="tooltip__row"><span class="tooltip__label">No indicator selected</span></div>'}
    ${reportLinks}
    ${pinned ? "" : '<div class="tooltip__pin-hint">Click to pin · view reports</div>'}
  `;
  el.classList.add("is-visible");
  el.classList.toggle("is-pinned", pinned);
  positionTooltip(el, event);

  if (pinned) {
    const close = el.querySelector(".tooltip__close");
    if (close) close.addEventListener("click", (e) => {
      e.stopPropagation();
      clearPinnedTooltip();
    });
  }
}

/**
 * Build the "Open monthly report" link row(s) for the pinned tooltip.
 * One link per currently selected region whose YYYY-MM has a configured URL.
 * Falls back to the HRO listing URL when nothing matches.
 */
function buildReportLinksHtml(periodDate) {
  const reports = state.payload?.monthly_reports || {};
  const index = state.payload?.monthly_reports_index_url || "";
  const ym = `${periodDate.getFullYear()}-${String(periodDate.getMonth() + 1).padStart(2, "0")}`;
  const monthMap = reports[ym] || {};

  const selectedRegions = [...state.filters.regions];
  const links = [];

  selectedRegions.forEach((region) => {
    const url = monthMap[region];
    if (url) {
      links.push({ url, label: `Open ${region} report — ${formatMonthLabel(periodDate)}` });
    }
  });

  if (!links.length) {
    if (!index) return "";
    return `
      <div class="tooltip__links">
        <a class="tooltip__link tooltip__link--fallback"
           href="${escapeAttr(index)}" target="_blank" rel="noopener noreferrer">
          No report on file — open HRO monthly observations
        </a>
      </div>
    `;
  }

  return `
    <div class="tooltip__links">
      ${links.map((l) => `
        <a class="tooltip__link" href="${escapeAttr(l.url)}"
           target="_blank" rel="noopener noreferrer">
          ${escapeHtml(l.label)}
        </a>
      `).join("")}
    </div>
  `;
}

function formatMonthLabel(d) {
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long" });
}

function positionTooltip(el, event) {
  const pad = 10;
  const rect = el.getBoundingClientRect();
  let x = event.clientX + pad;
  let y = event.clientY + pad;
  if (x + rect.width  > window.innerWidth  - 8) x = event.clientX - rect.width  - pad;
  if (y + rect.height > window.innerHeight - 8) y = event.clientY - rect.height - pad;
  el.style.left = `${Math.max(8, x + window.scrollX)}px`;
  el.style.top  = `${Math.max(8, y + window.scrollY)}px`;
}

function filterContext(selected, all, allLabel) {
  const arr = [...selected];
  if (!arr.length) return "(none)";
  if (arr.length === all.length) return allLabel;
  if (arr.length <= 3) return arr.join(", ");
  return `${arr.length} of ${all.length} selected`;
}

// ---------------------------------------------------------------------------
// Legend + totals
// ---------------------------------------------------------------------------

function drawLegend(series) {
  const host = document.getElementById("legend");
  host.innerHTML = "";
  Object.values(series.byIndicator).forEach((s) => {
    const item = document.createElement("span");
    item.className = "legend__item";
    item.innerHTML = `
      <span class="legend__swatch" style="background:${s.color}"></span>
      <span>${escapeHtml(s.label)}</span>
    `;
    host.appendChild(item);
  });
}

function drawTotals(records) {
  const totals = { police_operations: 0, living_sites_evicted: 0, people_evicted: 0 };
  records.forEach((r) => {
    totals.police_operations    += r.police_operations    || 0;
    totals.living_sites_evicted += r.living_sites_evicted || 0;
    totals.people_evicted       += r.people_evicted       || 0;
  });
  document.getElementById("total-operations").textContent = formatNumber(totals.police_operations);
  document.getElementById("total-sites").textContent      = formatNumber(totals.living_sites_evicted);
  document.getElementById("total-people").textContent     = formatNumber(totals.people_evicted);
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function formatPeriod(d, agg, endISO) {
  if (agg === "daily") {
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }
  if (agg === "monthly") {
    return d.toLocaleDateString(undefined, { year: "numeric", month: "long" });
  }
  const end = endISO ? parseISO(endISO) : new Date(d.getTime() + 6 * 86400000);
  return `${shortDate(d)} → ${shortDate(end)}`;
}
function shortDate(d) {
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
function formatNumber(n) { return n.toLocaleString(); }
function isoDate(d) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}
function parseISO(s) {
  if (!s) return null;
  // Parse as local date to avoid timezone shifts on date-only strings.
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  const d = new Date(s);
  return isNaN(d) ? null : d;
}
function startOfDay(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; }
function endOfDay(d)   { const x = new Date(d); x.setHours(23, 59, 59, 999); return x; }
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s); }
function getCssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "";
}
