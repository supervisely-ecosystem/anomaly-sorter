import src.nodes as n
import src.sly_globals as g
import supervisely as sly

app = sly.Application(layout=n.layout)
# app.call_before_shutdown(g.scheduler.shutdown)  # ? it seems like this is not working


# * Class Selector Node: allows user to select a class for filtering
@n.class_selector.apply_button.click
def on_class_selector_apply_click():
    n.class_selector.hide_warning_badge()
    n.class_selector.modal.hide()
    n.class_selector.save()
    selected_class = n.class_selector.selected_class
    if selected_class is None:
        n.class_selector.show_warning_badge()
        return
    n.check_every_node.show_automation_details()
    n.stats_node.set_selected_class(n.class_selector.selected_class)
    n.stats_node.run()
    n.stats_node.apply_automation(g.AUTOMATION_INTERVAL)


# * Run Node: applies filters and sets the link to the filtered images
@n.run_node.card.click
def on_run_node_click():
    # n.run_node.modal.hide()
    if n.run_node.card.is_disabled():
        return
    _on_run_node_click()


def _on_run_node_click():
    n.run_node.hide_is_finished_badge()
    g.collection_id = n.run_node.run(filters=n.filters_node.filters, stats=n.stats_node.stats)
    if g.collection_id is None:
        msg = "No images found after applying filters. Please adjust your filters and try again."
        sly.app.show_dialog(title="Warning", description=msg, status="warning")
        n.run_node.hide_in_progress_badge()
        return
    sly.logger.info("Filters applied successfully.")
    link = n.run_node.prepare_link(project_id=g.project.id, collection_id=g.collection_id)
    sly.logger.info(f"Link to filtered images: {link}")
    n.navigate.card.link = link
    n.accept_node.hide_is_finished_badge()
    n.run_node.show_is_finished_badge()


# @n.stats_node.on_stats_calculated
# def on_stats_calculated():
#     n.run_node.card.enable()
#     if n.run_node.auto_apply:
#         _on_run_node_click()


# * Accept Node: tags accepted anomalies using user-defined bounderies
@n.accept_node.run_btn.click
def on_accept_node_run_click():
    n.accept_node.modal.hide()
    n.accept_node.run(g.collection_id)
    sly.logger.info("Accepted anomalies tagged successfully.")


# * Restore data and state if available
sly.app.restore_data_state(g.task_id)

# * Some restoration logic (!AFTER restore_data_state)
if n.class_selector.selected_class:
    n.class_selector.hide_warning_badge()
    n.check_every_node.show_automation_details()
    n.stats_node.set_selected_class(n.class_selector.selected_class)
    n.stats_node.run()
    n.stats_node.apply_automation(g.AUTOMATION_INTERVAL)
