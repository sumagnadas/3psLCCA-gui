"""
gui/components/outputs/lcc_plot.py

Creates an interactive matplotlib chart from LCC analysis results.
Use LCCChartWidget(results) to get a QWidget ready to embed in Qt.
"""

import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
except ImportError:
    from matplotlib.backends.backend_qt import FigureCanvasQTAgg, NavigationToolbar2QT


def M(x):
    """Convert to Million INR."""
    return x / 1e6


def sci_label(x):
    if x == 0:
        return "0"
    exp = int(np.floor(np.log10(abs(x))))
    coeff = x / (10 ** exp)
    return rf"${coeff:.0f}\cdot10^{{{exp}}}$"


def _get(d, *keys, default=0.0):
    """Safe nested dict access."""
    node = d
    for k in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(k, default)
    return node if node is not None else default


def _build_chart_data(results: dict):
    """
    Build values, labels, and stage_info from results.
    Returns (values, labels, stage_info).
    Stage order: Initial → Use → Reconstruction (optional) → End-of-Life
    """
    values = []
    labels = []

    # ── Initial stage (0-4) ────────────────────────────────────────────────
    values += [
        M(_get(results, "initial_stage", "economic",     "initial_construction_cost")),
        M(_get(results, "initial_stage", "environmental","initial_material_carbon_emission_cost")),
        M(_get(results, "initial_stage", "economic",     "time_cost_of_loan")),
        M(_get(results, "initial_stage", "social",       "initial_road_user_cost")),
        M(_get(results, "initial_stage", "environmental","initial_vehicular_emission_cost")),
    ]
    labels += [
        "Initial construction cost",
        "Initial carbon emission cost",
        "Time-related cost",
        "Road user cost (construction)",
        "Vehicular emission (rerouting)",
    ]

    # ── Use stage (5-15) ───────────────────────────────────────────────────
    values += [
        M(_get(results, "use_stage", "economic",     "routine_inspection_costs")),
        M(_get(results, "use_stage", "economic",     "periodic_maintenance")),
        M(_get(results, "use_stage", "environmental","periodic_carbon_costs")),
        M(_get(results, "use_stage", "economic",     "major_inspection_costs")),
        M(_get(results, "use_stage", "economic",     "major_repair_cost")),
        M(_get(results, "use_stage", "environmental","major_repair_material_carbon_emission_costs")),
        M(_get(results, "use_stage", "environmental","major_repair_vehicular_emission_costs")),
        M(_get(results, "use_stage", "social",       "major_repair_road_user_costs")),
        M(_get(results, "use_stage", "economic",     "replacement_costs_for_bearing_and_expansion_joint")),
        M(_get(results, "use_stage", "environmental","vehicular_emission_costs_for_replacement_of_bearing_and_expansion_joint")),
        M(_get(results, "use_stage", "social",       "road_user_costs_for_replacement_of_bearing_and_expansion_joint")),
    ]
    labels += [
        "Routine inspection cost",
        "Periodic maintenance cost",
        "Maintenance carbon cost",
        "Major inspection cost",
        "Major repair cost",
        "Repair carbon emission cost",
        "Repair vehicular emission cost",
        "Road user cost (repairs)",
        "Bearing & joint replacement cost",
        "Vehicular emission (replacement)",
        "Road user cost (replacement)",
    ]

    stage_info = [
        {"start": 0,  "end": 4,  "color": "#cfd9e8", "title": "Initial Stage",      "tick_color": "#2c4a75"},
        {"start": 5,  "end": 15, "color": "#cfe8e2", "title": "Use Stage",           "tick_color": "#1f6f66"},
    ]

    # ── Reconstruction stage (optional) ────────────────────────────────────
    if bool(results.get("reconstruction")):
        recon_start = len(values)
        values += [
            M(_get(results, "reconstruction", "economic",     "cost_of_reconstruction_after_demolition")),
            M(_get(results, "reconstruction", "environmental","carbon_cost_of_reconstruction_after_demolition")),
            M(_get(results, "reconstruction", "economic",     "time_cost_of_loan")),
            M(_get(results, "reconstruction", "economic",     "total_demolition_and_disposal_costs")),
            M(_get(results, "reconstruction", "environmental","carbon_costs_demolition_and_disposal")),
            M(_get(results, "reconstruction", "environmental","demolition_vehicular_emission_cost")),
            M(_get(results, "reconstruction", "environmental","reconstruction_vehicular_emission_cost")),
            M(_get(results, "reconstruction", "social",       "ruc_demolition")),
            M(_get(results, "reconstruction", "social",       "ruc_reconstruction")),
            -M(_get(results, "reconstruction", "economic",    "total_scrap_value")),
        ]
        labels += [
            "Reconstruction cost",
            "Reconstruction carbon cost",
            "Time-related cost (recon.)",
            "Demolition & disposal (recon.)",
            "Demolition carbon cost (recon.)",
            "Vehicular emission (demo. recon.)",
            "Vehicular emission (reconstruction)",
            "Road user cost (demo. recon.)",
            "Road user cost (reconstruction)",
            "Scrap value credit (recon.)",
        ]
        stage_info.append({
            "start": recon_start, "end": len(values) - 1,
            "color": "#e8d5f0", "title": "Reconstruction Stage", "tick_color": "#5a3270",
        })

    # ── End-of-life stage ──────────────────────────────────────────────────
    eol_start = len(values)
    values += [
        M(_get(results, "end_of_life", "economic",     "total_demolition_and_disposal_costs")),
        M(_get(results, "end_of_life", "environmental","carbon_costs_demolition_and_disposal")),
        M(_get(results, "end_of_life", "environmental","demolition_vehicular_emission_cost")),
        M(_get(results, "end_of_life", "social",       "ruc_demolition")),
        -M(_get(results, "end_of_life", "economic",    "total_scrap_value")),
    ]
    labels += [
        "Demolition & disposal cost",
        "Demolition carbon cost",
        "Vehicular emission (demolition)",
        "Road user cost (demolition)",
        "Scrap value credit",
    ]
    stage_info.append({
        "start": eol_start, "end": len(values) - 1,
        "color": "#edd5d5", "title": "End-of-Life Stage", "tick_color": "#7a3b3b",
    })

    return values, labels, stage_info


