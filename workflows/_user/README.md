This directory is a local convention only. Live private graphs live on `${COMFY_OUTPUT_DIR}/comfy-user/default/workflows/_user/`. Do not commit contents.

Save As `_user/` in Comfy. If you Save a new App or duplicate under live `_lab/`, the next `start` moves that extra into `_user/`. An in-place Save of a shipped lab graph is copied to `_user/_rescued/`, then `_lab/` is restored from git. Catalog updates do not clone shipped `_lab` graphs into this folder. If `_rescued/` already holds hundreds of lab copies from older starts, delete that folder and keep the rest of `_user/`.
