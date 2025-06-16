from supervisely.app.widgets import SolutionCard
from supervisely.sly_logger import logger
from supervisely.solution.base_node import SolutionElement


class BaseElement(SolutionElement):
    """
    Base class for all elements in the solution graph of this project.
    """

    def show_in_progress_badge(self) -> None:
        self.update_in_progress_badge(True)

    def hide_in_progress_badge(self) -> None:
        self.update_in_progress_badge(False)

    def update_in_progress_badge(self, enable: bool) -> None:
        if not hasattr(self, "card"):
            logger.error("Card is not defined for this element.")
            return
        if not isinstance(self.card, SolutionCard):
            logger.error("Card is not an instance of SolutionCard.")
            return
        if enable:
            self.card.update_badge_by_key(
                key="In Progress", label="⚡", plain=True, badge_type="warning"
            )
        else:
            self.card.remove_badge_by_key("In Progress")

    def show_is_finished_badge(self) -> None:
        self.update_is_finished_badge(True)

    def hide_is_finished_badge(self) -> None:
        self.update_is_finished_badge(False)

    def update_is_finished_badge(self, enable: bool) -> None:
        if not hasattr(self, "card"):
            logger.error("Card is not defined for this element.")
            return
        if not isinstance(self.card, SolutionCard):
            logger.error("Card is not an instance of SolutionCard.")
            return

        if enable:
            self.card.update_badge_by_key(
                key="Finished",
                label="✅",
                plain=True,
            )
        else:
            self.card.remove_badge_by_key("In Progress")