def _create_figure(values, labels, stage_info, text_color, bg_color):
    """Build and return (fig, bars) from pre-computed chart data."""
    _N = len(labels)
    x = np.arange(_N)

    fig_width = max(14, _N * 0.65)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.tick_params(colors=text_color)
    ax.yaxis.label.set_color(text_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(text_color)

    # Stage panels
    for stage in stage_info:
        ax.axvspan(stage["start"] - 0.5, stage["end"] + 0.5,
                   color=stage["color"], alpha=0.9)

    # Bars
    bar_colors = ["#8b1a1a" if v >= 0 else "#2e7d32" for v in values]
    bars = ax.bar(x, values, 0.50, color=bar_colors)

    # Stage dividers and titles
    for stage in stage_info[1:]:
        ax.axvline(stage["start"] - 0.5, color="black", linewidth=1.5)
    ax.axhline(0, color="black", linewidth=0.8)

    for stage in stage_info:
        center = (stage["start"] + stage["end"]) / 2
        ax.text(center, 1.02, stage["title"],
                transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=8, fontweight="bold",
                color=text_color)

    # Y limits and bar value labels
    ylim_top = max(max(values) * 1.3, 1.0)
    ylim_bot = min(min(values) * 1.3, -0.5)
    ax.set_ylim(ylim_bot, ylim_top)

    for bar, val in zip(bars, values):
        lbl = sci_label(val) if abs(val) < 0.1 else f"{val:.2f}"
        y_pos = val + ylim_top * 0.02 if val >= 0 else val - ylim_top * 0.05
        ax.text(
            bar.get_x() + bar.get_width() / 2, y_pos, lbl,
            ha="center", va="bottom" if val >= 0 else "top",
            rotation=90, fontsize=7, color=bar.get_facecolor(),
        )

    # Axes styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(x)

    # Wrap labels for x-axis (two lines)
    wrapped = [lbl.replace(" (", "\n(") if len(lbl) > 22 else lbl for lbl in labels]
    ax.set_xticklabels(wrapped, rotation=90, fontsize=6, color=text_color)
    ax.set_ylabel("Cost (Million INR)", fontsize=8, color=text_color)
    ax.tick_params(axis='y', labelsize=7, colors=text_color)
    ax.tick_params(axis='x', colors=text_color)
    ax.axhline(0, color=text_color, linewidth=0.8)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_xlim(-0.5, _N - 0.5)

    tick_color_map = {i: s["tick_color"] for s in stage_info for i in range(s["start"], s["end"] + 1)}
    for i, lbl in enumerate(ax.get_xticklabels()):
        lbl.set_color(tick_color_map.get(i, text_color))

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.40, top=0.88)
    return fig, bars


# ---------------------------------------------------------------------------
# Public widget
# ---------------------------------------------------------------------------

class LCCChartWidget(QWidget):
    """
    Interactive LCC bar chart widget.
    Includes a navigation toolbar (zoom / pan / save) and hover tooltips.
    """

    def __init__(self, results: dict, parent=None):
        super().__init__(parent)

        palette = QApplication.instance().palette()
        text_color = palette.windowText().color().name()
        bg_color   = palette.window().color().name()

        self._values, self._labels, stage_info = _build_chart_data(results)
        fig, self._bars = _create_figure(
            self._values, self._labels, stage_info, text_color, bg_color
        )

        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setMinimumHeight(480)
        toolbar = NavigationToolbar2QT(self._canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(toolbar)
        layout.addWidget(self._canvas)

        # ── Hover annotation ──────────────────────────────────────────────
        ax = fig.axes[0]
        self._annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc=bg_color,
                ec="#aaaaaa",
                alpha=0.95,
                linewidth=1,
            ),
            fontsize=8,
            color=text_color,
            zorder=10,
        )
        self._annot.set_visible(False)

        self._canvas.mpl_connect("motion_notify_event", self._on_hover)
        self._canvas.mpl_connect("axes_leave_event",    self._on_leave)

    # ── Hover handlers ────────────────────────────────────────────────────

    def _on_hover(self, event):
        if event.inaxes is None:
            self._set_annot_visible(False)
            return

        for bar, label, val in zip(self._bars, self._labels, self._values):
            if bar.contains(event)[0]:
                x = bar.get_x() + bar.get_width() / 2
                self._annot.xy = (x, val)
                inr = val * 1_000_000
                sign = "−" if val < 0 else ""
                self._annot.set_text(
                    f"{label}\n"
                    f"₹ {sign}{abs(inr):,.0f}\n"
                    f"({sign}{abs(val):.4f} M INR)"
                )
                self._set_annot_visible(True)
                return

        self._set_annot_visible(False)

    def _on_leave(self, event):
        self._set_annot_visible(False)

    def _set_annot_visible(self, visible: bool):
        if self._annot.get_visible() != visible:
            self._annot.set_visible(visible)
            self._canvas.draw_idle()


# Keep backward-compatible alias for any existing call sites
def create_lcc_figure(results: dict):
    palette = QApplication.instance().palette()
    text_color = palette.windowText().color().name()
    bg_color   = palette.window().color().name()
    values, labels, stage_info = _build_chart_data(results)
    fig, _ = _create_figure(values, labels, stage_info, text_color, bg_color)
    return fig
