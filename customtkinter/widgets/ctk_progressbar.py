import tkinter
import math
from typing import Union, Tuple

from .ctk_canvas import CTkCanvas
from ..theme_manager import ThemeManager
from ..draw_engine import DrawEngine
from .widget_base_class import CTkBaseClass


class CTkProgressBar(CTkBaseClass):
    """
    Progressbar with rounded corners, border, variable support,
    indeterminate mode, vertical orientation.
    For detailed information check out the documentation.
    """

    def __init__(self, *args,
                 width: Union[int, str] = "default_init",
                 height: Union[int, str] = "default_init",
                 corner_radius: Union[str, Tuple[str, str]] = "default_theme",
                 border_width: Union[int, str] = "default_theme",

                 bg_color: Union[str, Tuple[str, str], None] = None,
                 fg_color: Union[str, Tuple[str, str]] = "default_theme",
                 border_color: Union[str, Tuple[str, str]] = "default_theme",
                 progress_color: Union[str, Tuple[str, str]] = "default_theme",

                 variable: tkinter.Variable = None,
                 orientation: str = "horizontal",
                 mode: str = "determinate",
                 determinate_speed: float = 1,
                 indeterminate_speed: float = 1,
                 **kwargs):

        # set default dimensions according to orientation
        if width == "default_init":
            if orientation.lower() == "vertical":
                width = 8
            else:
                width = 200
        if height == "default_init":
            if orientation.lower() == "vertical":
                height = 200
            else:
                height = 8

        # transfer basic functionality (_bg_color, size, _appearance_mode, scaling) to CTkBaseClass
        super().__init__(*args, bg_color=bg_color, width=width, height=height, **kwargs)

        # color
        self._border_color = ThemeManager.theme["color"]["progressbar_border"] if border_color == "default_theme" else border_color
        self._fg_color = ThemeManager.theme["color"]["progressbar"] if fg_color == "default_theme" else fg_color
        self._progress_color = ThemeManager.theme["color"]["progressbar_progress"] if progress_color == "default_theme" else progress_color

        # control variable
        self._variable = variable
        self._variable_callback_blocked = False
        self._variable_callback_name = None

        # shape
        self._corner_radius = ThemeManager.theme["shape"]["progressbar_corner_radius"] if corner_radius == "default_theme" else corner_radius
        self._border_width = ThemeManager.theme["shape"]["progressbar_border_width"] if border_width == "default_theme" else border_width
        self._determinate_value: float = 0.5  # range 0-1
        self._determinate_speed = determinate_speed  # range 0-1
        self._indeterminate_value: float = 0  # range 0-inf
        self._indeterminate_width: float = 0.4  # range 0-1
        self._indeterminate_speed = indeterminate_speed  # range 0-1 to travel in 50ms
        self._loop_running: bool = False
        self._orientation = orientation
        self._mode = mode  # "determinate" or "indeterminate"

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # Each time an item is resized due to pack position mode, the binding Configure is called on the widget
        self.bind('<Configure>', self._update_dimensions_event)

        self._draw()  # initial draw

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self.set(self._variable.get(), from_variable_callback=True)
            self._variable_callback_blocked = False

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def destroy(self):
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        super().destroy()

    def _draw(self, no_color_updates=False):
        if self._orientation.lower() == "horizontal":
            orientation = "w"
        elif self._orientation.lower() == "vertical":
            orientation = "s"
        else:
            orientation = "w"

        if self._mode == "determinate":
            requires_recoloring = self._draw_engine.draw_rounded_progress_bar_with_border(self._apply_widget_scaling(self._current_width),
                                                                                          self._apply_widget_scaling(self._current_height),
                                                                                          self._apply_widget_scaling(self._corner_radius),
                                                                                          self._apply_widget_scaling(self._border_width),
                                                                                          0,
                                                                                          self._determinate_value,
                                                                                          orientation)
        else:  # indeterminate mode
            progress_value = (math.sin(self._indeterminate_value * math.pi / 40) + 1) / 2
            progress_value_1 = min(1.0, progress_value + (self._indeterminate_width / 2))
            progress_value_2 = max(0.0, progress_value - (self._indeterminate_width / 2))

            requires_recoloring = self._draw_engine.draw_rounded_progress_bar_with_border(self._apply_widget_scaling(self._current_width),
                                                                                          self._apply_widget_scaling(self._current_height),
                                                                                          self._apply_widget_scaling(self._corner_radius),
                                                                                          self._apply_widget_scaling(self._border_width),
                                                                                          progress_value_1,
                                                                                          progress_value_2,
                                                                                          orientation)

        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))
            self._canvas.itemconfig("border_parts",
                                    fill=ThemeManager.single_color(self._border_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._border_color, self._appearance_mode))
            self._canvas.itemconfig("inner_parts",
                                    fill=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._fg_color, self._appearance_mode))
            self._canvas.itemconfig("progress_parts",
                                    fill=ThemeManager.single_color(self._progress_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._progress_color, self._appearance_mode))

    def configure(self, require_redraw=False, **kwargs):
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            require_redraw = True

        if "progress_color" in kwargs:
            self._progress_color = kwargs.pop("progress_color")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)

            self._variable = kwargs.pop("variable")

            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get(), from_variable_callback=True)
            else:
                self._variable = None

        if "mode" in kwargs:
            self._mode = kwargs.pop("mode")
            require_redraw = True

        if "determinate_speed" in kwargs:
            self._determinate_speed = kwargs.pop("determinate_speed")

        if "indeterminate_speed" in kwargs:
            self._indeterminate_speed = kwargs.pop("indeterminate_speed")

        if "width" in kwargs:
            self._set_dimensions(width=kwargs.pop("width"))

        if "height" in kwargs:
            self._set_dimensions(height=kwargs.pop("height"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "progress_color":
            return self._progress_color

        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "orientation":
            return self._orientation
        elif attribute_name == "mode":
            return self._mode
        elif attribute_name == "determinate_speed":
            return self._determinate_speed
        elif attribute_name == "indeterminate_speed":
            return self._indeterminate_speed
        else:
            return super().cget(attribute_name)

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)

    def set(self, value, from_variable_callback=False):
        """ set determinate value """
        self._determinate_value = value

        if self._determinate_value > 1:
            self._determinate_value = 1
        elif self._determinate_value < 0:
            self._determinate_value = 0

        self._draw(no_color_updates=True)

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(round(self._determinate_value) if isinstance(self._variable, tkinter.IntVar) else self._determinate_value)
            self._variable_callback_blocked = False

    def get(self) -> float:
        """ get determinate value """
        return self._determinate_value

    def start(self):
        """ start indeterminate mode """
        if not self._loop_running:
            self._loop_running = True
            self._internal_loop()

    def stop(self):
        """ stop indeterminate mode """
        self._loop_running = False

    def _internal_loop(self):
        if self._loop_running:
            if self._mode == "determinate":
                self._determinate_value += self._determinate_speed / 50
                if self._determinate_value > 1:
                    self._determinate_value -= 1
                self._draw()
                self.after(20, self._internal_loop)
            else:
                self._indeterminate_value += self._indeterminate_speed
                self._draw()
                self.after(20, self._internal_loop)

    def step(self):
        if self._mode == "determinate":
            self._determinate_value += self._determinate_speed / 50
            if self._determinate_value > 1:
                self._determinate_value -= 1
            self._draw()
        else:
            self._indeterminate_value += self._indeterminate_speed
            self._draw()

    def bind(self, sequence=None, command=None, add=None):
        """ called on the tkinter.Canvas """
        return self._canvas.bind(sequence, command, add)
