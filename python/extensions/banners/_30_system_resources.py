from python.helpers.extension import Extension
import os
import psutil


class SystemResourcesCheck(Extension):
    async def execute(self, banners: list = [], frontend_context: dict = {}, **kwargs):
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu_percent = None

        try:
            cpu_cores = psutil.cpu_count(logical=True)
        except Exception:
            cpu_cores = None

        load_avg = self._get_load_average()

        try:
            vm = psutil.virtual_memory()
            ram_percent = vm.percent
            ram_used_gb = (vm.total - vm.available) / (1024 ** 3)
            ram_total_gb = vm.total / (1024 ** 3)
        except Exception:
            ram_percent = None

            ram_used_gb = None
            ram_total_gb = None

        disk_percent, disk_used_gb, disk_total_gb, disk_path = self._get_disk_usage()

        try:
            net = psutil.net_io_counters()
            net_sent = self._format_bytes(net.bytes_sent)
            net_recv = self._format_bytes(net.bytes_recv)
        except Exception:
            net_sent = "N/A"
            net_recv = "N/A"

        load_value = "N/A"
        if load_avg:
            la1, la5, la15 = load_avg
            load_value = f"{la1:.2f} / {la5:.2f} / {la15:.2f}"

        if disk_percent is None or disk_used_gb is None or disk_total_gb is None:
            disk_value = "N/A"
        else:
            disk_value = f"{disk_used_gb:.2f}/{disk_total_gb:.2f} GB"

        if cpu_percent is None:
            cpu_value = "N/A"
        else:
            cores_value = "" if cpu_cores is None else f" ({cpu_cores} cores)"
            cpu_value = f"{cpu_percent:.0f}%{cores_value}"

        if ram_percent is None or ram_used_gb is None or ram_total_gb is None:
            ram_value = "N/A"
        else:
            ram_value = f"{ram_used_gb:.2f}/{ram_total_gb:.2f} GB"

        cpu_bar = self._bar_html(cpu_percent)
        ram_bar = self._bar_html(ram_percent)
        disk_bar = self._bar_html(disk_percent)

        banners.append({
            "id": "system-resources",
            "type": "info",
            "priority": 10,
            "title": "System Resources",
            "html": (
                "<div style=\"display:flex;flex-direction:column;gap:14px;padding-top:6px;\">"
                "<div style=\"display:flex;flex-direction:column;gap:12px;\">"
                "<div style=\"display:flex;flex-wrap:wrap;column-gap:12px;row-gap:10px;align-items:center;\">"
                "<div style=\"flex:0 1 140px;min-width:110px;display:flex;flex-direction:column;gap:6px;\">"
                "<div style=\"font-size:12px;letter-spacing:.10em;text-transform:uppercase;opacity:.65;line-height:1.1\">CPU</div>"
                f"<div style=\"font-weight:750;font-variant-numeric:tabular-nums;letter-spacing:.02em;line-height:1.1\">{cpu_value}</div>"
                "</div>"
                f"{cpu_bar}"
                "</div>"
                "<div style=\"display:flex;flex-wrap:wrap;column-gap:12px;row-gap:10px;align-items:center;\">"
                "<div style=\"flex:0 1 140px;min-width:110px;display:flex;flex-direction:column;gap:6px;\">"
                "<div style=\"font-size:12px;letter-spacing:.10em;text-transform:uppercase;opacity:.65;line-height:1.1\">RAM</div>"
                f"<div style=\"font-weight:750;font-variant-numeric:tabular-nums;letter-spacing:.02em;line-height:1.1\">{ram_value}</div>"
                "</div>"
                f"{ram_bar}"
                "</div>"
                "<div style=\"display:flex;flex-wrap:wrap;column-gap:12px;row-gap:10px;align-items:center;\">"
                "<div style=\"flex:0 1 140px;min-width:110px;display:flex;flex-direction:column;gap:6px;\">"
                "<div style=\"font-size:12px;letter-spacing:.10em;text-transform:uppercase;opacity:.65;line-height:1.1\">Disk</div>"
                f"<div style=\"font-weight:750;font-variant-numeric:tabular-nums;letter-spacing:.02em;line-height:1.1\">{disk_value}</div>"
                "</div>"
                f"{disk_bar}"
                "</div>"
                "</div>"
                "<div style=\"height:1px;background:rgba(255,255,255,.08);\"></div>"
                "<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:10px 14px;\">"
                f"<div><div style=\"font-size:12px;letter-spacing:.10em;text-transform:uppercase;opacity:.65;margin-bottom:6px;\">Load (1/5/15)</div><div style=\"font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;opacity:.85;font-variant-numeric:tabular-nums\">{load_value}</div></div>"
                f"<div><div style=\"font-size:12px;letter-spacing:.10em;text-transform:uppercase;opacity:.65;margin-bottom:6px;\">Net (since boot)</div><div style=\"font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;opacity:.85;font-variant-numeric:tabular-nums\">{net_sent} sent / {net_recv} recv</div></div>"
                "</div>"
                "</div>"
            ),
            "dismissible": True,
            "source": "backend",
        })

    def _bar_html(self, percent: float | None) -> str:
        if percent is None:
            return ""

        p = max(0.0, min(100.0, float(percent)))
        if p >= 85:
            color = "#ef4444"
        elif p >= 70:
            color = "#f59e0b"
        else:
            color = "#22c55e"

        return (
            "<div style=\"flex:1 1 220px;width:100%;max-width:260px;height:10px;border-radius:999px;"
            "background:rgba(255,255,255,.10);overflow:hidden;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08);\">"
            f"<div style=\"height:100%;width:{p:.0f}%;background:{color};border-radius:999px;\"></div>"
            "</div>"
        )

    def _get_load_average(self) -> tuple[float, float, float] | None:
        try:
            return os.getloadavg()
        except Exception:
            return None

    def _get_disk_usage(self) -> tuple[float | None, float | None, float | None, str]:
        for path in ["/", os.path.expanduser("~")]:
            try:
                usage = psutil.disk_usage(path)
                used_gb = usage.used / (1024 ** 3)
                total_gb = usage.total / (1024 ** 3)
                return usage.percent, used_gb, total_gb, path
            except Exception:
                continue
        return None, None, None, "/"

    def _format_bytes(self, value: int) -> str:
        size = float(value)
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} EB"
