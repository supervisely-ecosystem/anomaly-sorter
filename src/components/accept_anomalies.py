from collections import defaultdict
from typing import Optional

from src.components.base_element import BaseElement
from supervisely.annotation.tag_meta import TagApplicableTo, TagMeta, TagValueType
from supervisely.api.api import Api
from supervisely.api.image_api import ImageInfo
from supervisely.api.module_api import ApiField
from supervisely.app.exceptions import show_dialog
from supervisely.app.widgets import Button, SolutionCard
from supervisely.project.project_meta import ProjectMeta
from supervisely.sly_logger import logger
from supervisely.solution.base_node import SolutionCardNode
from supervisely.task.progress import tqdm_sly

TAG_ACCEPTED = "_accepted"
TAG_ACCEPTED_BOUNDARY = "_accepted_boundary"


class AcceptAnomaliesNode(BaseElement):
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
        self.api = api
        self.project_id = project_id
        self._validate_project_meta()
        self.card = self._create_card()
        self.node = SolutionCardNode(content=self.card, x=x, y=y)

        super().__init__(*args, **kwargs)

    def _create_card(self):
        return SolutionCard(
            title="Tag Accepted Anomalies",
            tooltip=self._create_tooltip(),
            width=250,
            tooltip_position="right",
        )

    def _create_tooltip(self):
        return SolutionCard.Tooltip(
            description=f"""Node that automates the tagging of accepted anomalies in a collection of images.
            Users review images sorted by specified metrics and manually tag 'start' and 'end' images to mark the boundaries of accepted anomalies.
            This node detects these boundaries based on user tags and tags all images within the boundaries, helping to efficiently identify and accept true anomalies while excluding false positives.""",
            content=[self.run_btn],
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

        @btn.click
        def on_run_click():
            self.run()

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
        for idx, img in enumerate(sorted_images):
            img: ImageInfo
            if self._has_tag(img, tag_accepted):
                remove_tags[img.dataset_id].append(img.id)
            if self._has_tag(img, tag_boundary):
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
        if start is not None and end is not None:
            logger.info(f"Tagging images from index {start} to {end} as accepted anomalies.")
            for i in range(start, end + 1):
                img = sorted_images[i]
                tags_json.append({"tagId": tag_accepted.sly_id, "entityId": img.id})

        if tags_json:
            self.api.image.tag.add_to_entities_json(self.project_id, tags_json, log_progress=True)
            logger.info(f"Tagged {len(tags_json)} images as accepted anomalies.")
        else:
            logger.info("No images to tag as accepted anomalies.")

        self.hide_in_progress_badge()
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
