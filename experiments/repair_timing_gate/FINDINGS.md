# repair_timing setup: keep-winner vs Liberty estimator

Two independent recipes on the same vs-nop setup-repair path
(`RSZ_SIMPLE_VS_NOP=1` + `RSZ_GUIDED_PICK=1`). Do not combine them.
Replay a CTS snapshot with `experiments/repair_timing_gate/replay_setup.tcl`.

WNS is the objective. TNS is informational.

## Keep-winner (WNS)

Leave the vs-nop STA winner applied instead of restore+reapply.

```
RSZ_SIMPLE_VS_NOP=1
RSZ_GUIDED_PICK=1
RSZ_KEEP_WINNER=1
```

ibex pack002 (nangate45, CTS snapshot):

| | WNS | TNS | time |
|---|---|---|---|
| greedy | −0.38 | −569 | 131s |
| vs-nop champion | −0.34 | −410 | 507s |
| keep-winner | −0.34 | −412 | 244s |

Same WNS as the 507s champion, about 2× faster. Trial ECO flags
`inverse_undo`, `one_sta`, and `skip_restore_sta` did not beat keep on
WNS or stack a real speedup.

## Liberty estimator (speed)

Score size-up / pin-swap / buffer / clone vs nop with DelayEstimator
(`delay_levels=1`) and commit the winner once. Abort after WNS is flat
for 150 iters. No trial STA.

```
RSZ_SIMPLE_VS_NOP=1
RSZ_GUIDED_PICK=1
RSZ_FASTER_CHAMPION=1
```

Vs greedy on the same snapshots (25 finished runs: gcd, aes p065, jpeg,
ibex packs 000–019/022/037):

- Sum of runtimes: greedy 4096s, estimator 754s → **5.4×**
- Mean WNS loss vs greedy: **19 ps** (median 20 ps)
- That is **1.3% of the constraint period** on average, **1.1% of greedy T_eff**
  (`T_eff = T − WNS`)
- **0** wins, **7** ties, **18** losses vs greedy WNS
- Worst losses: jpeg −50 ps, aes −40 ps; ibex typically 0 to −50 ps
- gcd: WNS tie at −0.16 on a 0.25 ns clock (T_eff 0.41 ns); repair does
  not move WNS

Estimator almost never inserts buffers and stops on WNS-flat-150.
It is the fast knob, not a WNS replacement for keep-winner.
