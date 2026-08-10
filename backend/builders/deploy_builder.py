"""
Deployment payloads for `deployCheckForWarnings` and `deployBusinessEntity`.

Ported from aux_web_version/backend/builders/deploy_builder.py, with
`datastore_uri` injected rather than hardcoded — it is environment-specific.

AUX fires both calls and DISCARDS the warnings response entirely
(aux_web_version/backend/pipeline.py:739 — never assigned, never checked). Here
the two payloads are returned separately so the run engine can call the warnings
endpoint FIRST, show what QAD said at the stage-5 gate, and deploy only on
approval. The warnings are the whole point of that gate.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from builders.identity import AppIdentity, resolve


def build_deploy_payload(bc_pascal: str,
                         identity: Optional[AppIdentity] = None) -> Dict[str, Any]:
    ident = resolve(identity)
    entity_uri = ident.entity_uri(bc_pascal)

    return {
        "status": "built",
        # Called first. Response must be surfaced, not discarded.
        "check_warnings": {
            "entityURI": entity_uri,
            "isInitialDataLoaded": False,
        },
        # Called only after the user approves.
        "deploy": {
            "entityURI": entity_uri,
            "appURI": ident.module_uri,
            "dataStoreURI": ident.datastore_uri,
            "isInitialDataLoaded": False,
            "allowActivityTracking": False,
        },
        "summary": {
            "bc_pascal": bc_pascal,
            "entity_uri": entity_uri,
            "datastore_uri": ident.datastore_uri,
        },
    }
