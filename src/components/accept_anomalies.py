from collections import defaultdict
from typing import Optional

from src.components.base_element import BaseActionElement
from supervisely.annotation.tag_meta import TagApplicableTo, TagMeta, TagValueType
from supervisely.api.api import Api
from supervisely.api.image_api import ImageInfo
from supervisely.api.module_api import ApiField
from supervisely.app.exceptions import show_dialog
from supervisely.app.widgets import (
    Button,
    Container,
    Dialog,
    Field,
    Icons,
    RadioGroup,
    SolutionCard,
)
from supervisely.project.project_meta import ProjectMeta
from supervisely.sly_logger import logger
from supervisely.solution.base_node import SolutionCardNode
from supervisely.task.progress import tqdm_sly

TAG_ACCEPTED = "_accepted"
TAG_ACCEPTED_BOUNDARY = "_accepted_boundary"


class AcceptAnomaliesNode(BaseActionElement):
    """
    This class represents a node in the solution graph that allows users to accept anomalies by tagging images in a collection.
    It automates the tagging of accepted anomalies based on user-defined boundaries.
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
        self._validate_project_meta()
        self.card = self._create_card()
        self.node = SolutionCardNode(content=self.card, x=x, y=y)
        self.modals = [self.modal]

        @self.card.click
        def on_card_click():
            self.modal.show()

    @property
    def modal(self) -> Dialog:
        if not hasattr(self, "_modal"):
            self._modal = self._create_modal()
        return self._modal

    def _create_modal(self):
        return Dialog(title="Accept Anomalies", content=self._create_modal_content(), size="tiny")

    def _create_modal_content(self):
        self.mode = RadioGroup(
            items=[
                RadioGroup.Item(value="keep", label="Keep Previous Tags"),
                RadioGroup.Item(value="rewrite", label="Rewrite Previous Tags"),
            ],
            direction="vertical",
        )
        field = Field(
            title="Tagging Mode",
            description="Choose how to handle existing 'accepted' tags:",
            content=self.mode,
        )
        btn_container = Container([self.run_btn], style="align-items: flex-end")
        return Container([field, btn_container])

    def _create_card(self):
        return SolutionCard(
            title="Tag Accepted Anomalies",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="right",
            icon=Icons(
                class_name="zmdi zmdi-check-all",
                color="#4CAF50",
                bg_color="#E8F5E9",
            ),
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(
            description=f"Automates the tagging of accepted anomalies using user-defined start image and end image of the sorted anomaly set.",
            # content=[self.run_btn],
        )

    @property
    def run_btn(self):
        if not hasattr(self, "_run_btn"):
            self._run_btn = self._create_run_button()
        return self._run_btn

    def _create_run_button(self):
        btn = Button(
            "Run",
            icon="zmdi zmdi-play",
            button_size="mini",
            plain=True,
            button_type="text",
        )

        return btn

    def run(self, collection_id: Optional[int] = None) -> None:
        if collection_id is None:
            msg = "Collection ID must be provided to run the AcceptAnomaliesNode."
            logger.error(msg)
            show_dialog(title="Error", description=msg, status="error")
            return
        self.hide_is_finished_badge()
        self.show_in_progress_badge()

        project_meta = self._validate_project_meta()
        tag_accepted = project_meta.tag_metas.get(TAG_ACCEPTED)
        tag_boundary = project_meta.tag_metas.get(TAG_ACCEPTED_BOUNDARY)

        images = self.api.entities_collection.get_items(collection_id)

        def _sort_key(img: ImageInfo) -> Optional[int]:
            try:
                return int(img.meta[ApiField.CUSTOM_SORT])
            except (ValueError, KeyError):
                return None

        sorted_images = sorted(images, key=_sort_key)

        start, end = None, None
        remove_tags = defaultdict(list)
        boundary_images = defaultdict(list)
        for idx, img in enumerate(sorted_images):
            img: ImageInfo
            if self.tagging_mode == "rewrite" and self._has_tag(img, tag_accepted):
                remove_tags[img.dataset_id].append(img.id)
            if self._has_tag(img, tag_boundary):
                boundary_images[img.dataset_id].append(img.id)
                if start is None:
                    start = idx
                    logger.info(f"Start image set: {img.name} (ID: {img.id})")
                else:
                    end = idx
                    logger.info(f"End image set: {img.name} (ID: {img.id})")

        if len(remove_tags) > 0:
            logger.info("Removing old accepted tags from images.")
            for _, img_ids in remove_tags.items():
                p = tqdm_sly(desc="Removing tags from images", total=len(img_ids))
                self.api.advanced.remove_tags_from_images([tag_accepted.sly_id], img_ids, p.update)

        tags_json = []
        success = False
        if start is not None and end is not None:
            for _, img_ids in boundary_images.items():
                self.api.advanced.remove_tags_from_images([tag_boundary.sly_id], img_ids)

            logger.info(f"Tagging images from index {start} to {end} as accepted anomalies.")
            for i in range(start, end + 1):
                img = sorted_images[i]
                tags_json.append({"tagId": tag_accepted.sly_id, "entityId": img.id})
            success = True
        else:
            logger.warning("No start and end images found for tagging accepted anomalies.")
            show_dialog(
                title="Warning",
                description="No start and end images found for tagging accepted anomalies.",
                status="warning",
            )

        if tags_json:
            self.api.image.tag.add_to_entities_json(self.project_id, tags_json, log_progress=True)
            logger.info(f"Tagged {len(tags_json)} images as accepted anomalies.")
        else:
            logger.info("No images to tag as accepted anomalies.")

        self.hide_in_progress_badge()
        if success:
            self.show_is_finished_badge()
            logger.info("AcceptAnomaliesNode run completed successfully.")

    def _has_tag(self, img: ImageInfo, tag_meta: TagMeta) -> bool:
        return any(tag["tagId"] == tag_meta.sly_id for tag in img.tags)

    def _validate_project_meta(self) -> ProjectMeta:
        """
        Check if the project meta has the required tag and upload them if not.
        """
        meta = ProjectMeta.from_json(self.api.project.get_meta(self.project_id))
        need_updated = False
        for tag_name in [TAG_ACCEPTED, TAG_ACCEPTED_BOUNDARY]:
            if not meta.tag_metas.has_key(tag_name):
                tag_meta = TagMeta(
                    tag_name,
                    TagValueType.NONE,
                    applicable_to=TagApplicableTo.IMAGES_ONLY,
                )
                meta = meta.add_tag_meta(tag_meta)
                need_updated = True

        if need_updated:
            meta = self.api.project.update_meta(self.project_id, meta)
            logger.info("Project meta updated with new tags.")

        return meta

    @property
    def tagging_mode(self) -> str:
        """
        Returns the selected tagging mode.
        """
        return self.mode.get_value()
