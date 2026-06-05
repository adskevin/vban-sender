import ipaddress
import sys
import tkinter as tk

import customtkinter as ctk

from core.config import (
    DEFAULT_DESKTOP_STREAM,
    DEFAULT_MIC_STREAM,
    DEFAULT_PORT,
    AppConfig,
    load_config,
    save_config,
)
from core.devices import (
    DeviceOption,
    build_grouped_device_options,
    capture_index_for_option,
    combo_values,
    default_desktop_option,
    default_mic_option,
    device_hint,
    resolve_device_option,
)
from core.session import TrackSettings, TransmissionSession

STATUS_STOPPED = ("Parado", "gray")
STATUS_TRANSMITTING = ("Transmitindo {tracks} para {ip}...", "#2ecc71")
STATUS_ERROR = ("Erro: {msg}", "#e74c3c")

TRACK_DESKTOP = "desktop"
TRACK_MIC = "mic"


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("VBAN Sender")
        self.geometry("520x640")
        self.minsize(480, 580)

        self._session: TransmissionSession | None = None
        self._device_options: list[DeviceOption] = []
        self._transmitting = False
        self._levels: dict[str, float] = {TRACK_DESKTOP: 0.0, TRACK_MIC: 0.0}
        self._meter_poll_id: str | None = None

        self._scroll: ctk.CTkScrollableFrame | None = None
        self._build_ui()
        self._load_device_lists()
        self._apply_saved_config()
        self._update_track_controls_state()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 4}
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self._scroll = scroll

        ctk.CTkLabel(scroll, text="IP do receptor", anchor="w").pack(fill="x", **pad)
        self._ip_entry = ctk.CTkEntry(scroll, placeholder_text="192.168.1.100")
        self._ip_entry.pack(fill="x", padx=16, pady=(0, 8))

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row, text="Porta UDP", anchor="w").pack(side="left")
        self._port_entry = ctk.CTkEntry(row, width=100)
        self._port_entry.insert(0, str(DEFAULT_PORT))
        self._port_entry.pack(side="right")

        self._desktop_frame = self._build_track_section(
            scroll,
            title="Áudio do desktop",
            checkbox_text="Transmitir áudio do desktop",
            stream_default=DEFAULT_DESKTOP_STREAM,
            hint=device_hint(),
        )
        self._mic_frame = self._build_track_section(
            scroll,
            title="Microfone",
            checkbox_text="Transmitir microfone",
            stream_default=DEFAULT_MIC_STREAM,
            hint=device_hint(),
        )

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=16, pady=12)

        self._toggle_btn = ctk.CTkButton(
            footer,
            text="Iniciar",
            command=self._on_toggle,
            fg_color="#27ae60",
            hover_color="#219a52",
        )
        self._toggle_btn.pack(pady=(0, 8))

        self._status_label = ctk.CTkLabel(
            footer, text=STATUS_STOPPED[0], text_color=STATUS_STOPPED[1]
        )
        self._status_label.pack()

        self._setup_mousewheel_scroll()

    def _scroll_delta(self, event: tk.Event) -> int:
        if event.num == 5:
            return 1
        if event.num == 4:
            return -1
        if not event.delta:
            return 0
        if sys.platform == "darwin":
            return -int(event.delta)
        return -int(event.delta / 120)

    def _on_mousewheel_scroll(self, event: tk.Event) -> str | None:
        if self._scroll is None:
            return None
        delta = self._scroll_delta(event)
        if delta:
            self._scroll._parent_canvas.yview_scroll(delta, "units")
        return "break"

    def _bind_mousewheel_recursive(self, widget: tk.Misc) -> None:
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(sequence, self._on_mousewheel_scroll, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _setup_mousewheel_scroll(self) -> None:
        if self._scroll is None:
            return
        self._bind_mousewheel_recursive(self._scroll)
        self._bind_mousewheel_recursive(self._scroll._parent_canvas)
        self._bind_mousewheel_recursive(self._scroll._parent_frame)

    def _build_track_section(
        self,
        parent: ctk.CTkScrollableFrame,
        title: str,
        checkbox_text: str,
        stream_default: str,
        hint: str,
    ) -> dict:
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=8, pady=12)

        ctk.CTkLabel(
            frame, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", padx=12, pady=(12, 4))

        enabled_var = tk.BooleanVar(value=True)
        checkbox = ctk.CTkCheckBox(
            frame,
            text=checkbox_text,
            variable=enabled_var,
            command=self._update_track_controls_state,
        )
        checkbox.pack(anchor="w", padx=12, pady=4)

        ctk.CTkLabel(frame, text="Dispositivo", anchor="w").pack(
            fill="x", padx=12, pady=(8, 2)
        )
        combo = ctk.CTkComboBox(frame, state="readonly", width=400)
        combo.pack(fill="x", padx=12, pady=(0, 4))

        if hint:
            ctk.CTkLabel(
                frame,
                text=hint,
                anchor="w",
                font=ctk.CTkFont(size=11),
                text_color="gray60",
                wraplength=440,
            ).pack(fill="x", padx=12, pady=(0, 4))

        ctk.CTkLabel(frame, text="Nome do stream", anchor="w").pack(
            fill="x", padx=12, pady=(4, 2)
        )
        stream_entry = ctk.CTkEntry(frame)
        stream_entry.insert(0, stream_default)
        stream_entry.pack(fill="x", padx=12, pady=(0, 4))

        ctk.CTkLabel(frame, text="Nível", anchor="w").pack(fill="x", padx=12, pady=(4, 2))
        meter = ctk.CTkProgressBar(frame)
        meter.set(0)
        meter.pack(fill="x", padx=12, pady=(0, 12))

        return {
            "frame": frame,
            "enabled_var": enabled_var,
            "checkbox": checkbox,
            "combo": combo,
            "stream_entry": stream_entry,
            "meter": meter,
        }

    def _load_device_lists(self) -> None:
        try:
            self._device_options = build_grouped_device_options()
            names = combo_values(self._device_options)

            self._desktop_frame["combo"].configure(values=names)
            self._mic_frame["combo"].configure(values=names)

            default_d = default_desktop_option(self._device_options)
            if default_d and default_d.display_name in names:
                self._desktop_frame["combo"].set(default_d.display_name)
            elif names:
                self._desktop_frame["combo"].set(names[0])

            default_m = default_mic_option(self._device_options)
            if default_m and default_m.display_name in names:
                self._mic_frame["combo"].set(default_m.display_name)
            elif names:
                self._mic_frame["combo"].set(names[0])
        except Exception as exc:
            self._set_status_error(str(exc))

    def _apply_saved_config(self) -> None:
        cfg = load_config()

        if cfg["receiver_ip"]:
            self._ip_entry.delete(0, tk.END)
            self._ip_entry.insert(0, cfg["receiver_ip"])

        self._port_entry.delete(0, tk.END)
        self._port_entry.insert(0, str(cfg["port"]))

        self._apply_track_config(self._desktop_frame, cfg["desktop"])
        self._apply_track_config(self._mic_frame, cfg["mic"])

    def _apply_track_config(self, track_ui: dict, track_cfg: dict) -> None:
        track_ui["enabled_var"].set(track_cfg["enabled"])
        if track_cfg["stream_name"]:
            track_ui["stream_entry"].delete(0, tk.END)
            track_ui["stream_entry"].insert(0, track_cfg["stream_name"])
        values = track_ui["combo"].cget("values")
        if track_cfg["device_name"] and track_cfg["device_name"] in values:
            track_ui["combo"].set(track_cfg["device_name"])

    def _update_track_controls_state(self) -> None:
        if self._transmitting:
            return
        self._set_track_enabled(self._desktop_frame)
        self._set_track_enabled(self._mic_frame)

    def _set_track_enabled(self, track_ui: dict) -> None:
        active = track_ui["enabled_var"].get()
        state = "readonly" if active else "disabled"
        entry_state = "normal" if active else "disabled"
        track_ui["combo"].configure(state=state)
        track_ui["stream_entry"].configure(state=entry_state)

    def _build_config_from_ui(self) -> AppConfig:
        return {
            "receiver_ip": self._ip_entry.get().strip(),
            "port": int(self._port_entry.get().strip()),
            "desktop": {
                "enabled": self._desktop_frame["enabled_var"].get(),
                "device_name": self._desktop_frame["combo"].get(),
                "stream_name": self._desktop_frame["stream_entry"].get().strip(),
            },
            "mic": {
                "enabled": self._mic_frame["enabled_var"].get(),
                "device_name": self._mic_frame["combo"].get(),
                "stream_name": self._mic_frame["stream_entry"].get().strip(),
            },
        }

    def _validate(self) -> tuple[str, int, list[TrackSettings]] | None:
        ip_str = self._ip_entry.get().strip()
        try:
            ipaddress.IPv4Address(ip_str)
        except ipaddress.AddressValueError:
            self._set_status_error("IP inválido (use IPv4)")
            return None

        try:
            port = int(self._port_entry.get().strip())
        except ValueError:
            self._set_status_error("Porta inválida")
            return None
        if not 1 <= port <= 65535:
            self._set_status_error("Porta deve estar entre 1 e 65535")
            return None

        tracks: list[TrackSettings] = []
        stream_names: list[str] = []

        if self._desktop_frame["enabled_var"].get():
            result = self._validate_track(
                self._desktop_frame,
                "Áudio do desktop",
                TRACK_DESKTOP,
            )
            if result is None:
                return None
            tracks.append(result)
            stream_names.append(result.stream_name)

        if self._mic_frame["enabled_var"].get():
            result = self._validate_track(
                self._mic_frame,
                "Microfone",
                TRACK_MIC,
            )
            if result is None:
                return None
            if result.stream_name in stream_names:
                self._set_status_error("Os nomes de stream devem ser diferentes")
                return None
            tracks.append(result)
            stream_names.append(result.stream_name)

        if not tracks:
            self._set_status_error("Ative pelo menos uma faixa para transmitir")
            return None

        return ip_str, port, tracks

    def _validate_track(
        self,
        track_ui: dict,
        label: str,
        track_id: str,
    ) -> TrackSettings | None:
        stream = track_ui["stream_entry"].get().strip()
        if not stream:
            self._set_status_error(f"{label}: nome do stream é obrigatório")
            return None

        display_name = track_ui["combo"].get()
        option = resolve_device_option(display_name, self._device_options)
        if option is None or option.is_separator:
            self._set_status_error(f"{label}: selecione um dispositivo válido")
            return None

        try:
            capture_index = capture_index_for_option(option)
        except ValueError as exc:
            self._set_status_error(f"{label}: {exc}")
            return None

        return TrackSettings(
            enabled=True,
            device_index=capture_index,
            device_kind=option.kind,
            stream_name=stream[:16],
            label=label,
            track_id=track_id,
        )

    def _on_toggle(self) -> None:
        if self._transmitting:
            self._stop_transmission()
        else:
            self._start_transmission()

    def _start_transmission(self) -> None:
        validated = self._validate()
        if validated is None:
            return

        ip_str, port, tracks = validated

        self._session = TransmissionSession(
            receiver_ip=ip_str,
            receiver_port=port,
            tracks=tracks,
            on_error=self._on_session_error,
            on_level=self._on_session_level,
        )
        self._session.start()
        self._transmitting = True

        self._toggle_btn.configure(
            text="Parar",
            fg_color="#c0392b",
            hover_color="#a93226",
        )
        track_labels = " + ".join(t.stream_name for t in tracks)
        self._set_status_transmitting(ip_str, track_labels)
        self._set_inputs_state(disabled=True)

        save_config(self._build_config_from_ui())
        self._start_meter_poll()

    def _stop_transmission(self) -> None:
        self._stop_meter_poll()
        if self._session is not None:
            self._session.stop()
            self._session = None
        self._transmitting = False
        self._toggle_btn.configure(
            text="Iniciar",
            fg_color="#27ae60",
            hover_color="#219a52",
        )
        self._set_status_stopped()
        self._set_inputs_state(disabled=False)
        self._desktop_frame["meter"].set(0)
        self._mic_frame["meter"].set(0)
        self._update_track_controls_state()

    def _set_inputs_state(self, disabled: bool) -> None:
        state = "disabled" if disabled else "normal"
        self._ip_entry.configure(state=state)
        self._port_entry.configure(state=state)
        cb_state = "disabled" if disabled else "normal"
        self._desktop_frame["checkbox"].configure(state=cb_state)
        self._mic_frame["checkbox"].configure(state=cb_state)
        if disabled:
            self._desktop_frame["combo"].configure(state="disabled")
            self._desktop_frame["stream_entry"].configure(state="disabled")
            self._mic_frame["combo"].configure(state="disabled")
            self._mic_frame["stream_entry"].configure(state="disabled")
        else:
            self._update_track_controls_state()

    def _set_status_stopped(self) -> None:
        self._status_label.configure(
            text=STATUS_STOPPED[0], text_color=STATUS_STOPPED[1]
        )

    def _set_status_transmitting(self, ip: str, tracks: str) -> None:
        text = STATUS_TRANSMITTING[0].format(tracks=tracks, ip=ip)
        self._status_label.configure(
            text=text, text_color=STATUS_TRANSMITTING[1]
        )

    def _set_status_error(self, msg: str) -> None:
        text = STATUS_ERROR[0].format(msg=msg)
        self._status_label.configure(text=text, text_color=STATUS_ERROR[1])

    def _on_session_error(self, track_id: str, msg: str) -> None:
        self.after(0, lambda m=msg: self._handle_session_error(m))

    def _handle_session_error(self, msg: str) -> None:
        if self._transmitting:
            self._stop_transmission()
        self._set_status_error(msg)

    def _on_session_level(self, track_id: str, level: float) -> None:
        self._levels[track_id] = level

    def _start_meter_poll(self) -> None:
        self._stop_meter_poll()
        self._poll_meters()

    def _stop_meter_poll(self) -> None:
        if self._meter_poll_id is not None:
            self.after_cancel(self._meter_poll_id)
            self._meter_poll_id = None

    def _poll_meters(self) -> None:
        if not self._transmitting:
            return
        self._set_meter(TRACK_DESKTOP, self._levels.get(TRACK_DESKTOP, 0.0))
        self._set_meter(TRACK_MIC, self._levels.get(TRACK_MIC, 0.0))
        self._meter_poll_id = self.after(33, self._poll_meters)

    def _set_meter(self, track_id: str, level: float) -> None:
        if track_id == TRACK_DESKTOP:
            self._desktop_frame["meter"].set(level)
        elif track_id == TRACK_MIC:
            self._mic_frame["meter"].set(level)

    def _on_close(self) -> None:
        self._stop_transmission()
        self.destroy()


if __name__ == "__main__":
    MainWindow().mainloop()
