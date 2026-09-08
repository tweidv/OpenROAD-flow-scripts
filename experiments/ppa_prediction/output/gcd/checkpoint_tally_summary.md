# Checkpoint tally (from existing search_eval steps)

Costs apply only to **running** a flow stage. Model predictions are free.
Initial floorplan features for all candidates are free (metadata peek, not re-run).

Stage run costs: {'floorplan': 2.0, 'placement': 4.0, 'cts': 2.0, 'routing': 3.0} (11 per full run from scratch)

## 100 train / 900 test

### Model-guided (complete search)

| Stage | Count | Subtotal |
|-------|------:|---------:|
| floorplan | 0 | 0.0 |
| placement | 900 | 3600.0 |
| cts | 900 | 1800.0 |
| routing | 900 | 2700.0 |
| **TOTAL** | **2700** | **8100.0** |

Cost to 95%: model **9.0** vs random mean **60.4** (p50 **44.0**, 1000 shuffled orders)

## 20 train / 980 test

### Model-guided (complete search)

| Stage | Count | Subtotal |
|-------|------:|---------:|
| floorplan | 0 | 0.0 |
| placement | 980 | 3920.0 |
| cts | 980 | 1960.0 |
| routing | 980 | 2940.0 |
| **TOTAL** | **2940** | **8820.0** |

Cost to 95%: model **9.0** vs random mean **56.8** (p50 **44.0**, 1000 shuffled orders)

