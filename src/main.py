import src.nodes as n
import src.sly_globals as g
import supervisely as sly
from supervisely.app.content import DataJson

app = sly.Application(layout=n.layout)
# app.call_before_shutdown(g.scheduler.shutdown)  # ? it seems like this is not working


@n.class_selector.apply_button.click
def on_class_selector_apply_click():
    n.class_selector.save()
    n.class_selector.modal.hide()
    n.stats_node.set_selected_class(n.class_selector.selected_class)
    n.stats_node.apply_automation(g.AUTOMATION_INTERVAL)


# ! Debugging purposes only
if sly.is_development():
    n.class_selector.classes_table.select(["person_poly"])

on_class_selector_apply_click()


# * Main function to apply filters and navigate to the filtered images
@n.run_node.card.click
def on_run_node_click():
    """
    This function is called when the RunNode card is clicked.
    It retrieves the filters from the CustomFilters node and runs the filters on the images in the project.
    """
    n.run_node.hide_is_finished_badge()
    n.run_node.show_in_progress_badge()
    g.collection_id = n.run_node.run(filters=n.filters_node.filters, stats=n.stats_node.stats)
    if g.collection_id is None:
        msg = "No images found after applying filters. Please adjust your filters and try again."
        sly.app.show_dialog(title="Warning", message=msg, status="warning")
        n.run_node.hide_in_progress_badge()
        return
    sly.logger.info("Filters applied successfully.")
    link = n.run_node.prepare_link(project_id=g.project.id, collection_id=g.collection_id)
    sly.logger.info(f"Link to filtered images: {link}")
    n.navigate.card.link = link
    n.run_node.hide_in_progress_badge()
    n.run_node.show_is_finished_badge()


# * Tag accepted anomalies
@n.accept_node.run_btn.click
def on_accept_node_run_click():
    """
    This function is called when the AcceptAnomaliesNode run button is clicked.
    It tags the accepted anomalies in the project based on user-defined boundaries.
    """
    n.accept_node.run(g.collection_id)
    sly.logger.info("Accepted anomalies tagged successfully.")
