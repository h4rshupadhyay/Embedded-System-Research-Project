# Independent review of the current FIR manuscript

Reviewed on 20 October 2026 against `research/fir-clarity-rewrite`, manuscript at commit `2f8dd5e`. Line references below refer to that revision of [manuscript.md](manuscript.md). This note combines an independent primary-source scientific review with the coordinating reviewer's separate numerical, timing and PDF checks. Earlier ratings, internal acceptance statements and agent self-reviews were not treated as validation.

## Verdict and scope

**Revision required for the Arm timing account; the central, explicitly model-relative energy conclusions remain credible within the inspected scope.** The concrete timing defect below changes derived cycle totals. It does not change the six-event energy equation or establish a failure of the arithmetic-control and specialization findings. The remaining issues concern precise comparison language and auditability. There is no basis here for a publication-acceptance probability or an assertion of field priority.

The manuscript now presents a bounded empirical case study: exact FIR arithmetic, a finite generated candidate set, one simulator/configuration, and established transformations. It explicitly disclaims a new FIR algorithm, a general selector, physical-energy validation, application prevalence and independent statistical sampling. Those acknowledged limits are not additional findings.

The scientific reviewer read the complete current manuscript and inspected the frozen protocol, representative generated direct/transposed/Hcub/CMSIS wrappers, pinned CMSIS helper code, and local Git chronology. Primary papers and official documentation were checked online as described below. No firmware rebuild, target simulation, new benchmark, graph search, or physical measurement was performed. This is not a complete proof of every generated C expression or a fresh reproduction of every saved binary.

## Actionable findings

### 1. P2 — The claimed Arm-table cycle formula undercounts return-by-POP

**Location:** manuscript lines 204–209; intervention cycle values at lines 540–548; Appendix A lines 796–822. Local implementation: [simulator.py](../../fir-baseline/simulator.py), lines 95–103 and 124–125.

