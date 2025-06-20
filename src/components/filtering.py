from typing import Callable, Dict, List, Optional, Tuple

from src.components.base_element import BaseActionElement
from supervisely.app.content import DataJson
from supervisely.app.widgets import (
    Button,
    Checkbox,
    Container,
    Dialog,
    Empty,
    Field,
    Flexbox,
    Icons,
    InputNumber,
    RadioGroup,
    SolutionCard,
    Text,
    Widget,
)
from supervisely.sly_logger import logger
from supervisely.solution.base_node import SolutionCardNode, SolutionElement


class CustomFilters(SolutionElement):
    """
    This class is a placeholder for the custom filters functionality.
    """

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.card = self._create_card()
        self.node = SolutionCardNode(content=self.card, x=x, y=y)
        self.modals = [self.modal]

        @self.card.click
        def on_card_click():
            self.modal.show()

    @property
    def modal(self) -> Dialog:
        """Returns a modal dialog for custom filters."""
        if not hasattr(self, "_modal"):
            self._modal = self._create_modal()
        return self._modal

    def _create_card(self):
        return SolutionCard(
            title="Filter & Sort Settings",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="right",
            icon=Icons(
                class_name="zmdi zmdi-filter-list",
                color="#1976D2",
                bg_color="#E3F2FD",
            ),
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(
            description="Configure filtering and sorting options for your images."
        )

    def _create_modal(self):
        """Create a modal dialog for custom filters."""
        return Dialog(title="Custom Filters", content=self._create_modal_content(), size="tiny")

    def _create_modal_content(self) -> Widget:
        """Create the content of the modal dialog."""

        # filter by number of labels
        min_num_label = Text("Number of Labels greater than:", font_size=13)
        self.min_num_check = Checkbox(min_num_label)
        self.min_num_input = InputNumber(min=0, step=1, size="mini", controls=False, width=100)
        self.min_num_input.disable()

        max_num_label = Text("Number of Labels less than:", font_size=13)
        self.max_num_check = Checkbox(max_num_label)
        self.max_num_input = InputNumber(min=0, step=1, size="mini", controls=False, width=100)
        self.max_num_input.disable()

        min_num_box = Flexbox(
            widgets=[
                Empty(style="width: 20px"),
                self.min_num_check,
                self.min_num_input,
            ],
            vertical_alignment="center",
        )
        max_num_box = Flexbox(
            widgets=[
                Empty(style="width: 20px"),
                self.max_num_check,
                self.max_num_input,
            ],
            vertical_alignment="center",
        )
        num_lbls_field = Field(Container([min_num_box, max_num_box]), "Filter by Number of Labels")

        @self.min_num_check.value_changed
        def on_min_num_check_change(is_checked: bool):
            # self._update_sort_options()
            if is_checked:
                self.min_num_input.enable()
            else:
                self.min_num_input.disable()

        @self.max_num_check.value_changed
        def on_max_num_check_change(is_checked: bool):
            # self._update_sort_options()
            if is_checked:
                self.max_num_input.enable()
            else:
                self.max_num_input.disable()

        # filter by area (e.g. total area on image should be greater than some value)
        min_area_label = Text("Has Labels with Area greater than:", font_size=13)
        px_label = Text("px", font_size=13)
        self.min_area_check = Checkbox(min_area_label)
        self.min_area_input = InputNumber(min=0, step=1, size="mini", controls=False, width=100)
        self.min_area_input.disable()

        # max_area_label = Text("Max Area (px):", font_size=13)
        # self.max_area_check = Checkbox(max_area_label)
        # self.max_area_input = InputNumber(min=0, step=1, size="mini", controls=False, width=100)
        # self.max_area_input.disable()

        min_area_box = Flexbox(
            widgets=[
                Empty(style="width: 20px"),
                self.min_area_check,
                self.min_area_input,
                px_label,
            ],
            vertical_alignment="center",
        )
        # max_area_box = Flexbox(
        #     widgets=[
        #         Empty(style="width: 20px"),
        #         self.max_area_check,
        #         self.max_area_input,
        #     ],
        #     vertical_alignment="center",
        # )
        area_field = Field(
            Container([min_area_box]),
            "Filter by Area",
        )

        @self.min_area_check.value_changed
        def on_min_area_check_change(is_checked: bool):
            # self._update_sort_options()
            if is_checked:
                self.min_area_input.enable()
            else:
                self.min_area_input.disable()

        # @self.max_area_check.value_changed
        # def on_max_area_check_change(is_checked: bool):
        #     self._update_sort_options()
        #     if is_checked:
        #         self.max_area_input.enable()
        #     else:
        #         self.max_area_input.disable()

        # filter by average intensity difference
        # min_intensity_diff_label = Text("Average Intensity Difference greater than:", font_size=13)
        # self.min_intensity_diff_check = Checkbox(min_intensity_diff_label)
        # self.min_intensity_diff_input = InputNumber(
        #     min=0, step=1, size="mini", controls=False, width=100
        # )
        # self.min_intensity_diff_input.disable()

        # max_intensity_diff_label = Text("Average Intensity Difference less than:", font_size=13)
        # self.max_intensity_diff_check = Checkbox(max_intensity_diff_label)
        # self.max_intensity_diff_input = InputNumber(
        #     min=0, step=1, size="mini", controls=False, width=100
        # )
        # self.max_intensity_diff_input.disable()
        # min_intensity_diff_box = Flexbox(
        #     widgets=[
        #         Empty(style="width: 20px"),
        #         self.min_intensity_diff_check,
        #         self.min_intensity_diff_input,
        #     ],
        #     vertical_alignment="center",
        # )
        # max_intensity_diff_box = Flexbox(
        #     widgets=[
        #         Empty(style="width: 20px"),
        #         self.max_intensity_diff_check,
        #         self.max_intensity_diff_input,
        #     ],
        #     vertical_alignment="center",
        # )
        # avg_intensity_diff_field = Field(
        #     Container([min_intensity_diff_box, max_intensity_diff_box]),
        #     "Filter by Average Intensity Difference",
        # )

        # @self.min_intensity_diff_check.value_changed
        # def on_avg_intensity_diff_check_change(is_checked: bool):
        #     self._update_sort_options()
        #     if is_checked:
        #         self.min_intensity_diff_input.enable()
        #     else:
        #         self.min_intensity_diff_input.disable()

        # @self.max_intensity_diff_check.value_changed
        # def on_max_intensity_diff_check_change(is_checked: bool):
        #     self._update_sort_options()
        #     if is_checked:
        #         self.max_intensity_diff_input.enable()
        #     else:
        #         self.max_intensity_diff_input.disable()

        # # sort options:
        self.sort_by_label = Text("Sort by:", font_size=13)
        self.sort_by = RadioGroup(
            items=self._create_sort_options(
                num_labels=True,
                total_area=True,
                max_area=True,
                avg_intensity_diff=True,
                max_intensity_diff=True,
                min_intensity_diff=True,
            ),
            size="mini",
            direction="vertical",
        )
        sort_options_box = Flexbox(
            widgets=[
                Empty(style="width: 20px"),
                # self.sort_by_label,
                self.sort_by,
            ],
            vertical_alignment="start",
        )

        # # sort order
        # self.sort_order_label = Text("Sort order:", font_size=13)
        # self.sort_order = RadioGroup(
        #     items=[
        #         RadioGroup.Item("asc", "Ascending"),
        #         RadioGroup.Item("desc", "Descending"),
        #     ],
        #     size="mini",
        # )
        # sort_order_box = Flexbox(
        #     widgets=[
        #         Empty(style="width: 20px"),
        #         self.sort_order_label,
        #         self.sort_order,
        #     ],
        #     vertical_alignment="center",
        # )
        self.sort_options_field = Field(
            Container([sort_options_box]),
            "Sort by",
        )

        self.apply_button = Button("Save", icon="zmdi zmdi-check")
        apply_button_box = Container([self.apply_button], style="align-items: flex-end")

        content = Container(
            [
                num_lbls_field,
                area_field,
                # avg_intensity_diff_field,
                self.sort_options_field,
                apply_button_box,
            ],
        )

        @self.apply_button.click
        def on_apply_button_click():
            """
            Handle the click event of the apply button.
            This method should be overridden in subclasses to apply specific filters.
            """
            filters = self._get_filters_from_widges()
            keys_map = {
                "min_num_labels": "Min Number of Labels",
                "max_num_labels": "Max Number of Labels",
                "min_area": "Min Area",
                "sort_by": "Sort By",
            }
            for full_name in keys_map.values():
                self.card.remove_property_by_key(full_name)
            if filters:
                self.save()
                self.modal.hide()

                for key, full_name in keys_map.items():
                    if key in filters:
                        label = str(filters[key])
                        if key == "sort_by":
                            label = label.replace("_", " ").title()
                        self.card.update_property(full_name, label, highlight=True)

        return content

    def _create_sort_options(
        self,
        num_labels: bool = False,
        total_area: bool = False,
        max_area: bool = False,
        avg_intensity_diff: bool = False,
        max_intensity_diff: bool = False,
        min_intensity_diff: bool = False,
    ) -> List[RadioGroup.Item]:
        items = []
        if num_labels:
            items.append(RadioGroup.Item("_labels", "Number of Labels"))
        if total_area:
            items.append(RadioGroup.Item("_total_area", "Total area"))
        if max_area:
            items.append(RadioGroup.Item("_max_area", "Maximum Area"))
        if avg_intensity_diff:
            items.append(RadioGroup.Item("_avg_intensity_diff", "Average Intensity Difference"))
        if max_intensity_diff:
            items.append(RadioGroup.Item("_max_intensity_diff", "Maximum Intensity Difference"))
        if min_intensity_diff:
            items.append(RadioGroup.Item("_min_intensity_diff", "Minimum Intensity Difference"))
        return items

    def _update_sort_options(self) -> None:
        """
        Update the sort options based on the selected filters.
        This method can be overridden in subclasses to provide specific sort options.
        """
        self.sort_by.set(
            self._create_sort_options(
                num_labels=True,
                total_area=True,
                max_area=True,
                avg_intensity_diff=True,
                max_intensity_diff=True,
                min_intensity_diff=True,
            )
        )

    def save(self, filters: Optional[Dict] = None) -> None:
        """
        Save the filters specified in the modal dialog.
        This method should be overridden in subclasses to save specific filter criteria.
        """
        if filters is None:
            filters = self._get_filters_from_widges()
        DataJson()[self.widget_id]["filters"] = filters
        DataJson().send_changes()
        logger.info("Filters saved", extra={"filters": filters})

    def _get_filters_from_widges(self) -> Dict:
        """
        Get the filters specified in the modal dialog.
        This method should be overridden in subclasses to return specific filter criteria.
        """
        filters = {}
        if self.min_num_check.is_checked():
            filters["min_num_labels"] = self.min_num_input.get_value()
        if self.max_num_check.is_checked():
            filters["max_num_labels"] = self.max_num_input.get_value()
        if self.min_area_check.is_checked():
            filters["min_area"] = self.min_area_input.get_value()
        # if self.max_area_check.is_checked():
        #     filters["max_area"] = self.max_area_input.get_value()
        # if self.min_intensity_diff_check.is_checked():
        #     filters["min_intensity_diff"] = self.min_intensity_diff_input.get_value()
        # if self.max_intensity_diff_check.is_checked():
        #     filters["max_intensity_diff"] = self.max_intensity_diff_input.get_value()
        if self.sort_by.get_value() is not None:
            filters["sort_by"] = self.sort_by.get_value()
        # if self.sort_order.get_value() is not None:
        #     filters["sort_order"] = self.sort_order.get_value()
        return filters

    @property
    def filters(self) -> Dict:
        """
        Get the filters specified in the modal dialog.
        This property should be overridden in subclasses to return specific filter criteria.
        """
        return DataJson()[self.widget_id].get("filters", {})
