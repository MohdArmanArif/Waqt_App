import os
from PyQt6.QtGui import QFont, QFontDatabase


class FontManager:
    """
    Loads custom font files from the local `fonts/` folder and lets you
    request them by family name, weight, and italic style.

    If a font family you ask for wasn't loaded from the `fonts/` folder,
    you'll get back a plain Qt default font — as if you never specified
    a font at all. This prevents Qt from guessing a system font that
    might look completely wrong.

    Usage:
        fm = FontManager()
        label.setFont(fm.get_font("SF Pro Display", 18, weight=700))
    """

    def __init__(self, fonts_folder="fonts"):
        # Get the directory where this Python file lives
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Build full path to the fonts folder (next to this file)
        self.fonts_folder = os.path.join(script_dir, fonts_folder)

        # Set of family names we successfully loaded (e.g. {"SF Pro Display", "SF Mono"})
        # We use this later to check if a requested font is actually available
        self.loaded_families = set()

        # Dictionary mapping family names to a list of style dicts.
        # Example:
        #   {
        #     "SF Pro Display": [
        #       {"style_name": "Bold", "weight": 700, "italic": False, ...},
        #       {"style_name": "Regular", "weight": 400, "italic": False, ...},
        #     ]
        #   }
        self.font_catalog = {}

        # Load all fonts from the folder right away
        self._load_all_fonts()

    def _load_all_fonts(self):
        """
        Scans the fonts folder for .otf and .ttf files, registers each one
        with Qt, and stores metadata about every available style.

        If the folder doesn't exist or is empty, we just end up with an
        empty catalog — all font requests will fall back to the Qt default.
        """

        # If the folder doesn't exist at all, log it and move on
        if not os.path.exists(self.fonts_folder):
            print(f"[FontManager] Fonts folder not found: {self.fonts_folder}")
            print("[FontManager] All font requests will use the Qt default font.")
            return

        # Find all valid font files in the folder
        font_files = [
            f for f in os.listdir(self.fonts_folder)
            if not f.startswith(".")                        # skip hidden files like ._mac files
            and f.lower().endswith((".otf", ".ttf"))        # only real font files
        ]

        if not font_files:
            print(f"[FontManager] No font files found in: {self.fonts_folder}")
            print("[FontManager] All font requests will use the Qt default font.")
            return

        for file_name in font_files:
            file_path = os.path.join(self.fonts_folder, file_name)

            # Register this font file with Qt so it can be used in the app
            font_id = QFontDatabase.addApplicationFont(file_path)

            # Qt returns -1 if the file couldn't be read or isn't a valid font
            if font_id == -1:
                print(f"[FontManager] Failed to load font file: {file_path}")
                continue

            # A single font file can contain multiple families (rare, but possible)
            families = QFontDatabase.applicationFontFamilies(font_id)

            if not families:
                print(f"[FontManager] No font families found in: {file_path}")
                continue

            for family_name in families:

                # Track this family as available
                self.loaded_families.add(family_name)

                # Create a catalog entry for this family if it's the first time we see it
                if family_name not in self.font_catalog:
                    self.font_catalog[family_name] = []

                # Qt knows all the named styles for a family (Regular, Bold, Italic, etc.)
                style_names = QFontDatabase.styles(family_name)

                for style_name in style_names:

                    # Skip if we already recorded this style (can happen when
                    # multiple font files belong to the same family)
                    if self._style_already_recorded(family_name, style_name):
                        continue

                    # Ask Qt to build a font object so we can read its properties
                    font = QFontDatabase.font(family_name, style_name, 12)

                    self.font_catalog[family_name].append({
                        "style_name": style_name,       # e.g. "Bold Italic"
                        "weight": int(font.weight()),   # numeric weight, e.g. 400 or 700
                        "italic": font.italic(),        # True if this is an italic style
                        "file_name": file_name,
                        "file_path": file_path,
                    })

    def _style_already_recorded(self, family_name, style_name):
        """
        Returns True if we already stored this style for this family.
        Prevents duplicate entries when multiple font files cover the same family.
        """
        for entry in self.font_catalog.get(family_name, []):
            if entry["style_name"] == style_name:
                return True
        return False

    def has_family(self, family_name):
        """
        Returns True if this font family was loaded from the fonts folder.

        Use this if you want to check before calling get_font(), though
        get_font() already handles the missing-font case gracefully.
        """
        return family_name in self.loaded_families

    def get_font(self, family_name, point_size, weight=None, italic=False):
        """
        Returns a QFont for the requested family, size, weight, and italic style.

        If the family wasn't loaded from the fonts folder, returns a plain
        Qt default font (no custom family) — this is the safe fallback.

        Args:
            family_name: e.g. "SF Pro Display"
            point_size:  font size in points, e.g. 18
            weight:      numeric weight (400 = regular, 700 = bold), or None
            italic:      True for italic, False for normal
        """

        # If the family wasn't loaded from our fonts folder, don't guess —
        # just return a plain default font with the requested size
        if family_name not in self.loaded_families:
            return self._default_font(point_size, italic)

        # If no specific weight was requested, let Qt pick the default weight
        if weight is None:
            font = QFont(family_name, point_size)
            font.setItalic(italic)
            return font

        # Find the closest available style for the requested weight/italic combo
        best_match = self._find_best_style(family_name, weight, italic)

        if best_match:
            # Build the font from the exact Qt style name so the weight is accurate
            matched_font = QFontDatabase.font(family_name, best_match["style_name"], point_size)
            matched_font.setItalic(best_match["italic"])
            return matched_font

        # This shouldn't normally happen (we found the family but no styles),
        # but fall back to default just in case
        return self._default_font(point_size, italic)

    @staticmethod
    def _default_font(point_size, italic=False):
        """
        Returns a plain QFont with no family specified.

        Qt will use its own default font — whatever the OS/platform picks.
        This is the correct fallback when a custom font isn't available.
        """
        font = QFont()
        font.setPointSize(point_size)
        font.setItalic(italic)
        return font

    def _find_best_style(self, family_name, requested_weight, requested_italic):
        """
        Finds the closest available style for a family by weight and italic.

        Strategy:
        1. Prefer styles that match the italic flag exactly
        2. Among those, pick the one whose weight is numerically closest
        """

        styles = self.font_catalog.get(family_name, [])
        if not styles:
            return None

        # First try to narrow down to styles matching the italic flag
        same_italic = [s for s in styles if s["italic"] == requested_italic]

        # If no italic match exists, fall back to all styles
        candidates = same_italic if same_italic else styles

        # Return the style whose weight is closest to what was requested
        return min(candidates, key=lambda s: abs(s["weight"] - requested_weight))

    def get_family_styles(self, family_name):
        """
        Returns all loaded style info dicts for a given family.
        Returns an empty list if the family wasn't loaded.
        """
        return self.font_catalog.get(family_name, [])

    def print_family_styles(self, family_name):
        """
        Debug helper — prints a readable list of all styles for a family.
        Call this during development to inspect what got loaded.
        """
        styles = self.get_family_styles(family_name)

        if not styles:
            print(f"[FontManager] No styles found for family: {family_name}")
            return

        print(f"\nStyles loaded for '{family_name}':")
        for s in styles:
            print(
                f"  style={s['style_name']}, "
                f"weight={s['weight']}, "
                f"italic={s['italic']}, "
                f"file={s['file_name']}"
            )