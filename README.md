DashDAQ Log Viewer

A simple desktop app to explore and visualize **DashDAQ** logs (e.g. from your Pajero) with:

* ✅ File picker to load any DashDAQ CSV
* ✅ Automatic detection of all logged parameters (works with more / fewer channels)
* ✅ Units-aware axis labels (kph, RPM, °C, kPa, AFR, etc.)
* ✅ Overlay mode *or* separate stacked subplots
* ✅ Time range selector to zoom in on specific pulls
* ✅ Light / Dark mode toggle

Built with **Python**, **Tkinter**, **Pandas**, and **Matplotlib**.

---

## Features

### 🔍 CSV Handling

* Opens standard **DashDAQ CSV exports**.
* Automatically:

  * Skips metadata/header lines.
  * Uses the **first data row as a units row** (e.g. `ms`, `kph`, `RPM`, `°C`, `kpa`).
  * Drops any trailing extra/unnamed columns.
  * Converts all signal columns to numeric where possible.
* Creates a `Time_s` column (seconds relative to log start) for nicer x-axis handling.

### 📈 Plotting

* **Signal selection list** on the left:

  * Use *Ctrl+click* / *Shift+click* to select multiple signals.

* **Two plot modes:**

  * **Separate subplots** (default)
    Each selected signal gets its own subplot, its own y-scale, and its own label with units – ideal for RPM / speed / boost / temps together.
  * **Overlay (same axis)**
    All selected signals on a single axis (useful for signals with similar ranges, e.g. ECT & IAT).

* Y-axis labels are automatically generated from the units row, e.g.

  * `RPM [RPM]`
  * `Speed [kph]`
  * `MAP [kpa]`
  * `ECT [°C]`

### ⏱ Time Range Selector

* Text fields for **Start** and **End** time (in the same units as x-axis, usually seconds).
* Default: full log range.
* Enter a smaller range (e.g. `20` to `45`) to zoom into a specific pull.
* Buttons:

  * **Apply range + Plot selected** – applies the time window and plots the chosen signals.
  * **Full range (reset time)** – restores the full time range of the log.

### 🌗 Light / Dark Mode Toggle

* Menu: **View → Dark mode**

  * Checked = dark theme (good for night use / screenshots).
  * Unchecked = light theme.
* Theme affects:

  * App background and panels
  * Listboxes and buttons
  * Plot background, grid, ticks, labels, and legend

---

## Requirements

* Python **3.8+** (recommended)
* Packages:

  * `pandas`
  * `matplotlib`

Install via:

```bash
pip install pandas matplotlib
```

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. (Optional but recommended) Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate         # macOS / Linux
   # or
   venv\Scripts\activate            # Windows
   ```

3. Install dependencies:

   ```bash
   pip install pandas matplotlib
   ```

---

## Usage

1. Make sure `dashdaq_viewer.py` is in your project directory.

2. Run the app:

   ```bash
   python dashdaq_viewer.py
   ```

3. In the GUI:

   1. Go to **File → Open CSV…**
   2. Select your **DashDAQ log** (e.g. `Pajero_Run1.csv`).
   3. Once loaded:

      * All numeric signals (excluding time) are listed on the left.
      * The time range box is set to cover the full log.

### Plotting Signals

1. In the **Signals** list:

   * Click to select a signal.
   * Use *Ctrl+click* / *Shift+click* to select multiple.

2. Choose **plot mode**:

   * **Separate subplots** (recommended for mixed units like RPM vs speed vs boost).
   * **Overlay (same axis)** (recommended for similar-magnitude signals).

3. Optionally adjust **Time range**:

   * `Start` and `End` will default to the min and max time values.
   * Change them (e.g. to zoom into a specific hill climb or acceleration pull).
   * Units:

     * If `Time_s` is present → seconds.
     * If raw `Time` is used → milliseconds.

4. Click **Apply range + Plot selected** to draw the plots.

5. To reset:

   * Click **Full range (reset time)** to restore entire log time.
   * Click **Clear plot** to blank the figure.

### Light / Dark Mode

* Use **View → Dark mode** to toggle theme.
* The current theme will be applied immediately to:

  * The main window
  * Controls
  * Existing plots

---

## Expected CSV Format

The viewer assumes your CSV looks like a typical **DashDAQ log**:

* Some metadata lines at the top (ignored).
* A header line that starts with `"Time"` and includes all signal names.
* First data row contains **units** for each column.
* Following rows contain numeric data.

Example (simplified):

```csv
"DashDAQ Log File",...
"Time","Speed","RPM","ECT","IAT","MAP"
"ms","kph","RPM","°C","°C","kpa"
0,0,900,85,30,101
100,1,950,85,31,101
...
```

If you add or remove signals in DashDAQ, the app will automatically adapt – it just lists whatever numeric columns are present.

---

## Screenshots (optional)

> *Add screenshots here once you’ve got the app running, e.g.:*
>
> * `docs/screenshot-dark-mode.png`
> * `docs/screenshot-subplots.png`

```markdown
![Dark mode with subplots](docs/screenshot-dark-mode.png)
![Time range zoom](docs/screenshot-time-range.png)
```

---

## Troubleshooting

* **No signals appear after loading CSV**

  * Check that the CSV is a real **DashDAQ export** and that there *is* a header row starting with `"Time"`.
  * Ensure the first row after the header is the units row, not data.

* **Plots are empty for a selected time range**

  * Check your `Start` and `End` values.
  * If they’re outside the data range, the app will warn you and fall back to full range.

* **Window doesn’t open / crashes immediately**

  * Make sure `tkinter` is available (it ships with standard Python on most platforms).
  * Confirm `pandas` and `matplotlib` installed without errors.

---

## Roadmap / Ideas

Potential future enhancements:

* Interactive time-range slider on the plot.
* Saving / exporting selected signals as new CSVs.
* Saving preset “view profiles” (e.g. RPM + Speed + MAP combo).
* Live-tail mode for logs that are growing while driving.

---

## Contributing

Pull requests and suggestions are welcome:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

