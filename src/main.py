import src.nodes as n
import src.sly_globals as g
import supervisely as sly

app = sly.Application(layout=n.layout)
app.call_before_shutdown(g.scheduler.shutdown)  # ? it seems like this is not working


@n.class_selector.apply_button.click
def on_apply():
    n.class_selector.save()
    n.class_selector.modal.hide()
    n.stats_node.set_selected_class(n.class_selector.selected_class)
    n.stats_node.apply_automation(g.AUTOMATION_INTERVAL)


# * Main function to apply filters and navigate to the filtered images
@n.run_node.card.click
def on_run_node_click():
    """
    This function is called when the RunNode card is clicked.
    It retrieves the filters from the CustomFilters node and runs the filters on the images in the project.
    """
    collection_id = n.run_node.run(filters=n.filters_node.filters, stats=n.stats_node.stats)
    sly.logger.info("Filters applied successfully.")
    link = n.run_node.prepare_link(project_id=g.project.id, collection_id=collection_id)
    sly.logger.info(f"Link to filtered images: {link}")
    n.navigate.card.link = link
