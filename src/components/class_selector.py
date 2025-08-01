from src.components.base_element import BaseActionElement
from supervisely.api.api import Api
from supervisely.app.content import DataJson
from supervisely.app.widgets import (
    Button,
    ClassesListSelector,
    Container,
    Dialog,
    Icons,
    SolutionCard,
    Text,
    Widget,
)
from supervisely.project.project_meta import ProjectMeta
from supervisely.sly_logger import logger
from supervisely.solution.base_node import SolutionCardNode, SolutionElement


class ClassSelector(SolutionElement):
    """
    This class represents a card that allows users to select a class for filtering images.
    """

    def __init__(
        self,
        api: Api,
        project_id: int,
        x: int = 0,
        y: int = 0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.api = api
        self.project_id = project_id
        self.card = self._create_card()
        self.node = SolutionCardNode(content=self.card, x=x, y=y)
        self.modals = [self.modal]

        @self.card.click
        def on_card_click():
            self.modal.show()

        self.show_warning_badge()

    @property
    def modal(self) -> Dialog:
        """
        Returns a modal dialog for custom filters.
        """
        if not hasattr(self, "_modal"):
            self._modal = self._create_modal()
        return self._modal

    def _create_card(self):
        return SolutionCard(
            title="Class Selection",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="right",
            icon=Icons(
                class_name="zmdi zmdi-layers",
                color="#2196F3",
                bg_color="#E3F2FD",
            ),
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(description="Select a class to filter images")

    def _create_modal(self):
        """
        Create a modal dialog for class selection.
        """
        return Dialog(
            title="Select Class for Filtering",
            content=self._create_modal_content(),
            size="tiny",
        )

    def _create_modal_content(self) -> Widget:
        """
        Create the content of the modal dialog.
        """
        intro_text = Text(
            "Select a class from the table below to filter images by that class.",
            font_size=13,
        )

        meta = ProjectMeta.from_json(self.api.project.get_meta(self.project_id))
        self.classes_table = ClassesListSelector(meta.obj_classes)
        self.apply_button = Button("Apply")
        apply_button_box = Container([self.apply_button], style="align-items: flex-end")

        content = Container([intro_text, self.classes_table, apply_button_box])

        return content

    def save(self) -> None:
        """Save the selected filters to the DataJson."""
        selected_class = self._get_class_from_widges()
        DataJson()[self.widget_id]["selected_class"] = selected_class
        DataJson().send_changes()
        logger.info("Selected class saved successfully.")

    @property
    def selected_class(self) -> str:
        """
        Get the selected class from the DataJson.
        """
        return DataJson()[self.widget_id].get("selected_class", "")

    def _get_class_from_widges(self) -> str:
        """
        Get the selected class from the ClassesListSelector widget.
        """
        selected_classes = self.classes_table.get_selected_classes()
        if not selected_classes:
            logger.error("No class selected, returning an empty string.")
            self.show_warning_badge()
            return ""
        if len(selected_classes) > 1:
            logger.warning("Multiple classes selected, returning the first one.")
        return selected_classes[0].name

    def show_warning_badge(self) -> None:
        self._update_warning_badge(True)

    def hide_warning_badge(self) -> None:
        self._update_warning_badge(False)

    def _update_warning_badge(self, enable: bool) -> None:
        if not hasattr(self, "card"):
            logger.error("Card is not defined for this element.")
            return
        if not isinstance(self.card, SolutionCard):
            logger.error("Card is not an instance of SolutionCard.")
            return

        if enable:
            self.card.update_badge_by_key(
                key="No Class Selected",
                label="⚠️",
                plain=True,
            )
        else:
            self.card.remove_badge_by_key("No Class Selected")
