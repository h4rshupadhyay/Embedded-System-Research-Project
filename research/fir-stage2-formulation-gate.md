# Stage 2 FIR formulation gate: the proposed state loses instruction constraints

20 October 2026. Bounded mathematical/literature gate; no optimizer, generated
kernel, target execution or new performance measurement.

## Core decision and closest-method comparison

**No-go for implementing a new method on this H1 claim.** Even with one output
and no sample reuse, equal `(tap position, certified range, live mathematical
values)` can have different minimum continuation costs because accumulator
locations differ. Appendix A proves this for an abstract machine, not Cortex-M0
or GCC. Restoring complete suffix-relevant information yields standard
dominance, with no established FIR-specific search reduction. Other structural
rules remain possible; the [Stage 1 case study](fir-paper/manuscript.md) stands.

**Problem.** Given integer `h[0:N)`, independent samples `x_k∈[l,u]∩Z`, fixed
widths `w,W,r`, shift `q`, instructions/storage `A` and positive symbolic costs
`c`, choose contiguous partition `Π`, schedule `σ`, instructions `a` and
locations `ρ`. Family `F` computes one output, groups/taps in increasing order,
without interleaving or recomputation: one native accumulator per group, exact
widening of completed groups, wide reduction, one final quantizer. Only cuts
and those reductions may change the arithmetic graph. Define

\[
\begin{aligned}
L_k&=\min(h_k l,h_k u),& U_k&=\max(h_k l,h_k u),\\
I_{a,j}&=\left[\sum_{k=a}^{j-1}L_k,\sum_{k=a}^{j-1}U_k\right],\\
\min_{\Pi,\sigma,a,\rho}\ C&=\sum_{o\in\sigma}c(a_o),&
Q(s)&=\operatorname{clip}_{r}\!\left(\left\lfloor s/2^q\right\rfloor\right).
\end{aligned}
\]

Products, group prefixes and wide-reduction prefixes must fit their widths;
require `y=Q(Σ h_k x_k)` for every input. The candidate property is equal minimum
suffix cost for equal `s=(i,I,L)`, permitting one cheapest prefix per key. Grant
the key its partition branch, exact symbolic live identities and tight
intervals; it still omits `ρ`. The claim concerns this model, not compiled cost.

The same variables distinguish **what can be expressed** from **how efficiently
it is searched**:

