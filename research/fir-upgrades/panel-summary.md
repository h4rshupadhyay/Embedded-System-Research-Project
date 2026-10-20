# Frozen FIR Task 5 panel results

Protocol digest: `d2b85b2580ec551efcbc457159ff9237482aa2f146417ed236bbd0c0aeb8646c`

Inventory: 288 identities; 280 admitted; 8 unavailable; 0 failed.

Assessment: **incomplete**. The native fast-CMSIS block64 identities remain unavailable because pending unresolved pointer-object aliasing.

The fixed panel is purposive and synthetic. Normalized costs are per measured output; post-startup is not an isolated steady-state estimate.

## Primary extension check

At least one wide-required fixed-compiler cell meets the frozen reversal condition:

| Filter / compiler / block / stimulus / regime | Hcub nJ/output | D_old | D_new |
|---|---:|---:|---:|
| wide_lp2800 / gcc10 / 1 / adc / post_startup | 1154.854753302439024390243902 | 1537.146564302439024390243902 | 1099.806204892682926829268293 |
| wide_lp2800 / gcc10 / 1 / adc / startup | 1154.921525381322957198443580 | 1537.213336381322957198443580 | 1099.642403357976653696498054 |
| wide_lp2800 / gcc10 / 1 / full / post_startup | 1154.702636593170731707317073 | 1537.121015355121951219512195 | 1099.629883289756097560975610 |
| wide_lp2800 / gcc10 / 1 / full / startup | 1154.816039638132295719844358 | 1537.190265237354085603112840 | 1099.510589334630350194552529 |
| wide_lp2800 / gcc10 / 64 / adc / post_startup | 661.3052730682926829268292683 | 904.0089545229268292682926829 | 515.4679421551219512195121951 |
| wide_lp2800 / gcc10 / 64 / adc / startup | 662.8281981322957198443579767 | 905.9392379416342412451361868 | 517.1316313540856031128404669 |
| wide_lp2800 / gcc10 / 64 / full / post_startup | 661.1531563590243902439024390 | 903.9847144126829268292682927 | 515.3158254458536585365853659 |
| wide_lp2800 / gcc10 / 64 / full / startup | 662.7227123891050583657587549 | 905.9370500894941634241245136 | 517.0261456108949416342412451 |
| wide_lp2800 / gcc15 / 64 / adc / post_startup | 615.7376150653658536585365854 | 836.8285752117073170731707317 | 591.2867457795121951219512195 |
| wide_lp2800 / gcc15 / 64 / adc / startup | 617.1406074513618677042801556 | 838.8555848443579766536964981 | 593.3805298715953307392996109 |
| wide_lp2800 / gcc15 / 64 / full / post_startup | 615.6353575502439024390243902 | 836.8192436087804878048780488 | 591.2527161160975609756097561 |
| wide_lp2800 / gcc15 / 64 / full / startup | 617.0801454280155642023346304 | 838.8415049922178988326848249 | 593.3650915680933852140077821 |
| wide_lp4600 / gcc10 / 1 / adc / post_startup | 1113.703133302439024390243902 | 1533.490678041951219512195122 | 1083.565708564878048780487805 |
| wide_lp4600 / gcc10 / 1 / adc / startup | 1113.769905381322957198443580 | 1533.560261357976653696498054 | 1083.518019357976653696498054 |
| wide_lp4600 / gcc10 / 1 / full / post_startup | 1113.457250836097560975609756 | 1533.350477366829268292682927 | 1083.264496010731707317073171 |
| wide_lp4600 / gcc10 / 1 / full / startup | 1113.572640891050583657587549 | 1533.444268214007782101167315 | 1083.271214214007782101167315 |
| wide_lp4600 / gcc10 / 64 / adc / post_startup | 636.0644915151219512195121951 | 904.0089545229268292682926829 | 524.5433878302439024390243902 |
| wide_lp4600 / gcc10 / 64 / adc / startup | 637.5409841712062256809338521 | 905.9392379416342412451361868 | 526.2075773968871595330739300 |
| wide_lp4600 / gcc10 / 64 / full / post_startup | 635.8186090487804878048780488 | 903.9658734956097560975609756 | 524.2975053639024390243902439 |
| wide_lp4600 / gcc10 / 64 / full / startup | 637.3437196809338521400778210 | 905.8904101439688715953307393 | 526.0103129066147859922178988 |
| wide_lp4600 / gcc15 / 64 / adc / post_startup | 619.0794369843902439024390244 | 836.8285752117073170731707317 | 594.2680188780487804878048780 |
| wide_lp4600 / gcc15 / 64 / adc / startup | 620.4620914163424124513618677 | 838.8555848443579766536964981 | 596.3779243540856031128404669 |
| wide_lp4600 / gcc15 / 64 / full / post_startup | 618.9351543853658536585365854 | 836.7676039756097560975609756 | 594.2294180702439024390243902 |
| wide_lp4600 / gcc15 / 64 / full / startup | 620.3623783190661478599221790 | 838.7948650466926070038910506 | 596.3594826031128404669260700 |

## Complete-case outcome counts

The reversal condition holds in 24 of 32 complete wide-required fixed-compiler cells: GCC10 16/16, GCC15 8/16. This reports each compiler separately; it does not pool compiler minima into a fixed-compiler denominator.

D_old and D_new are known in 40/48 fixed cells and 20/24 compiler-selectable cells. The remaining native block64 cells are unknown because the fast-CMSIS candidate is unavailable.

Complete-cell all-form winners (ties retained in JSON): cert_direct_balanced 12, cert_direct_first 16, trans_const 16, trans_hcub_demand 4

## Exact source quantizer thresholds

Counts below use exact source sums for measured samples only; they are not inferred from target branches.

| Filter | Stimulus | Regime | Positive | Negative | Total | Range |
|---|---|---|---:|---:|---:|---|
| native_lp1800 | adc | post_startup | 0 | 0 | 0 | [64, 1089] |
| native_lp1800 | adc | startup | 0 | 0 | 0 | [0, 257] |
| native_lp1800 | full | post_startup | 0 | 0 | 0 | [64, 1089] |
| native_lp1800 | full | startup | 0 | 0 | 0 | [0, 257] |
| wide_lp2800 | adc | post_startup | 0 | 0 | 0 | [64, 1089] |
| wide_lp2800 | adc | startup | 0 | 0 | 0 | [0, 257] |
| wide_lp2800 | full | post_startup | 31 | 22 | 53 | [64, 1089] |
| wide_lp2800 | full | startup | 6 | 6 | 12 | [0, 257] |
| wide_lp4600 | adc | post_startup | 0 | 0 | 0 | [64, 1089] |
| wide_lp4600 | adc | startup | 0 | 0 | 0 | [0, 257] |
| wide_lp4600 | full | post_startup | 55 | 53 | 108 | [64, 1089] |
| wide_lp4600 | full | startup | 12 | 14 | 26 | [0, 257] |

Maximum admitted static RAM end: `0x20001210` (ceiling `0x200017f0`); maximum conservative live stack: 688 / 2048 bytes; maximum Flash end: `0x0800135e`.

Unique admitted firmware binaries by SHA256: 280 across 280 logical identities; 0 duplicate groups.

## Derived result files

`panel-summary.json` contains every fixed-compiler cell, tied minimizer, D_old/D_new result, direct correction, Hcub increment, compiler-selectable result, and paired width/amplitude/regime contrast. `panel-results.json` preserves the complete identity inventory and raw-evidence references. `verification/independent-audit.json` records the independent raw-evidence audit.
