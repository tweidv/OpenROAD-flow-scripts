"""Shared trajectory-level train/test split for PPA experiments."""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

DEFAULT_TRAIN_SIZE = 20
DEFAULT_RANDOM_STATE = 42


def split_trajectories(
    trajectory_ids,
    *,
    train_size: int = DEFAULT_TRAIN_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[list[str], list[str]]:
    """Hold out a fixed number of trajectories for training; rest are test."""
    ids = np.array(sorted(trajectory_ids))
    n = len(ids)
    if train_size >= n:
        raise ValueError(f"train_size={train_size} must be < n_trajectories={n}")
    if n - train_size < 2:
        raise ValueError(f"need at least 2 test trajectories; got {n - train_size}")

    train, test = train_test_split(
        ids,
        train_size=train_size,
        random_state=random_state,
    )
    return sorted(train.tolist()), sorted(test.tolist())


def split_train_validation(
    train_trajectory_ids,
    *,
    val_size: int = 5,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[list[str], list[str]]:
    """Hold out validation trajectories from the training pool (trajectory-level)."""
    ids = np.array(sorted(train_trajectory_ids))
    n = len(ids)
    if val_size >= n:
        raise ValueError(f"val_size={val_size} must be < n_train={n}")
    if n - val_size < 1:
        raise ValueError(f"need at least 1 inner-train trajectory; got {n - val_size}")

    inner_train, inner_val = train_test_split(
        ids,
        test_size=val_size,
        random_state=random_state,
    )
    return sorted(inner_train.tolist()), sorted(inner_val.tolist())
