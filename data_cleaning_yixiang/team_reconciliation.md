# Preliminary comparison for team reconciliation

This comparison was written **after** Yixiang's independent implementation and
first full-data validation. It is a review aid, not evidence of team agreement.
No teammate's code was copied into this implementation and no shared branch was edited.

Source reviewed: `origin/Qiyue-Zhao` at
`d8a88af7b247005e345fb8b60b1b76d308269593`, specifically the README,
`clean_anthropic.py`, and `merge_data.py`. Teammate results below are reported by
that branch; they were not independently rerun here.

| Topic | Yixiang's verified output | Qiyue's published workflow | Reconciliation needed |
|---|---|---|---|
| BLS scope | 11,847 CA area-occupation rows | README reports 11,847 rows | Counts agree; compare actual keys/values before claiming identical data |
| AI scope | 149,421 occupation-metric rows across two products, multiple geography/hierarchy levels and both months | 5,121 Claude.ai leaf rows: global autonomy/augmentation/automation plus CA usage share | Different scopes explain why totals are not directly comparable; choose the team's required metrics explicitly |
| Integrated grain | 11,847 BLS rows with May 2026 CA share context | 67,194 reported long-format rows, with multiple periods/metrics per area-occupation | Both grains can be intentional; never sum repeated employment over the long table |
| Occupation mapping | Published leaf shares grouped by six-digit prefix; mapping marked provisional | Exact O*NET reference lookup, then `.00` base occupations for direct BLS matching | Review specialized suffix occupations and official taxonomy correspondence; compare excluded/unmatched keys |
| Source references | Original ZIP and CSV hashes; no separate O*NET reference input | O*NET 31.0 occupation reference included | Obtain the exact O*NET file and verify relevant version crosswalk before approving mapping |
| Validation | Full raw-file profiles, independent all-row BLS/AI verification, fresh notebook hash comparison | Notebook/README describe duplicate, missing, merge, record and rerun checks | Compare evidence, not just sample appearance or a successful run |

The inspected `Leo` and `yoona-zhang` branch trees did not contain a Module 6
cleaning directory at the fetched snapshot. This is not a claim about unfinished
work elsewhere. No conclusion about other members' results has been invented.

## Outstanding team decisions

1. Agree which source scopes, periods, metrics and final row unit support Vision A.
2. Verify the occupation mapping and explain which specialized codes are retained,
   aggregated, or excluded; review both unmatched-key exports.
3. Compare full BLS keys/values across members, then reconcile any differences.
4. Approve the final group checklist and upload the PDF/ZIP in Gradescope.

Until those steps occur, the supplied PDF remains an individual evidence report
with the mapping issue explicitly marked Unresolved.
