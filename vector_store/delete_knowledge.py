import logging
import shutil

from constants import KNOWLEDGE_REPOSITORY_PATH

logger = logging.getLogger(__name__)


def delete_knowledge():
    """Delete everything in the knowledge folder."""
    if KNOWLEDGE_REPOSITORY_PATH.exists():
        logger.info(f"Deleting {KNOWLEDGE_REPOSITORY_PATH}")
        shutil.rmtree(KNOWLEDGE_REPOSITORY_PATH)
