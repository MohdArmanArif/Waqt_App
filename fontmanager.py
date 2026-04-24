import os
from PyQt6.QtGui import QFont, QFontDatabase


class FontManager:
    """
    Loads font files from a folder and builds a searchable catalog of:
    - font families (e.g. "SF Mono", "SF Pro Display")
    - styles (e.g. Regular, Bold, Medium Italic)
    - weight values (e.g. 400, 700)
    - italic flags (True/False)

    This allows you to request fonts later by:
    - family name
    - weight
    - italic

    Even if the exact style isn't available, the closest match will be used.
    """

    def __init__(self, fonts_folder="fonts"):
        # Get absolute path to the folder containing this Python file
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Build full path to fonts folder
        self.fonts_folder = os.path.join(script_dir, fonts_folder)

        # Store all loaded font family names
        self.loaded_families = set()

        # Main data structure storing all font info
        # Format:
        # {
        #   "SF Mono": [ {style info}, {style info}, ... ],
        #   "SF Pro Display": [ ... ]
        # }
        self.font_catalog = {}

        # Load fonts immediately on creation
        self.load_all_fonts()

    def load_all_fonts(self):
        """
        Loads all font files (.otf, .ttf) from the fonts folder.

        For each font file:
        - register it with Qt
        - extract its family name(s)
        - extract available styles (Regular, Bold, etc.)
        - store weight + italic info
        """

        if not os.path.exists(self.fonts_folder):
            print(f"Fonts folder not found: {self.fonts_folder}")
            return

        for file_name in os.listdir(self.fonts_folder):

            # Ignore hidden/system files (like ._mac files)
            if file_name.startswith("."):
                continue

            # Only process font files
            if not file_name.lower().endswith((".otf", ".ttf")):
                continue

            file_path = os.path.join(self.fonts_folder, file_name)

            # Register font with Qt
            font_id = QFontDatabase.addApplicationFont(file_path)

            if font_id == -1:
                print(f"Failed to load font: {file_path}")
                continue

            # Get the font family names from this file
            families = QFontDatabase.applicationFontFamilies(font_id)

            if not families:
                print(f"No families found in: {file_path}")
                continue

            for family_name in families:

                # Track available families
                self.loaded_families.add(family_name)

                # Initialize catalog entry if not already present
                if family_name not in self.font_catalog:
                    self.font_catalog[family_name] = []

                # Get all styles for this family (e.g. Regular, Bold, Italic)
                style_names = QFontDatabase.styles(family_name)

                for style_name in style_names:

                    # Create a font object for this style
                    font = QFontDatabase.font(family_name, style_name, 12)

                    # Extract useful metadata
                    font_info = {
                        "style_name": style_name,        # e.g. "Bold Italic"
                        "weight": int(font.weight()),   # e.g. 400, 700
                        "italic": font.italic(),        # True/False
                        "file_name": file_name,
                        "file_path": file_path,
                    }

                    # Avoid duplicate entries
                    if not self._style_already_recorded(family_name, style_name):
                        self.font_catalog[family_name].append(font_info)

                        # For debugging
                        # print(
                        #     f"  Family: {family_name} | "
                        #     f"Style: {style_name} | "
                        #     f"Weight: {font_info['weight']} | "
                        #     f"Italic: {font_info['italic']}"
                        # )

    def _style_already_recorded(self, family_name, style_name):
        """
        Prevent duplicate style entries for a family.
        """
        for entry in self.font_catalog.get(family_name, []):
            if entry["style_name"] == style_name:
                return True
        return False

    def has_family(self, family_name):
        """
        Check if a font family exists in the loaded catalog.
        """
        return family_name in self.loaded_families

    def get_family_styles(self, family_name):
        """
        Return all styles for a given font family.
        """
        return self.font_catalog.get(family_name, [])

    def print_family_styles(self, family_name):
        """
        Debug helper: prints all styles for a family.
        """
        styles = self.get_family_styles(family_name)

        if not styles:
            print(f"No styles found for family: {family_name}")
            return

        print(f"\nStyles for {family_name}:")
        for style in styles:
            print(
                f"  style_name={style['style_name']}, "
                f"weight={style['weight']}, "
                f"italic={style['italic']}, "
                f"file={style['file_name']}"
            )

    def get_font(self, family_name, point_size, weight=None, italic=False):
        """
        Returns a QFont object matching the requested parameters.

        If an exact match doesn't exist:
        - finds the closest weight
        - prioritizes matching italic if possible
        """

        # Base font object
        font = QFont(family_name, point_size)

        # If no weight requested, just apply italic and return
        if weight is None:
            font.setItalic(italic)
            return font

        # Try to find best available style
        best_match = self.find_best_style(family_name, weight, italic)

        if best_match:
            style_name = best_match["style_name"]

            # Build font from exact style
            matched_font = QFontDatabase.font(family_name, style_name, point_size)
            matched_font.setItalic(best_match["italic"])
            return matched_font

        # Fallback if nothing found
        font.setWeight(weight)
        font.setItalic(italic)
        return font

    def find_best_style(self, family_name, requested_weight, requested_italic):
        """
        Find the closest available style.

        Priority:
        1. Match italic if possible
        2. Match closest weight
        """

        styles = self.font_catalog.get(family_name, [])
        if not styles:
            return None

        # Prefer matching italic exactly
        same_italic = [
            style for style in styles
            if style["italic"] == requested_italic
        ]

        candidates = same_italic if same_italic else styles

        # Pick closest weight
        best_match = min(
            candidates,
            key=lambda style: abs(style["weight"] - requested_weight)
        )

        return best_match