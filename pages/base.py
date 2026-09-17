"""Base page class with shared helper methods for all preference pages."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class BasePage(Adw.PreferencesPage):
    """Abstract base for every settings page.

    Provides helper methods to create Adw rows and wire them up to a
    change-notification callback so the command preview stays in sync.
    """

    def __init__(self, title: str, icon_name: str, on_changed=None):
        super().__init__(title=title, icon_name=icon_name)
        self._on_changed = on_changed

    # ------------------------------------------------------------------
    # Change notification
    # ------------------------------------------------------------------

    def _notify(self, *_args):
        """Called whenever any widget value changes."""
        if self._on_changed:
            self._on_changed()

    # ------------------------------------------------------------------
    # Widget factories
    # ------------------------------------------------------------------

    def _add_group(self, title: str, description: str = "") -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=title)
        if description:
            group.set_description(description)
        self.add(group)
        return group

    def _add_switch(
        self, group: Adw.PreferencesGroup, title: str, subtitle: str = ""
    ) -> Adw.SwitchRow:
        row = Adw.SwitchRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        row.connect("notify::active", self._notify)
        group.add(row)
        return row

    def _add_entry(
        self, group: Adw.PreferencesGroup, title: str
    ) -> Adw.EntryRow:
        row = Adw.EntryRow(title=title)
        row.connect("changed", self._notify)
        group.add(row)
        return row

    def _add_combo(
        self,
        group: Adw.PreferencesGroup,
        title: str,
        options: list[tuple[str, str | None]],
        subtitle: str = "",
    ) -> Adw.ComboRow:
        """Create an ``Adw.ComboRow``.

        *options* is a list of ``(display_name, flag_value | None)``.
        When *flag_value* is ``None`` the option is treated as "default /
        no flag".
        """
        row = Adw.ComboRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        model = Gtk.StringList.new([name for name, _ in options])
        row.set_model(model)
        row.connect("notify::selected", self._notify)
        # Stash the mapping so get_args() can look it up later.
        row._flag_options = options  # noqa: SLF001
        group.add(row)
        return row

    # ------------------------------------------------------------------
    # Value helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _combo_val(combo: Adw.ComboRow) -> str | None:
        """Return the selected flag value, or ``None`` if default."""
        idx = combo.get_selected()
        opts = combo._flag_options  # noqa: SLF001
        if idx < len(opts):
            return opts[idx][1]
        return None

    @staticmethod
    def _entry_val(entry: Adw.EntryRow) -> str:
        return entry.get_text().strip()

    # ------------------------------------------------------------------
    # Interface (subclasses must implement)
    # ------------------------------------------------------------------

    def get_args(self) -> list[str]:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError
