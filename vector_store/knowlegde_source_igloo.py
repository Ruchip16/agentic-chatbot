import logging
import os

import pyigloo

from constants import SOURCE_RESPOSITORY_PATH

logger = logging.getLogger(__name__)


class Igloo:
    """Class for connecting to igloo."""

    def __init__(self, endpoint: str):
        """Initialize."""
        self.endpoint: str = endpoint
        # TODO: Raise an error if any of these are None
        self.api_user: str = os.environ.get("IGLOO_USER", None)
        self.api_pass: str = os.environ.get("IGLOO_PASS", None)
        self.api_key: str = os.environ.get("IGLOO_API_KEY", None)
        self.access_key: str = os.environ.get("IGLOO_ACCESS_KEY", None)

        info = {
            "ACCESS_KEY": self.access_key,
            "API_KEY": self.api_key,
            "API_USER": self.api_user,
            "API_PASSWORD": self.api_pass,
            "API_ENDPOINT": self.endpoint,
        }
        self.session = pyigloo.igloo(info=info)

    def get_object(self, object_id: str):
        """Get a single object."""
        result = self.session.objects_view(objectid=object_id)
        return result

    def get_children_from_parent(
        self,
        parent_path: str | None = None,
        parent_object_id: str | None = None,
        recursive: bool = False,
    ):
        """Get all children from a parent url path."""
        # Get the parent object id
        if parent_path is None and parent_object_id is None:
            raise ValueError("Must set one of 'parent_path' or 'parent_object_id'")
        if parent_path is not None:
            logger.info(f"Fetching objects under path {parent_path}")
            response = self.session.objects_bypath(path=parent_path)
            if response is None:
                raise ValueError(
                    f"Parent path {parent_path} does not exist. Please check the path and try again."
                )
            parent_object_id = response["id"]

        # Get all the children
        all_children = []
        for child in self.session.get_all_children_from_object(
            parent_object_id, pagesize=100
        ):
            children = [child]
            if recursive:
                try:
                    child_object_id = child["id"]
                    childs_children = self.get_children_from_parent(
                        parent_object_id=child_object_id, recursive=True
                    )
                except TypeError:
                    continue
                children.extend(childs_children)
            all_children.extend(children)

        return all_children

    def get_document_binary(self, document_id: str) -> bytes:
        """Get the contents of a document."""
        # Send a request to the /documents/document_id/view_binary endpoint to get file contents
        endpoint = self.session.endpoint
        api_root = self.session.IGLOO_API_ROOT_V1
        url = "{0}{1}/documents/{2}/view_binary".format(endpoint, api_root, document_id)
        headers = {b"Accept": "application/json"}
        response = self.session.igloo.get(url=url, headers=headers)
        return response.content

    def get_attachments(self, object_id: str):
        """Get all attachments on an object."""
        # Get page metadata
        page = self.get_object(object_id=object_id)
        # List the attachments
        page_attachments = self.session.attachments_view(objectid=object_id)
        items = page_attachments.get("items", [])
        # Get information about each attachment
        attachments = []
        for item in items:
            document_id = item["ToId"]
            document_metadata = self.session.objects_view(document_id)
            document_binary = self.get_document_binary(document_id=document_id)
            attachment = document_metadata | {
                "contentBinary": document_binary,
                "attachedToHref": page["href"],
            }
            attachments.append(attachment)
        return attachments


def fetchall(
    url_fragment: str,
    recursive: bool = False,
    attachments: bool = True,
    metadata: dict = {},
    **kwargs,
):
    """
    Fetch pages from the Source.

    Args:
    ----
        url_fragment (str): URL fragment to pull all children from.
            For example, to pull all pages under https://source.redhat.com/departments/operations/travel,
            set url_fragment="/departments/operations/travel"
        recursive (bool): Whether or not to recurse into child pages. Defaults to False.
        attachments (bool): Whether or not to fetch page attachments. Defaults to True.
        metadata (dict): Metadata to attach to each page chunk. Defaults to {}.
        **kwargs: Additional arguments not used.

    """
    endpoint = "https://source.redhat.com/"

    # Connect to Igloo
    igloo = Igloo(endpoint=endpoint)

    # Get all documents under parent path
    fragment_documents = igloo.get_children_from_parent(
        parent_path=url_fragment, recursive=recursive
    )

    # Fetch all attachments
    if attachments:
        for document in fragment_documents:
            object_id = document["id"]
            object_attachments = igloo.get_attachments(object_id=object_id)
            fragment_documents += object_attachments

    # Convert to files and save locally
    meta_lookup = {}
    for document in fragment_documents:
        if document["isPublished"] and not document["IsArchived"]:
            # Write the document in it's URL path locally
            doc_href: str = document.get("attachedToHref", document["href"])
            extension = document.get("fileExtension", ".html")
            doc_title: str = document["title"].replace(extension, "")
            doc_path = doc_href.lstrip("/") + "/" + doc_title + extension
            path = SOURCE_RESPOSITORY_PATH / doc_path
            folder_path = path.parent
            if document["content"].strip() != "" or "contentBinary" in document:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                if "contentBinary" in document:
                    with open(path, "wb") as f:
                        f.write(document["contentBinary"])
                else:
                    with open(path, "w") as f:
                        f.write(document["content"])

            # Save metadata
            used_columns = ["content", "contentBinary"]
            file_metadata = {
                key: value for key, value in document.items() if key not in used_columns
            }
            file_metadata["url"] = endpoint + doc_href.lstrip("/")
            file_metadata = file_metadata | metadata
            meta_lookup[path] = file_metadata

    return meta_lookup