Arm's cited DDI0432C Table 3-1 assigns `POP {…,PC}` **4 + N** cycles, where N includes PC. The manuscript's aggregate formula assigns this instruction **1 + N + 2 = 3 + N** when its data transfers contribute N reads and its control transfer contributes one taken branch. The coordinating reviewer checked that the pinned simulator counts those transfers individually and increments the branch count once; this is not a hidden extra branch event. [Arm Cortex-M0 TRM, §3.3, Table 3-1 and footnote c](https://documentation-service.arm.com/static/5e8e294afd977155116a6a5b).

The saved `pop_pc` microcheck already exposes the mismatch: `BL`, unconditional `B`, `PUSH {r4,lr}`, and `POP {r4,pc}` total 16 cycles under that table, but the current helper expects 15. This microcheck tests consistency with the implemented formula, not the correctness of that formula against Arm's table.

The coordinating reviewer also found 258 measured POP-to-PC executions in each of the four intervention rows. Adding this omitted term alone changes GCC15 general from 350,968 to 351,226 cycles, or 1366.638132 cycles/output instead of 1365.634241. Equal corrections cancel in those intervention cycle differences. All 280 admitted panel rows also contain this return form, with omitted correction per output ranging from 0.0175609756 to 2.0038910506 cycles; cancellation must not be assumed for other comparisons. The paper's modeled-energy equation uses separate fitted event weights and remains unchanged.

**Required change:** audit the executed instruction subset against the cited table, account for POP-to-PC explicitly, and regenerate affected cycle-only summaries from saved opcode counts. Alternatively, identify the present quantity as a simplified timing proxy and state its known discrepancy. Do not claim that adding this one term proves every other timing case correct. No new target execution is needed to demonstrate or address this omission in the saved rows.

### 2. P2 — Define what “identical generation budget” means

**Location:** manuscript lines 310–317, especially line 313; interpretive conclusions at lines 670–674 and 732–737.

Coefficients, numeric semantics and runtime block arguments can be matched concretely. “Generation budget” has no operational definition here. The wide designs use two direct partition recipes, whereas Hcub uses one fixed graph seed and emission schedule. Those disclosed choices can support a frozen finite-candidate comparison; they do not by themselves demonstrate equal search effort or comparably optimized implementations. Hcub's source paper optimizes addition/subtraction count and explicitly sets register-pressure optimization aside, reinforcing the need to identify the particular graph/schedule being tested. [Voronenko and Püschel, §1, “Other optimization metrics”](https://spiral.ece.cmu.edu/pub-spiral/pubfile/synth_28.pdf).

**Suggested change:** replace the ambiguous equality with the actual control: fixed generation recipes, the specified number of graph/partition alternatives, and no replacement based on observed target cost. Retain the existing finite-candidate limitation. This is a clarification request, not evidence that outcomes were cherry-picked or that the observed comparisons are invalid.

### 3. P3 — State the existential predicate's missing-data logic explicitly

**Location:** manuscript lines 338–346.

“No reversal among the complete wide conditions refutes that extension” is too broad if any required wide condition is unavailable. A witness establishes an existential claim; lack of a witness refutes it only when the entire required wide domain is assessed. The following missing-case sentence partly repairs this, but the two statements should not require reconciliation by the reader.

**Suggested change:** state three outcomes: at least one admitted wide witness supports the extension; zero witnesses with all required wide conditions complete refutes it; zero witnesses with required wide conditions missing leaves it unresolved. The frozen local [protocol](../panel-protocol.json), `comparison` field, supplies the predicate and the incomplete-panel rule. The actual result has all 32 wide conditions complete and 24 witnesses, so this wording issue does not alter that result. The eight unavailable native cases concern completeness of the larger panel.

### 4. P3 — Make two primary-source dependencies easier to inspect

**Location:** manuscript lines 247–254, 314–316 and references [2], [7], [9] at lines 857–860 and 885–894.

The manuscript correctly separates compiler/source eligibility from output agreement, but its GCC reference covers optimization options rather than the integer behavior relied on by the CMSIS packed helpers. The inspected helpers use signed shifts and signed conversions. GCC documents sign-extending signed right shift, modulo conversion to signed widths and its signed-left-shift extension; thus an ISO-C-only undefined-shift objection would be incomplete. [GCC 15.2, “Integers implementation”](https://gcc.gnu.org/onlinedocs/gcc-15.2.0/gcc/Integers-implementation.html).

**Suggested change:** cite the applicable versioned integer-semantics documentation and name these specific dependencies beside library eligibility. This improves proof auditability; no new arithmetic-safety defect was demonstrated. Reference [2] also has a directly hosted author-group manuscript at [SPIRAL's FIR paper](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf), which could supplement the author-uploaded ResearchGate link. The latter's full text was accessible during review; the directly hosted PDF was search-indexed but timed out on direct retrieval.

### 5. P3 — Keep result floats closer to the argument they support

**Location:** current [PDF](manuscript.pdf), pages 5–7; manuscript original-energy table at lines 388–397 and RAM-sensitivity Figure 2 at line 484.

The coordinating reviewer inspected the final PDF and found that §6's compiler discussion begins on page 5 before the main original-energy table (Table III) appears on page 6. Figure 2's RAM sensitivity appears on page 7 amid the intervention/panel progression. This delays evidence needed for the earlier argument; it is not a clipping or unreadable-content finding.

**Suggested change:** constrain those floats to their relevant results sections, then inspect the rendered page sequence. The manuscript does not require another numerical experiment to resolve this presentation issue.

## Core claims checked against primary sources

| Claim / local location | Check and conclusion |
|---|---|
| Configuration-specific CPU energy, lines 211–226 | Nikov et al., Tables 1–2, give exactly the six event definitions, the displayed 20 MHz/prefetch-off/zero-wait coefficients and 2.80% MAPE. Their §2.3 explains zero-intercept NNLS fitting and absorbed residuals; §2.5 explains correlations affecting weights. The manuscript's distinction between model arithmetic, fitted event contributions and physical-event prices is justified. The MAPE is not a confidence bound on these FIR pairwise rankings. [Primary paper](https://arxiv.org/html/2301.12806v1). |
| Incremental sharing rather than realization effect, lines 48–54, 174–186 and 437–445 | The displayed ordinary and Hcub sources retain the same suffix-state updates and final quantizer while changing constant-product expressions. This is a meaningful controlled implementation contrast. The result concerns the generated Hcub graphs and schedules, not every possible multiple-constant-multiplication implementation. The manuscript's finite-search qualification is necessary. [Hcub primary paper](https://spiral.ece.cmu.edu/pub-spiral/pubfile/synth_28.pdf); local [ordinary source](../sources/wide_lp2800/trans_const/b1/probe.c) and [Hcub source](../sources/wide_lp2800/trans_hcub_demand/b1/probe.c). |
| Wide versus fast CMSIS arithmetic, lines 247–254 and 310–316 | Pinned v1.14.4 FIR source documents wide accumulation and final shift/saturation; fast source uses a narrower accumulator and demands overflow control. Generated wrappers reverse coefficients. The native-array certificate can discharge overflow without scaling inputs. This does not discharge unrelated pointer-object aliasing, so preserving unresolved fast/block64 identities is defensible. [Standard FIR source](https://raw.githubusercontent.com/ARM-software/CMSIS-DSP/v1.14.4/Source/FilteringFunctions/arm_fir_q15.c), [fast FIR source](https://raw.githubusercontent.com/ARM-software/CMSIS-DSP/v1.14.4/Source/FilteringFunctions/arm_fir_fast_q15.c), local [protocol certificates](../panel-protocol.json). |
| Synthetic-array generation, lines 286–308 | SciPy 1.15.3 documents `(len(h)+1)//2` output length with `half=True` and an approximately square-root prototype magnitude response for the homomorphic method. The 95-to-48 construction and explicit application-filter disclaimer are appropriate. [Pinned SciPy documentation](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.minimum_phase.html). |
| Prior FIR generation and computation-order effects, lines 88–94 | Gačić et al. §4 explicitly compares time-domain rules having equal arithmetic cost but different computation order; their software generator and experiments predate this case study. This supports the manuscript's restrained framing. [Author-uploaded full text](https://www.researchgate.net/publication/2589071_Fast_Automatic_Software_Implementations_of_FIR_Filters). |
| Prior physically measured energy optimization, lines 90–94 | D'Alberto et al. §3.2 describes XScale board-current sampling and runtime/energy feedback to SPIRAL. Their platform and method do not validate the present Cortex-M0 estimates; the manuscript says so. [Author manuscript](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf). |
| Accuracy-constrained software word lengths, lines 83–86 | Ménard and Sentieys §§5.1–5.2 use SQNR constraints and processor instruction/data-transfer models. The manuscript correctly distinguishes that problem from a full-domain exact-output contract without claiming width selection itself is new. [Author-uploaded manuscript](https://www.researchgate.net/publication/220905057_DSP_Code_Generation_with_Optimized_Data_Word-Length_Selection). |
| Compiler intervention interpretation, lines 354–378 and 570–587 | GCC documents specialization-related optimization machinery, but current documentation cannot identify the historical pass responsible for a particular binary. Changing three callee uses of `b` to `1` is a concrete intervention under `b=1`; multiple emitted changes prevent exclusive assignment of all savings to rotation removal. The current wording maintains that distinction. [Official optimization documentation](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html). |

## Prospective status and evidentiary limits

The review independently compared the current `panel-protocol.json` with its payload at local commit `bf97665` and obtained the same SHA256, `d2b85b2580ec551efcbc457159ff9237482aa2f146417ed236bbd0c0aeb8646c`. That payload already contains the existential wide-cell reversal predicate, both nontransposed candidate sets and the unavailability rule. Git ancestry places it before measurement commit `6817998`. This supports the manuscript's local freeze account and is stronger evidence than a bare present-day hash. It is not an authenticated external preregistration or proof that no unrecorded observations ever existed. The manuscript appropriately calls the original four-cell rule retrospective.

The exact product-endpoint construction and conservative L1 prefix certificate at lines 134–143 are mathematically valid for independent signed-int16 samples. Representative direct source widens each completed partial before the final addition; representative transposed source widens before suffix additions when required. Finite output checks cannot replace full-domain source reasoning. This review did not reconstruct a complete proof for every graph primitive, all compiler extensions, all library paths or every generated binary.

De Coster et al.'s linked primary PDF could not be fully retrieved by the review browser; indexed primary text confirmed the paper's identity and bit-true-simulation topic, but the precise magnitude-analysis passage was not independently verified in full. [Linked primary manuscript](https://cecs.uci.edu/~papers/compendium94-03/papers/1998/isss98/pdffiles/1_2.pdf). This is an access limit, not a demonstrated miscitation. No exhaustive related-work or priority search was performed. Internal test passes, hashes and saved verification establish specific consistency properties; they do not establish authenticity, physical validity, novelty or publication suitability by themselves.

## Coordinating numerical and PDF review

The coordinating reviewer independently reconstructed all 280 admitted panel rows from saved raw stderr, without importing the project's numerical helpers. It checked each raw stderr SHA against the inventory, removed the closing marker from instruction counts, decoded the native multiplication count from the Thumb opcode bucket, and applied the six stated decimal coefficients as integer weights. Every reconstructed total matched both `energy_weighted_integer` and `energy_nj` in the saved inventory.

Those reconstructions reproduce the manuscript's central panel counts: 24 reversals among 32 complete wide conditions, Hcub above ordinary transposition in all 32, and disjoint all-form winners of 16 ordinary, eight first direct, four balanced direct, four Hcub and eight first/balanced ties. Independent recomputation of all three coefficient L1 sums, full-sum endpoint intervals and admitted native-group prefix bounds also agrees with the manuscript.

Reconstruction of the four intervention performance rows gives 8.85647867% and 31.44305832% modeled-energy reductions for GCC10 and GCC15, respectively, and compiler gaps of +70469.699925 and −11857.443121 nJ. The cycle exception in finding 1 comes from a separate comparison of the cited Arm table with simulator source, saved opcode counts and disassembly. All four intervention rows contain the same 258 POP-to-PC count, so that particular correction cancels in their reported cycle differences. Broader cycle-table corrections still require the indicated subset audit.

The coordinating review included the final PDF's figures, table legibility and float order; the specific remaining presentation issue is finding 5. Its reconstruction result is a saved-evidence consistency audit, not a new target run, complete source/binary correctness audit, physical model validation or re-execution of the full portable artifact suite.

## Resolution, 20 October 2026

All five actionable findings are addressed in the current revision:

1. A separate [version 2 timing report](../timing/README.md) adds the measured
   POP-to-PC count and rejects unsupported scalar instructions. Its bound
   saved-data reconstruction covers 20 original, 280 panel and four intervention
   identities, preserving eight unavailable panel cases. All 24 affected paper
   cycle cells agree with that report; energies are unchanged. The literal
   BL/B/PUSH/POP-PC sequence gives 16 cycles under the correction and 15 under
   the frozen historical helper, which remains a superseded historical artifact.
2. Section 4.4 defines the two direct partition recipes and single fixed Hcub
   graph/emission schedule, prohibits outcome-based replacement and explicitly
   disclaims equal optimization effort or exhaustive search.
3. Section 4.4 states support, refutation and unresolved outcomes for the
   existential predicate separately. Missing native cases remain distinct from
   the complete wide domain.
4. Section 4.2 names the CMSIS helpers' signed-right-shift, signed-conversion
   and signed-left-shift dependencies. Reference [12] links both GCC 10.3 and
   GCC 15.2 integer-semantics documentation. Reference [2] adds the author-group
   manuscript location; direct retrieval timed out, so that addition does not
   claim a new full-text verification.
5. Principal Tables III/IV now appear inline on page 5. Figure 2 is on page 6,
   before the compiler section on page 7. Intervention Tables VIII/IX precede
   the panel section on page 8. The panel evidence finishes before the
   discussion on page 10. Final references are balanced on page 12.

Fresh host verification passes 249 tests with no skips; report regeneration is
byte-identical, and a relocated 920-file copy verifies with `PATH=/nonexistent`.
All 19 protected payloads from the preceding clarity validation retain their
recorded SHA-256. The historical archive and first paper are unchanged.
The coordinator inspected every final PDF page; the TeX output has no overfull
boxes. Exact current hashes are in [timing-review-validation.json](timing-review-validation.json).

One independent fresh-context reviewer returned PASS with zero actionable
Critical, Important or Minor findings. Using a separate standard-library
calculation, it reconstructed all 304 raw timing/energy rows and verified every
bound stderr/disassembly/binary hash and all 24 changed paper cells. It found
no ordering change among 680 panel pairs, 40 original pairs or two intervention
pairs, and independently ran the eight focused tests and production `--verify`.
It checked the official Arm table and both GCC documentation versions and
inspected all 12 pages of the preceding final-layout render. The coordinator's
subsequent bibliography balancing changed only page 12, which was inspected
again along with the full final render.

The reviewer declined to infer physical timing/energy validity, fresh target
reproduction, comprehensive arithmetic/compiler correctness or publication
suitability from this correction. Those boundaries remain appropriate: this
revision corrects a saved-data timing account and its presentation, and adds
no evidence for those broader claims. The independent reviewer performed no
target execution, compilation, graph regeneration or repository edits. It
inspected the coordinator's full-suite output but did not rerun that full suite.
