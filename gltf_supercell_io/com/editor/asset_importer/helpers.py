import bpy
import shutil
import tempfile
from bpy.app.handlers import persistent
from ...net.asset_request import (
    AssetRequest,
    AssetRequestServer,
    clean_asset_fetch_cache,
    list_servers,
    list_versions,
)

tempdir = tempfile.mkdtemp(prefix="sc-gltf-io-browser")


def get_version_items(self, context):
    props = context.scene.sc_asset_browser
    if not props.game:
        return []

    request = AssetRequest(
        game_server=AssetRequestServer(props.game),
    )

    items = []
    versions = list_versions(request)
    if versions is None:
        return items

    for i, data in enumerate(versions):
        version = data["version"]
        items.append(
            (
                version,
                version,
                "",
                i,
            )
        )

    return items


def get_game_items(self, context):
    items = []
    games = list_servers()
    if games is None:
        return items

    for i, data in enumerate(games):
        name = data["name"]
        code = data["codename"]
        items.append(
            (
                code,
                name,
                "",
                i,
            )
        )

    return items


def cleanup_temporary_files():
    shutil.rmtree(tempdir, ignore_errors=True)


def clean_asset_browser_cache():
    clean_asset_fetch_cache()
    cleanup_temporary_files()


@persistent
def refresh_handler(dummy):
    bpy.ops.supercell.assets_refresh()  # type: ignore