| Closest method | Translation into `Π,σ,a,ρ`, legality and cost | Consequence for H1 |
|---|---|---|
| Ménard–Sentieys (2004), §§4–5.4, Fig. 3 | Supplied CDFG; selects widths/instructions `a` for estimated time under SQNR; models arithmetic/transfers. Branch-and-bound uses compatibility and partial cost/accuracy bounds. No variable `Π` in the inspected formulation. | Width search/pruning exist; SQNR differs from exactness. Outer enumeration of grouped graphs is conceivable: neither equivalent FIR recurrence nor expressiveness impossibility is established. Changing the predicate supplies no search advance. [Manuscript](https://www.researchgate.net/publication/220905057_DSP_Code_Generation_with_Optimized_Data_Word-Length_Selection). |
| SPIRAL FIR (2003), §§2–5, equations 12–15 | Decomposition/`σ` analogues: overlap-add, overlap-save and blocking. Searches rules/coding choices, including dynamic programming, using measured runtime. Inspected rules supply neither our `w,W,Q` certificate nor this `ρ` state. | FIR search/locality are established. The square-block rule does not demonstrate every range-selected disjoint `Π`; this proves neither inability to express them nor an efficiency separation. [Manuscript](https://www.researchgate.net/publication/2589071_Fast_Automatic_Software_Implementations_of_FIR_Filters). |
| Unison (2018 manuscript), §§3–8 | Supplied operation graph; register `ρ`, allocation-relevant alternative instructions `a`, issue cycles `σ`; register-class/interference/dependency/resource constraints and spill/split copies. | Expresses the lost location constraints for fixed graphs; does not establish our partition search/range theorem. General instruction selection is explicitly excluded (§3). Adding familiar constraints establishes no faster method. [Manuscript](https://arxiv.org/pdf/1804.02452). |

**Surviving contribution:** “In family F/model C below, tight ranges and live
symbolic values do not make `(i,I,L)` sufficient; complete-state equivalence
supports ordinary dominance without an established FIR-specific search gain.”
This negative result is falsified by a same-cost legal update from `r1`, or by
showing locations were already in the proposed key. Repaired dominance fails
if equal keys retain differently legal/priced suffixes.

The investment gates are distinct:

- **Originality: not passed.** No new recurrence/pruning rule; combining known
  ingredients or ordinary contiguous-partition DP establishes none.
- **Correctness: coarse state fails; repair is conditional.** Witness scope is
  its explicit instruction/storage family.
- **Utility: unresolved.** No proven search reduction, equal-budget advantage or
  GCC-cost relation. Before implementation, a future rule needs justified
  compression and a predeclared matched-quality/equal-budget value criterion.
- **Access: decisive text obtained; priority unresolved.** This targeted reading
  proves no literature-wide absence. Access is not the reason for this no-go.

## Appendix A. Hand-worked exact instance and state collision

Use `h=(3,−2,3)`, independent `x_0,x_1,x_2∈{−2,−1,0,1}`, native signed
`w=4` (`[−8,7]`), fixed reduction `W=6` (`[−32,31]`), and
`Q(s)=clip_[−2,1](floor(s/4))`. Six bits are a specified available width, not
the minimum: signed five bits would already contain the full sum. This is a
small analytic domain, not the project's int16 performance workload.

All nonempty contiguous groups and **all their accumulation prefixes** are:

| Group `[a,b)` | Prefix intervals in tap order | Native legal? |
|---|---|---|
| `[0,1)` | `[−6,3]` | Yes |
| `[1,2)` | `[−2,4]` | Yes |
| `[2,3)` | `[−6,3]` | Yes |
| `[0,2)` | `[−6,3]`, `[−8,7]` | Yes |
| `[1,3)` | `[−2,4]`, `[−8,7]` | Yes |
| `[0,3)` | `[−6,3]`, `[−8,7]`, `[−14,10]` | No |

The intervals are tight because each tap uses a distinct independent sample.
The legal partitions are exactly `[0,1)|[1,3)`, `[0,2)|[2,3)` and the three
singletons. The empty accumulator has `[0,0]`. Products have respectively
`[−6,3]`, `[−2,4]`, `[−6,3]`. A symmetric `max|x| Σ|h|` certificate would give
10 for each two-tap group and would not admit signed four bits; the sign-aware
interval above, not that coarser certificate, is used here.

For both schedules fix the same legal branch `Π=[0,2)|[2,3)`; failure even
conditional on this branch suffices to reject its coarse continuation-state
claim. Put `a_0=3x_0`, `a_{01}=3x_0−2x_1`, `b=3x_2`. Widen `a_{01}` before
adding it to the wide `Z=0`, then widen `b` before the second wide addition.
The wide prefixes are `[0,0]`, `[−8,7]`, `[−14,10]`; no native addition of
`a_{01}+b` occurs. Only then apply `Q`. For `x=(−1,0,0)`, `S=−3` gives `−1`
by floor, so truncation toward zero would be wrong. At `(−2,1,−2)` the sum is
`−14`; at `(1,−2,1)` it is `10`.

**Fully specified cost/storage model C.** Execution is sequential, with no
latency, pipeline, address-update or cache state. Inputs are immutable memory
at fixed addresses; constants are instruction immediates. There are two narrow
registers `r0,r1`, one separate sample scratch `s`, and separate wide registers
`Z,T`; wide registers cannot hold an unfinished native accumulator. Instructions
are: `ZERO Z` (cost `z`), `LD x_k→s` (`ℓ`), `MUL h_k,s→rj` (`m`, either `j`),
`MAC h_k,s,r0→r0` (`a`, only `r0`), `MOV r1→r0` (`μ`),
`EXT rj→T` (`e`, exact sign-extension of a completed group),
`WADD Z,T→Z` (`d`), final `Q Z→y` (`q_c`), and `STORE y` (`o`). Each symbol is
strictly positive. There are no other instructions, spills, cross-class moves
or rematerialization; every sample is loaded once and every product computed
once. Initial multiplication may initialize either narrow register; extending
an unfinished group to avoid its remaining native MAC is outside `F`.

This deliberately irregular abstract repertoire exposes an instruction-class
constraint; its costs are **not Cortex-M0 instruction counts, cycles or energy**.
Homogeneous interchangeable accumulator registers would remove this particular
collision. The general need to encode such constraints is already explicit in
Unison's register-class constraint C3 (§4.2), cited above.

Here is every instruction boundary's live mathematical data. Superseded values
die at last use; fixed input memory and constant addresses are implicit and
identical. `L` means mathematical values that still have a consumer, regardless
of physical location; neither schedule spills, so both the all-live and
resident-only interpretations give the same collision.

| Step | Schedule S0 | Schedule S1 | Live values after step |
|---|---|---|---|
| 1 | `ZERO Z` | Same | `{Z=0}` |
| 2 | `LD x0→s` | Same | `{Z=0,x0}` |
| 3 | `MUL 3,s→r0` | `MUL 3,s→r1` | `{Z=0,a0}`: collision point |
| 3a | No instruction | `MOV r1→r0` | `{Z=0,a0}` |
| 4 | `LD x1→s` | Same | `{Z=0,a0,x1}` |
| 5 | `MAC −2,s,r0→r0` | Same | `{Z=0,a01}` |
| 6 | `EXT r0→T` | Same | `{Z=0,T=a01}` |
| 7 | `WADD Z,T→Z` | Same | `{Z=a01}` |
| 8 | `LD x2→s` | Same | `{Z=a01,x2}` |
| 9 | `MUL 3,s→r0` | Same | `{Z=a01,b}` |
| 10 | `EXT r0→T` | Same | `{Z=a01,T=b}` |
| 11 | `WADD Z,T→Z` | Same | `{Z=S}` |
| 12 | `Q Z→y` | Same | `{y}` |
| 13 | `STORE y` | Same | `{}` |

Both schedules have three sample reads, one output write and zero spill
transfers. S0 has 13 abstract instructions; S1 has 14. Their symbolic costs are

\[
C_0=z+3\ell+2m+a+2e+2d+q_c+o,\qquad C_1=C_0+\mu.
\]

After step 3, both prefixes cost `z+ℓ+m`; both have `i=1`, active range
`[−6,3]`, identical exact symbolic live values and the same unexecuted arithmetic
graph. From S0 the **minimum** continuation cost is
`K=2ℓ+m+a+2e+2d+q_c+o`. Each counted instruction is mandatory for the fixed
branch and its two remaining products, two completed-group reductions and final
output. The displayed suffix attains this lower bound. From S1 the next native
update requires `r0`; the only legal way to transfer the unfinished value from
`r1` is the positive-cost `MOV`. Its minimum is therefore **exactly `K+μ`**,
attained by the displayed suffix. These are minima from reachable states, not
two arbitrarily inefficient suffixes. A location-free value function cannot
assign both answers to the same key.

If equal-cost projected prefixes are merged arbitrarily, retaining only the
S1 prefix loses the best continuation for this fixed-partition branch. This
does not independently prove that any particular tie rule fails, that an
unequal-prefix-cost dominance rule fails, or that the optimum over all three
partitions is lost. It refutes the asserted general sufficiency of this key.

**What repair actually proves.** Let `s*` identify the residual operation graph
with consumer progress, group/width/interval identities, every live symbolic
value's location, and all instruction-relevant machine state. In C, addresses
are fixed and readiness is trivial; richer models would need their relevant
storage/address/readiness information too. If two prefixes have identical
`s*`, every legal suffix of one is a legal suffix of the other with the same
cost. Appending the cheaper prefix to any such suffix cannot increase total
cost. This proves “keep the cheaper prefix” for identical full states by direct
suffix substitution. It is ordinary optimal substructure, not a FIR-specific
dominance theorem. No bound on the number of distinct `s*` states follows.
Range inclusion or equal peak-live counts alone does not supply this proof.

## Inspection and verification record

Freshly read the complete [bounded plan](fir-novelty-establishment-plan.md),
[Stage 1 progress](fir-paper/PROGRESS.md), [manuscript](fir-paper/manuscript.md)
and [post-join assessment](fir-post-join-research-assessment.md). Their target
results and broader literature history are inherited; no binary, compiler or
historical measurement was revalidated for this note.

Fresh primary inspection was limited to three closest methods:

- **Ménard–Sentieys:** author-uploaded full-text transcription, §§4–5.4 and
  Fig. 3, including all four stated search-space restrictions. No experiment
  reproduction or comprehensive citation chase.
- **SPIRAL FIR:** author-uploaded full-text transcription, §§2–5, especially
  equations 12–15 and the time-domain search discussion. Direct author-site PDF
  retrieval timed out; the full-text alternative was obtained.
- **Unison:** full 49-page arXiv PDF accessible; inspected §§3–8 model passages,
  especially C1–C3, copy extensions, scheduling and integrated live-range
  constraints. The HTML endpoint returned 404. Full text was available, but the
  entire 49-page evaluation/reference list was not audited.

No decisive exclusion is inferred from an abstract, missing download or an
uninspected implementation. The table describes the inspected formulations,
not the ultimate expressive limits of each tool or all later versions.

Arithmetic was checked manually and by a read-only Python standard-library
enumeration of all **64** input triples: extrema for every prefix of all six
contiguous groups matched the table; `[0,2)` and `[2,3)` fit signed four bits;
their widened sum equals the direct sum and gives identical final `Q` for every
triple; all wide prefixes fit six bits. The `−3→−1` floor boundary, extremal
windows and the 13/14 instruction totals were separately checked. The symbolic
minimum-suffix proof above is deductive; no optimizer was written or run.
