#!/usr/bin/env python3
"""
DashDAQ log viewer with:
- Light/Dark mode toggle
- Time range selection
- Overlay / separate subplots
- Units from CSV

Usage:
    python dashdaq_viewer.py
"""

import io
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------- Data loading / parsing ----------

def load_dashdaq_csv(csv_path: Path):
    """
    Load a DashDAQ CSV file and return:
        - df: cleaned DataFrame with numeric columns
        - units: dict mapping column name -> unit string (if available)

    Handles:
    - Header metadata lines
    - Units row (first row after "Time" header)
    - Variable number of signals
    - Trailing empty columns
    """
    with csv_path.open("r", encoding="latin1") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('"Time"'):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError('Could not find a header line starting with "Time" in the CSV.')

    data_str = "".join(lines[header_idx:])
    df = pd.read_csv(io.StringIO(data_str))

    # Drop any extra unnamed columns from trailing commas
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Capture units row (first row after header)
    units = {}
    if "Time" in df.columns:
        units = {col: str(df.loc[0, col]) for col in df.columns}
        df = df.iloc[1:].reset_index(drop=True)

    # Convert all columns to numeric where possible
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Time in seconds relative to start
    if "Time" in df.columns:
        t = df["Time"].astype(float)
        df["Time_s"] = (t - t.min()) / 1000.0
        units["Time_s"] = "s"

    return df, units


# ---------- GUI Application ----------

class DashDAQViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        # Theme state
        self.dark_mode = True
        self._set_theme_colors()

        self.title("DashDAQ Log Viewer")
        self.geometry("1150x680")
        self.configure(bg=self.bg_color)

        # Data
        self.df = None
        self.units = {}
        self.signal_names = []

        # Plot mode: "overlay" or "subplots"
        self.plot_mode = tk.StringVar(value="subplots")

        # Time-range variables
        self.time_start_var = tk.StringVar()
        self.time_end_var = tk.StringVar()

        # Keep references to key widgets for theme updates
        self.left_frame = None
        self.signal_listbox = None
        self.mode_frame = None
        self.rb_subplots = None
        self.rb_overlay = None
        self.tr_frame = None
        self.entry_start = None
        self.entry_end = None
        self.lbl_tr_note = None
        self.btn_plot = None
        self.btn_full = None
        self.btn_clear = None

        # Matplotlib figure / canvas
        self.fig = None
        self.ax = None
        self.canvas = None

        # Build UI
        self._build_menu()
        self._build_main_ui()

    # ---------- Theme handling ----------

    def _set_theme_colors(self):
        """Set palette based on self.dark_mode."""
        if self.dark_mode:
            # Dark theme
            self.bg_color = "#121212"
            self.panel_color = "#1e1e1e"
            self.text_color = "#f5f5f5"
            self.grid_color = "#333333"
            self.accent_color = "#1f6feb"
        else:
            # Light theme
            self.bg_color = "#f0f0f0"
            self.panel_color = "#ffffff"
            self.text_color = "#000000"
            self.grid_color = "#cccccc"
            self.accent_color = "#1976d2"

    def toggle_dark_mode(self):
        """Toggle theme and restyle widgets + plot."""
        self.dark_mode = not self.dark_mode
        self._set_theme_colors()
        self.configure(bg=self.bg_color)

        # Update main frames / widgets colors
        if self.left_frame is not None:
            self.left_frame.configure(bg=self.bg_color)

        for widget in [
            self.mode_frame,
            self.tr_frame,
        ]:
            if widget is not None:
                widget.configure(bg=self.bg_color, fg=self.text_color)

        if self.signal_listbox is not None:
            self.signal_listbox.configure(
                bg=self.panel_color,
                fg=self.text_color,
                highlightbackground=self.grid_color,
                selectbackground=self.accent_color,
                selectforeground="white" if self.dark_mode else "white",
            )

        for entry in [self.entry_start, self.entry_end]:
            if entry is not None:
                entry.configure(
                    bg=self.panel_color,
                    fg=self.text_color,
                    insertbackground=self.text_color,
                )

        for btn in [self.btn_plot, self.btn_full, self.btn_clear]:
            if btn is not None:
                if btn is self.btn_plot:
                    btn.configure(
                        bg=self.accent_color,
                        fg="white",
                        activebackground=self.accent_color,
                        activeforeground="white",
                    )
                else:
                    btn.configure(
                        bg=self.panel_color,
                        fg=self.text_color,
                        activebackground=self.panel_color,
                        activeforeground=self.text_color,
                    )

        if self.lbl_tr_note is not None:
            self.lbl_tr_note.configure(
                bg=self.bg_color,
                fg="#aaaaaa" if self.dark_mode else "#555555",
            )

        if self.rb_subplots is not None:
            self.rb_subplots.configure(
                bg=self.bg_color,
                fg=self.text_color,
                activebackground=self.bg_color,
                activeforeground=self.text_color,
                selectcolor=self.bg_color,
            )
        if self.rb_overlay is not None:
            self.rb_overlay.configure(
                bg=self.bg_color,
                fg=self.text_color,
                activebackground=self.bg_color,
                activeforeground=self.text_color,
                selectcolor=self.bg_color,
            )

        # Restyle current figure
        if self.fig is not None and self.ax is not None:
            title = self.ax.get_title()
            xlabel = self.ax.get_xlabel()
            ylabel = self.ax.get_ylabel()
            self._style_figure(self.fig, self.ax, title, xlabel, ylabel)
            self.canvas.draw()

    # ---------- UI building ----------

    def _build_menu(self):
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open CSV…", command=self.open_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View menu with dark mode toggle
        view_menu = tk.Menu(menubar, tearoff=0)
        self.dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        view_menu.add_checkbutton(
            label="Dark mode",
            onvalue=True,
            offvalue=False,
            variable=self.dark_mode_var,
            command=self.toggle_dark_mode,
        )
        menubar.add_cascade(label="View", menu=view_menu)

        self.config(menu=menubar)

    def _build_main_ui(self):
        # Left panel: list of signals + plot controls
        self.left_frame = tk.Frame(self, bg=self.bg_color)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        lbl = tk.Label(
            self.left_frame,
            text="Signals (Ctrl+click / Shift+click to select multiple):",
            bg=self.bg_color,
            fg=self.text_color,
        )
        lbl.pack(anchor="w")

        self.signal_listbox = tk.Listbox(
            self.left_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            width=30,
            height=20,
            bg=self.panel_color,
            fg=self.text_color,
            highlightbackground=self.grid_color,
            selectbackground=self.accent_color,
            selectforeground="white",
        )
        self.signal_listbox.pack(fill=tk.Y, expand=False)

        # Plot mode controls
        self.mode_frame = tk.LabelFrame(
            self.left_frame,
            text="Plot mode",
            bg=self.bg_color,
            fg=self.text_color,
            labelanchor="n",
        )
        self.mode_frame.pack(fill=tk.X, pady=5)

        self.rb_subplots = tk.Radiobutton(
            self.mode_frame,
            text="Separate subplots",
            variable=self.plot_mode,
            value="subplots",
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            selectcolor=self.bg_color,
        )
        self.rb_subplots.pack(anchor="w")

        self.rb_overlay = tk.Radiobutton(
            self.mode_frame,
            text="Overlay (same axis)",
            variable=self.plot_mode,
            value="overlay",
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            selectcolor=self.bg_color,
        )
        self.rb_overlay.pack(anchor="w")

        # Time range selector
        self.tr_frame = tk.LabelFrame(
            self.left_frame,
            text="Time range",
            bg=self.bg_color,
            fg=self.text_color,
            labelanchor="n",
        )
        self.tr_frame.pack(fill=tk.X, pady=5)

        lbl_start = tk.Label(self.tr_frame, text="Start:", bg=self.bg_color, fg=self.text_color)
        lbl_start.grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.entry_start = tk.Entry(
            self.tr_frame,
            textvariable=self.time_start_var,
            bg=self.panel_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            width=10,
        )
        self.entry_start.grid(row=0, column=1, sticky="w", padx=2, pady=2)

        lbl_end = tk.Label(self.tr_frame, text="End:", bg=self.bg_color, fg=self.text_color)
        lbl_end.grid(row=1, column=0, sticky="w", padx=2, pady=2)
        self.entry_end = tk.Entry(
            self.tr_frame,
            textvariable=self.time_end_var,
            bg=self.panel_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            width=10,
        )
        self.entry_end.grid(row=1, column=1, sticky="w", padx=2, pady=2)

        self.lbl_tr_note = tk.Label(
            self.tr_frame,
            text="(Units match x-axis, usually seconds)",
            bg=self.bg_color,
            fg="#aaaaaa" if self.dark_mode else "#555555",
            font=("TkDefaultFont", 8),
        )
        self.lbl_tr_note.grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=2)

        # Buttons
        self.btn_plot = tk.Button(
            self.left_frame,
            text="Apply range + Plot selected",
            command=self.plot_selected,
            bg=self.accent_color,
            fg="white",
            activebackground=self.accent_color,
            activeforeground="white",
            relief=tk.FLAT,
        )
        self.btn_plot.pack(fill=tk.X, pady=5)

        self.btn_full = tk.Button(
            self.left_frame,
            text="Full range (reset time)",
            command=self.reset_full_time_range,
            bg=self.panel_color,
            fg=self.text_color,
            activebackground=self.panel_color,
            activeforeground=self.text_color,
            relief=tk.FLAT,
        )
        self.btn_full.pack(fill=tk.X, pady=2)

        self.btn_clear = tk.Button(
            self.left_frame,
            text="Clear plot",
            command=self.clear_plot,
            bg=self.panel_color,
            fg=self.text_color,
            activebackground=self.panel_color,
            activeforeground=self.text_color,
            relief=tk.FLAT,
        )
        self.btn_clear.pack(fill=tk.X, pady=8)

        # Right panel: matplotlib figure
        right_frame = tk.Frame(self, bg=self.bg_color)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self._style_figure(self.fig, self.ax, title="Open a CSV and select signals to plot")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ---------- Plot styling helpers ----------

    def _style_figure(self, fig, ax, title=None, xlabel="Time", ylabel="Value"):
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.panel_color)

        ax.tick_params(colors=self.text_color)
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)

        if title is not None:
            ax.set_title(title, color=self.text_color)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        for spine in ax.spines.values():
            spine.set_color(self.text_color)

        ax.grid(True, color=self.grid_color)

    def _style_axes_list(self, axes):
        for ax in axes:
            # Keep current labels and title
            title = ax.get_title()
            xlabel = ax.get_xlabel()
            ylabel = ax.get_ylabel()

            self._style_figure(
                self.fig,
                ax,
                title=title if title else None,
                xlabel=xlabel if xlabel else "Time",
                ylabel=ylabel if ylabel else "Value",
            )


    # ---------- Time helpers ----------

    def _time_column(self):
        if self.df is None:
            return None
        if "Time_s" in self.df.columns:
            return "Time_s"
        if "Time" in self.df.columns:
            return "Time"
        return None

    def _time_label(self):
        t_col = self._time_column()
        if t_col is None:
            return "Time"
        unit = self.units.get(t_col, "")
        if unit and unit.lower() != "nan":
            return f"{t_col} [{unit}]"
        if t_col == "Time_s":
            return "Time (s)"
        if t_col == "Time":
            return "Time (ms)"
        return t_col

    def _y_label_for_signal(self, col_name: str):
        unit = self.units.get(col_name, "")
        if unit and unit.lower() != "nan":
            return f"{col_name} [{unit}]"
        return col_name

    def _init_time_range(self):
        t_col = self._time_column()
        if t_col is None:
            self.time_start_var.set("")
            self.time_end_var.set("")
            return

        t = self.df[t_col].dropna()
        if t.empty:
            self.time_start_var.set("")
            self.time_end_var.set("")
            return

        t_min = float(t.min())
        t_max = float(t.max())
        self.time_start_var.set(f"{t_min:.2f}")
        self.time_end_var.set(f"{t_max:.2f}")

    def reset_full_time_range(self):
        if self.df is None:
            return
        self._init_time_range()

    def _get_time_range(self):
        t_col = self._time_column()
        if t_col is None:
            return None, None

        t = self.df[t_col].dropna()
        if t.empty:
            return None, None

        full_min = float(t.min())
        full_max = float(t.max())

        start_str = self.time_start_var.get().strip()
        end_str = self.time_end_var.get().strip()

        if not start_str or not end_str:
            return full_min, full_max

        try:
            start = float(start_str)
            end = float(end_str)
        except ValueError:
            messagebox.showwarning(
                "Invalid time range",
                "Start/End must be numbers. Using full range instead.",
            )
            return full_min, full_max

        if start > end:
            start, end = end, start

        if end < full_min or start > full_max:
            messagebox.showwarning(
                "Invalid time range",
                "Selected time range is outside the data. Using full range instead.",
            )
            return full_min, full_max

        start = max(start, full_min)
        end = min(end, full_max)
        return start, end

    # ---------- Actions ----------

    def open_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select DashDAQ CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            df, units = load_dashdaq_csv(Path(file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")
            return

        self.df = df
        self.units = units

        # Collect numeric signals except time columns
        time_cols = {"Time", "Time_s"}
        numeric_cols = [
            col for col in df.columns
            if col not in time_cols and pd.api.types.is_numeric_dtype(df[col])
        ]
        self.signal_names = numeric_cols

        # Populate listbox
        self.signal_listbox.delete(0, tk.END)
        for name in self.signal_names:
            self.signal_listbox.insert(tk.END, name)

        # Reset time range + label note
        self._init_time_range()
        t_col = self._time_column()
        if t_col == "Time_s":
            note = "(Units: seconds)"
        elif t_col == "Time":
            note = "(Units: milliseconds)"
        else:
            note = "(Units match x-axis)"
        self.lbl_tr_note.config(text=note)

        # Reset plot
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        time_label = self._time_label()
        self._style_figure(
            self.fig,
            self.ax,
            title=f"Loaded: {Path(file_path).name}",
            xlabel=time_label,
            ylabel="Value",
        )
        self.canvas.draw()

    def plot_selected(self):
        if self.df is None:
            messagebox.showinfo("No data", "Please open a CSV file first.")
            return

        selected_indices = self.signal_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No selection", "Please select one or more signals.")
            return

        time_col = self._time_column()
        if time_col is None:
            messagebox.showerror("Error", "No time column found in data.")
            return

        t_start, t_end = self._get_time_range()
        if t_start is None or t_end is None:
            return

        df_slice = self.df[(self.df[time_col] >= t_start) & (self.df[time_col] <= t_end)]
        if df_slice.empty:
            messagebox.showwarning("Empty range", "No data points in selected time range.")
            return

        mode = self.plot_mode.get()

        if mode == "overlay":
            self.fig.clf()
            ax = self.fig.add_subplot(111)

            for idx in selected_indices:
                col_name = self.signal_names[idx]
                series = df_slice[col_name]
                if series.dropna().empty:
                    continue
                ax.plot(df_slice[time_col], series, label=self._y_label_for_signal(col_name))

            self._style_figure(
                self.fig,
                ax,
                title=None,
                xlabel=self._time_label(),
                ylabel="Value",
            )
            ax.legend()
            ax.set_xlim(t_start, t_end)

            self.ax = ax
            self.canvas.draw()

        else:  # subplots
            n = len(selected_indices)
            self.fig.clf()
            axes = self.fig.subplots(n, 1, sharex=True)
            if n == 1:
                axes = [axes]

            for ax, idx in zip(axes, selected_indices):
                col_name = self.signal_names[idx]
                series = df_slice[col_name]
                if series.dropna().empty:
                    ax.set_visible(False)
                    continue

                ax.plot(df_slice[time_col], series)
                ax.set_ylabel(self._y_label_for_signal(col_name))

            self._style_axes_list(axes)
            axes[-1].set_xlabel(self._time_label())
            axes[-1].set_xlim(t_start, t_end)

            self.fig.tight_layout()
            self.ax = axes[0]
            self.canvas.draw()

    def clear_plot(self):
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self._style_figure(
            self.fig,
            self.ax,
            title="Plot cleared",
            xlabel="Time",
            ylabel="Value",
        )
        self.canvas.draw()


if __name__ == "__main__":
    app = DashDAQViewer()
    app.mainloop()
