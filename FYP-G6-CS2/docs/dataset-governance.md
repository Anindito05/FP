# Dataset governance

## Policy

`data/datasets.yaml` is the registry for classifier inputs. Tier A means clinician annotation or a clinical instrument with documented protocol. Tier B means peer-reviewed research labels without clinician validation. Tier C means unvalidated sources such as scrapes or unvetted dumps and is forbidden. The project never downloads corpora; adapters read only human-provided files under `data/raw/<id>/`.

All shipped candidates are disabled and `verified_by_human: false`. Tier A examples may contribute risk levels only after a human obtains the data, reviews usage terms, completes all `TODO_VERIFY` citation/license/annotation/schema fields, and verifies the label mapping. Tier B examples may contribute emotion/mood only when verified and `ALLOW_PEER_REVIEWED_NON_CLINICAL=true`; they never contribute risk labels. Health and evaluation must state “emotion labels are peer-reviewed but not clinician-validated”. Tier C and unverified entries are refused.

Candidates are C-SSRS-annotated Reddit risk examples, UMD/CLPsych Reddit suicidality data, DAIC-WOZ, CLEF eRisk, GoEmotions, EmpatheticDialogues, Dreaddit, and CAMS. Citation, license and annotation details remain `TODO_VERIFY` until checked against original papers and provider terms. Obtain restricted datasets through the provider's current request or agreement process. Never commit restricted data.

C-SSRS ideation/behaviour structure, PHQ-9 item 9, and WHO mhGAP emergency guidance inform taxonomy and escalation only. They are not training examples. A clinician must review `app/ml/levels.py`, `data/level_mapping.yaml`, and crisis wording.

## Human onboarding checklist

Obtain permission, keep source files outside version control, verify consent/de-identification and allowed uses, document annotation protocol and schema, map labels explicitly, and have a second reviewer confirm. Set `verified_by_human` only afterward. Ensure Tier B adapters emit emotion only. Build a versioned index and retain its manifest.

## Limitations and reporting

Retrieval over clinician-annotated examples is not a clinically validated classifier. Dataset shift, annotator disagreement, missing context, language variation, and the synthetic demo are substantial limits. Report per-dataset and per-tier metrics with splits grouped by user/thread; do not combine Tier B emotion metrics with Tier A risk claims. Synthetic scripts are pipeline checks, not effectiveness results. This is not a clinical tool.
