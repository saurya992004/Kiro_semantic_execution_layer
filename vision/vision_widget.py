"""
Vision Intelligence — Stylish input widget.
Type a query (e.g. "What's on my screen?"), capture & analyze, view JSON output.
"""

import json
import threading
import webbrowser
from pathlib import Path

import customtkinter as ctk

try:
    from .vision_engine import run_vision_pipeline, VISION_OUTPUT_DIR
except ImportError:
    from vision_engine import run_vision_pipeline, VISION_OUTPUT_DIR

# Theme: dark, modern
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_FAMILY = "Segoe UI"
TITLE_FONT = (FONT_FAMILY, 22, "bold")
LABEL_FONT = (FONT_FAMILY, 11)
MONO_FONT = ("Cascadia Code", 10) or ("Consolas", 10)


def _run_pipeline(query: str, on_start, on_done, on_error):
    def run():
        on_start()
        try:
            out = run_vision_pipeline(user_query=query or "What is on my screen? List all buttons and options.")
            on_done(out)
        except Exception as e:
            on_error(str(e))

    threading.Thread(target=run, daemon=True).start()


def _format_result(data: dict) -> str:
    """Pretty-print result for display (no full JSON dump)."""
    if data.get("success"):
        a = data.get("analysis", {})
        lines = [
            "✓ Screen captured and analyzed.",
            "",
            "📁 Screenshot: " + data.get("screenshot_path", ""),
            "📄 JSON: " + data.get("json_path", ""),
            "",
            "--- Summary ---",
            a.get("screen_summary", "—"),
            "",
            "--- Buttons ---",
        ]
        for b in a.get("detected_buttons", [])[:20]:
            lines.append(f"  • {b.get('label', '')} — {b.get('action_hint', '')}")
        if not a.get("detected_buttons"):
            lines.append("  (none detected)")
        lines.extend(["", "--- Options ---"])
        for o in a.get("detected_options", [])[:20]:
            lines.append(f"  • [{o.get('type', '')}] {o.get('label', '')}")
        if not a.get("detected_options"):
            lines.append("  (none detected)")
        lines.append("")
        lines.append("(Full JSON saved to vision_output/.)")
        return "\n".join(lines)
    else:
        return json.dumps(data, indent=2, ensure_ascii=False)


class VisionWidget(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jarvis — Vision Intelligence")
        self.geometry("720x580")
        self.minsize(560, 420)

        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(
            header,
            text="👁 Vision Intelligence",
            font=TITLE_FONT,
            text_color="#e0e0e0",
        )
        title.grid(row=0, column=0, sticky="w")
        subtitle = ctk.CTkLabel(
            header,
            text="Describe what you want to know about your screen, then capture & analyze.",
            font=LABEL_FONT,
            text_color="#888",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Input row
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, padx=24, pady=12, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="e.g. What's on my screen? List all buttons and options.",
            height=44,
            font=(FONT_FAMILY, 13),
            corner_radius=10,
            border_width=1,
            fg_color="#2b2b2b",
            border_color="#444",
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._on_analyze())

        self.btn_analyze = ctk.CTkButton(
            input_frame,
            text="Capture & Analyze",
            height=44,
            font=(FONT_FAMILY, 12, "bold"),
            corner_radius=10,
            fg_color="#0d7377",
            hover_color="#0a5c5f",
            command=self._on_analyze,
        )
        self.btn_analyze.grid(row=0, column=1)

        # Result area
        result_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=12, border_width=1, border_color="#333")
        result_frame.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="nsew")
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_rowconfigure(1, weight=1)

        result_header = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_header.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        result_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_header,
            text="Output (JSON)",
            font=(FONT_FAMILY, 12, "bold"),
            text_color="#aaa",
        ).grid(row=0, column=0, sticky="w")
        self.btn_open_folder = ctk.CTkButton(
            result_header,
            text="Open output folder",
            width=140,
            height=28,
            font=LABEL_FONT,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="#444",
            hover_color="#2b2b2b",
            command=self._open_output_folder,
        )
        self.btn_open_folder.grid(row=0, column=1)

        self.text_output = ctk.CTkTextbox(
            result_frame,
            font=MONO_FONT,
            corner_radius=8,
            fg_color="#0d0d0d",
            border_width=0,
            wrap="word",
        )
        self.text_output.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.text_output.insert("1.0", "Enter a query and click Capture & Analyze. Results and JSON will appear here.")
        self.text_output.configure(state="disabled")

        # Status
        self.status = ctk.CTkLabel(
            self,
            text="Ready",
            font=LABEL_FONT,
            text_color="#666",
        )
        self.status.grid(row=3, column=0, padx=24, pady=(0, 16), sticky="w")

    def _on_analyze(self):
        query = (self.entry.get() or "").strip()
        self.btn_analyze.configure(state="disabled", text="…")
        self._set_status("Hiding window, then capturing…")

        def on_start():
            self.after(0, lambda: self._set_status("Analyzing with Vision API…"))

        def on_done(out):
            self.after(0, self.deiconify)
            self.after(0, lambda: self._show_result(out))

        def on_error(err):
            self.after(0, self.deiconify)
            self.after(0, lambda: self._show_error(err))

        # Minimize so this window is NOT in the screenshot, then run pipeline after short delay
        self.iconify()
        self.after(450, lambda: _run_pipeline(query, on_start, on_done, on_error))

    def _set_status(self, msg: str):
        self.status.configure(text=msg)

    def _show_result(self, data: dict):
        self.btn_analyze.configure(state="normal", text="Capture & Analyze")
        self._set_status("Done. Output saved to vision_output/")
        self.text_output.configure(state="normal")
        self.text_output.delete("1.0", "end")
        self.text_output.insert("1.0", _format_result(data))
        self.text_output.configure(state="disabled")

    def _show_error(self, err: str):
        self.btn_analyze.configure(state="normal", text="Capture & Analyze")
        self._set_status(f"Error: {err}")
        self.text_output.configure(state="normal")
        self.text_output.delete("1.0", "end")
        self.text_output.insert("1.0", f"Error:\n{err}")
        self.text_output.configure(state="disabled")

    def _open_output_folder(self):
        import os
        path = Path(VISION_OUTPUT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(path))
        else:
            webbrowser.open(f"file://{path}")


def main():
    app = VisionWidget()
    app.mainloop()


if __name__ == "__main__":
    main()
