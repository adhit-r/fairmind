"""W2: small transformer fine-tune. Pure-torch tiny transformer, no HuggingFace.

Workload
--------
Trains a hand-rolled decoder-style transformer (token plus positional
embeddings, ``n_layers`` blocks of multi-head self-attention and a 2-layer
MLP, tied to a vocabulary head) on seeded synthetic next-token-prediction
batches with AdamW. Implemented directly against ``torch`` primitives so the
harness never requires HuggingFace. Config-scaled: layers, width, heads,
sequence length, batch size, and optimizer steps.

Analytic FLOP model (manual_flop method)
----------------------------------------
Training FLOPs use the standard Kaplan et al. (2020) approximation

    FLOPs ~= 6 * params * tokens

where ``tokens = batch_size * seq_len * steps`` (forward plus backward is
about 6 FLOPs per parameter per token) and ``params`` is computed
analytically from the config so the estimate works even when torch is not
importable:

    params = vocab * d_model            (token embedding)
           + seq_len * d_model          (positional embedding)
           + n_layers * (4 * d_model^2 + 2 * d_model * mlp_ratio * d_model)
           + d_model * vocab            (output head)

Documented simplifications: attention-score FLOPs (the ``seq^2`` term),
biases, and LayerNorm parameters are omitted; linear layers in the model are
built with ``bias=False`` so the analytic count tracks the real parameter
count closely. The actual ``sum(p.numel())`` is recorded in ``work_metrics``
whenever the workload runs, so the approximation error is visible, not hidden.
"""

from __future__ import annotations

import time
from typing import Any

WORKLOAD_ID = "transformer_finetune"
CLI_ALIASES = ("w2", "w2_finetune")
FUNCTIONAL_UNIT = "1000_finetune_examples"

REAL_CONFIG: dict[str, Any] = {
    "vocab_size": 2_000,
    "d_model": 128,
    "n_layers": 2,
    "n_heads": 4,
    "mlp_ratio": 4,
    "seq_len": 128,
    "batch_size": 16,
    "steps": 400,
    "learning_rate": 3e-4,
    "dtype": "float32",
}

DRY_CONFIG: dict[str, Any] = {
    "vocab_size": 100,
    "d_model": 32,
    "n_layers": 1,
    "n_heads": 2,
    "mlp_ratio": 2,
    "seq_len": 16,
    "batch_size": 4,
    "steps": 3,
    "learning_rate": 3e-4,
    "dtype": "float32",
}


def availability() -> tuple[bool, str]:
    """Probe imports without raising. Returns (available, reason)."""

    try:
        import torch  # noqa: F401
    except ImportError as exc:
        return False, f"import failed: {exc}"
    return True, "torch importable"


def analytic_params(config: dict[str, Any]) -> float:
    """Parameter count from config alone. Pure stdlib; see module docstring."""

    vocab = float(config["vocab_size"])
    d = float(config["d_model"])
    layers = float(config["n_layers"])
    mlp_ratio = float(config["mlp_ratio"])
    seq_len = float(config["seq_len"])
    per_layer = 4.0 * d * d + 2.0 * d * (mlp_ratio * d)
    return vocab * d + seq_len * d + layers * per_layer + d * vocab


def flop_estimate(config: dict[str, Any]) -> float:
    """Analytic FLOPs ~= 6 * params * tokens. Pure stdlib."""

    tokens = (
        float(config["batch_size"]) * float(config["seq_len"]) * float(config["steps"])
    )
    return 6.0 * analytic_params(config) * tokens


def functional_units(config: dict[str, Any]) -> float:
    examples = float(config["batch_size"]) * float(config["steps"])
    return examples / 1000.0


def _build_model(config: dict[str, Any]):
    """Construct the tiny transformer. Only called when torch is importable."""

    import torch
    from torch import nn

    d = int(config["d_model"])
    heads = int(config["n_heads"])
    mlp_dim = int(config["mlp_ratio"]) * d
    vocab = int(config["vocab_size"])
    seq_len = int(config["seq_len"])

    class Block(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.norm_attn = nn.LayerNorm(d)
            self.qkv = nn.Linear(d, 3 * d, bias=False)
            self.attn_out = nn.Linear(d, d, bias=False)
            self.norm_mlp = nn.LayerNorm(d)
            self.mlp_up = nn.Linear(d, mlp_dim, bias=False)
            self.mlp_down = nn.Linear(mlp_dim, d, bias=False)

        def forward(self, hidden: "torch.Tensor") -> "torch.Tensor":
            batch, seq, _ = hidden.shape
            normed = self.norm_attn(hidden)
            qkv = self.qkv(normed).reshape(batch, seq, 3, heads, d // heads)
            query, key, value = qkv.unbind(dim=2)
            query = query.transpose(1, 2)
            key = key.transpose(1, 2)
            value = value.transpose(1, 2)
            scores = query @ key.transpose(-2, -1) / float(d // heads) ** 0.5
            attn = torch.softmax(scores, dim=-1) @ value
            attn = attn.transpose(1, 2).reshape(batch, seq, d)
            hidden = hidden + self.attn_out(attn)
            normed = self.norm_mlp(hidden)
            hidden = hidden + self.mlp_down(torch.tanh(self.mlp_up(normed)))
            return hidden

    class TinyTransformer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.token_embed = nn.Embedding(vocab, d)
            self.pos_embed = nn.Embedding(seq_len, d)
            self.blocks = nn.ModuleList(
                Block() for _ in range(int(config["n_layers"]))
            )
            self.head = nn.Linear(d, vocab, bias=False)

        def forward(self, tokens: "torch.Tensor") -> "torch.Tensor":
            positions = torch.arange(tokens.shape[1], device=tokens.device)
            hidden = self.token_embed(tokens) + self.pos_embed(positions)
            for block in self.blocks:
                hidden = block(hidden)
            return self.head(hidden)

    return TinyTransformer()


def run(config: dict[str, Any], seed: int) -> dict[str, Any]:
    """Execute the fine-tune for real. Deterministic given (config, seed)."""

    available, reason = availability()
    if not available:
        raise RuntimeError(f"workload {WORKLOAD_ID} unavailable: {reason}")

    import torch

    torch.manual_seed(seed)
    dtype = getattr(torch, str(config.get("dtype", "float32")))
    model = _build_model(config).to(dtype=dtype)
    params_actual = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=float(config["learning_rate"])
    )
    loss_fn = torch.nn.CrossEntropyLoss()

    vocab = int(config["vocab_size"])
    batch = int(config["batch_size"])
    seq_len = int(config["seq_len"])
    steps = int(config["steps"])
    generator = torch.Generator().manual_seed(seed)

    start = time.perf_counter()
    final_loss = float("nan")
    for _ in range(steps):
        tokens = torch.randint(0, vocab, (batch, seq_len + 1), generator=generator)
        inputs, targets = tokens[:, :-1], tokens[:, 1:]
        logits = model(inputs)
        loss = loss_fn(logits.reshape(-1, vocab).float(), targets.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        final_loss = float(loss.detach())
    duration = time.perf_counter() - start

    return {
        "duration_seconds": duration,
        "work_metrics": {
            "params_actual": int(params_actual),
            "params_analytic": int(analytic_params(config)),
            "tokens": batch * seq_len * steps,
            "steps": steps,
            "dtype": str(config.get("dtype", "float32")),
            "final_loss": round(final_loss, 6),
        },
    }
