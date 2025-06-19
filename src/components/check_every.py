from supervisely.app.widgets import Icons, SolutionCard
from supervisely.solution.base_node import SolutionCardNode, SolutionElement


class InfoCheckEvery(SolutionElement):
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

    def _create_card(self):
        return SolutionCard(
            title="Check For Updates",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="right",
            icon=Icons(
                class_name="zmdi zmdi-flash-auto",
                color="#2196F3",
                bg_color="#E3F2FD",
            ),
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(
            description="The app automatically checks for new images or updates every minute and processes them if changes are detected."
        )

    def show_automation_details(self) -> None:
        self.node.show_automation_badge()
        self.node.update_property(key="Check Every", value="1 minute", highlight=True)

    def hide_automation_details(self) -> None:
        self.node.hide_automation_badge()
        self.node.remove_property_by_key("Check Every")
