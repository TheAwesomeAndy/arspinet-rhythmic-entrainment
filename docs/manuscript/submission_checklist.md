# TNSRE submission checklist

Updated 2026-11-17.

## Limits and charges

**Page limit.** TNSRE submission guidelines (https://www.embs.org/tnsre/for-authors/submission-guidelines/,
read 2026-11-17), verbatim:

> 10 pages or less, not counting references. Manuscripts that exceed 10 pages in the template will not be
> admitted for review.

**Article processing charge, 2026: US$2,160.** The TNSRE guidelines page itself, read on 2026-11-17, still lists
only earlier years, verbatim: "For papers submitted in 2024, the APC is US$1995 plus applicable local taxes. For
papers submitted in 2025, the APC is US$2075 plus applicable local taxes." The 2026 figure comes from:

* IEEE's table "2026 Article Processing Charges (Updated:12/30/2025)", row "TNSRE  IEEE Transactions on Neural
  Systems and Rehabilitation Engineering  Full Open Access  $2,160.00" (IEEE Standard OA APC; CONCERT OA offer
  $1,728.00). Read from a copy hosted by a university library:
  https://jumper.ncue.edu.tw/file/downloadFile/2026%20IEEE%20Publication's%20APCs_Fully&Hybrid%20OA-2025.12.pdf
* DOAJ record for ISSN 1558-0210 (API, last updated 2026-09-17): APC maximum 2160 USD.

Confirm the 2026 APC in the submission system before paying. Per the guidelines page, IEEE members receive a
5 % discount and IEEE Society members 20 %; discounts cannot be combined and do not apply to students.

## Open items

- [ ] **Rewrite source integration.** The 11-page rewrite of `main.tex` is not in the repository. Apply
      `pending_submission_edits.md` (A1-A2, B3-B4, C5-C6, D7, E8-E10) to it. Then rebuild and confirm the body
      ends within 10 pages, with 0 undefined references and 0 overfull boxes. Trim to offset the additions
      (about 17 lines).
- [ ] **Author and affiliation block.** Left to the authors; nothing is filled in by the pipeline.
- [ ] **Zenodo DOI.** Re-point and push the tag `v1.0-tnsre-submission` once the manuscript edits are in. Then
      archive that release on Zenodo, and put the DOI into the code-availability statement (placeholder
      `doi:10.5281/zenodo.XXXXXXX`), `CITATION.cff` and `README.md`.
- [ ] **Cover-letter signature.** `cover_letter.md` ends with a placeholder; add name, affiliation and contact
      details, and the date.
- [ ] **Funding line.** The `\thanks` stub carries "This work was supported in part by XXXX."; replace with the
      funding statement (or remove it if there is none).

## Done in this pass (for reference)

- Identifiability procedure as a documented entry point (`weineck/identifiability_procedure.py`) with a
  regression test that reproduces a committed cell exactly (`weineck/tests/`).
- Ethics statement of the original study located (Ethics Council of the Max Planck Society, Application No:
  2019_04; staged in `pending_submission_edits.md`, E8).
- References added since `d0f87cc` listed for verification in `new_refs_to_verify.md`.
