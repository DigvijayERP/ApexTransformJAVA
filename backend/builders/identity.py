"""
App identity and every URI pattern derived from it.

In the AUX reference implementation these live as module-level constants
repeated across five files — bc_builder.py:4-6, form_builder.py:3-4,
view_builder.py:4-6, event_handler_builder.py:3, deploy_builder.py:3-4 — and the
urn patterns themselves are re-spelled inline in each builder. That means the
app can only ever be `com.extensions.customapp`, and a change to a urn shape has
to be made in four places without any of them knowing about the others.

Here identity is injected and the patterns live once.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core import config


@dataclass(frozen=True)
class AppIdentity:
    """The four values every payload is built from.

    `module` and `module_short` derive mechanically from the app URI.
    `app_name` must match QAD's own app list, and `datastore_uri` is
    environment-specific — neither can be defaulted.
    """
    module: str
    module_short: str
    app_name: str
    datastore_uri: str

    @classmethod
    def from_config(cls) -> "AppIdentity":
        ident = config.app_identity()
        return cls(
            module=ident["module"],
            module_short=ident["module_short"],
            app_name=ident["app_name"],
            datastore_uri=ident["datastore_uri"],
        )

    # ── URI patterns. Every one of these is exercised by a QAD payload. ───────
    @property
    def module_uri(self) -> str:
        """Doubles as appURI — AUX sets both to the same value."""
        return f"urn:app:{self.module}"

    def entity_uri(self, bc: str) -> str:
        return f"urn:be:{self.module}.{bc}.I{bc}"

    def bdoc_uri(self, bc: str) -> str:
        return f"urn:bd:{self.module}.{bc}.{bc}"

    def cached_bdoc_uri(self, bc: str) -> str:
        """Note the I-prefix on the last segment — it differs from bdoc_uri."""
        return f"urn:bd:{self.module}.{bc}.I{bc}"

    def view_meta_uri(self, bc: str) -> str:
        return f"urn:view:viewmeta:{self.module}.{bc}"

    def field_uri(self, bc: str, field_code: str) -> str:
        return f"urn:field:{self.module}.{bc}.I{bc}:{bc}.{field_code}"

    def browse_uri(self, bc: str) -> str:
        return f"urn:browse:bebrowse:{self.module}.{bc.lower()}"

    def hybrid_browse_uri(self, bc: str) -> str:
        return f"urn:view:hybridbrowse:{self.module}.{bc.lower()}"

    def browse_view_uri(self, bc: str) -> str:
        return f"urn:view:browse:{self.module}.{bc.lower()}"

    def maint_view_uri(self, bc: str) -> str:
        return f"urn:view:maint:{self.module}.{bc.lower()}"

    def meta_uri(self, bc: str) -> str:
        return f"urn:view:meta:{self.module}.{bc.lower()}"


# QAD platform constants. These name QAD's own objects, not ours, and are the
# same on every install — so they are NOT part of AppIdentity and must not
# become settings.
ENTITY_DEPLOYMENT_URI = "urn:be:com.qad.qra.metadatav3.IEntityDeployment:"
APP_MODULE_NAME = "qracore"
PLATFORM_NAME = "webui"


def resolve(identity: Optional[AppIdentity] = None) -> AppIdentity:
    """Every builder takes an optional identity so tests can inject one."""
    return identity or AppIdentity.from_config()
