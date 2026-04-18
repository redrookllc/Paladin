import warnings
import logging
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
import lightgbm as lgb
import onnxruntime as ort
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("RedRook.v2")

BASE_DIR      = Path(__file__).resolve().parent
MODEL_PATH    = BASE_DIR / "MODELS" / "brain_model.pkl"
RR_MODEL_PATH = BASE_DIR / "MODELS" / "paladin_brain.pkl"
SCALER_PATH   = BASE_DIR / "MODELS" / "scaler.pkl"
ONNX_PATH     = BASE_DIR / "DATABASE" / "paladin.onnx"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class ChartAnnotation:
    """A single AI-drawn annotation on the chart."""
    kind:    str    = "hline"      # hline | zone | arrow | label | callout | marker
    price:   float  = 0.0          # primary y-level
    price2:  float  = 0.0          # secondary y-level (for zones)
    xi:      int    = -1           # bar index (-1 = last bar)
    label:   str    = ""
    color:   str    = "#ffffff"
    alpha:   float  = 0.7
    phase:   int    = 0            # which analysis phase draws this (0-4)
    tooltip: str    = ""


@dataclass
class ReasoningPhase:
    """One step of the AI's live analysis narration."""
    phase:    int   = 0
    title:    str   = ""
    verdict:  str   = ""          # BULLISH | BEARISH | NEUTRAL | CAUTION
    detail:   str   = ""          # full paragraph text typed out live


@dataclass
class TradeSignal:
    symbol:        str                     = ""
    direction:     str                     = "HOLD"
    confidence:    float                   = 0.0
    entry_price:   float                   = 0.0
    stop_loss:     float                   = 0.0
    take_profit:   float                   = 0.0
    risk_reward:   float                   = 0.0
    pattern:       str                     = "—"
    reasoning:     str                     = ""
    source:        str                     = "LightGBM"
    # --- new rich fields ---
    annotations:   List[ChartAnnotation]   = None   # chart drawings
    phases:        List[ReasoningPhase]    = None   # step-by-step analysis
    regime:        str                     = "RANGING"
    divergence:    str                     = "NONE"
    vol_state:     str                     = "NORMAL"
    trend_score:   float                   = 0.0    # -1.0 to +1.0
    confluence:    int                     = 0      # count of agreeing signals

    def __post_init__(self):
        if self.annotations is None:
            self.annotations = []
        if self.phases is None:
            self.phases = []


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    g = d.clip(lower=0).ewm(com=n - 1, adjust=False).mean()
    l = (-d).clip(lower=0).ewm(com=n - 1, adjust=False).mean()
    return (100 - 100 / (1 + g / l.replace(0, np.nan))).astype("float32")


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=n - 1, adjust=False).mean().astype("float32")


def _features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d = d.reset_index(drop=True)

    c, o, h, l, v = d["Close"], d["Open"], d["High"], d["Low"], d["Volume"]

    rng            = (h - l).replace(0, np.nan)
    d["body"]      = (c - o).abs().astype("float32")
    d["body_pct"]  = (d["body"] / rng).astype("float32")
    d["close_pos"] = ((c - l) / rng).astype("float32")
    d["wick_up"]   = (h - c.combine(o, max)).astype("float32")
    d["wick_dn"]   = (c.combine(o, min) - l).astype("float32")
    d["bull"]      = (c > o).astype("int8")

    for p in [1, 2, 3, 5, 10, 20]:
        d[f"ret_{p}"] = c.pct_change(p).astype("float32")

    for w in [5, 10, 20, 50, 100, 200]:
        d[f"sma{w}"] = c.rolling(w).mean().astype("float32")
        d[f"ema{w}"] = _ema(c, w).astype("float32")

    d["trend_5_20"]   = (d["sma5"]  > d["sma20"]).astype("int8")
    d["trend_20_50"]  = (d["sma20"] > d["sma50"]).astype("int8")
    d["trend_50_200"] = (d["sma50"] > d["sma200"]).astype("int8")
    d["bull_align"]   = (
        (d["sma5"] > d["sma20"]) & (d["sma20"] > d["sma50"]) & (d["sma50"] > d["sma200"])
    ).astype("int8")
    d["bear_align"]   = (
        (d["sma5"] < d["sma20"]) & (d["sma20"] < d["sma50"]) & (d["sma50"] < d["sma200"])
    ).astype("int8")

    d["gc"] = (
        (d["sma20"] > d["sma200"]) & (d["sma20"].shift() <= d["sma200"].shift())
    ).astype("int8")
    d["dc"] = (
        (d["sma20"] < d["sma200"]) & (d["sma20"].shift() >= d["sma200"].shift())
    ).astype("int8")

    d["rsi"]        = _rsi(c)
    d["rsi_os"]     = (d["rsi"] < 30).astype("int8")
    d["rsi_ob"]     = (d["rsi"] > 70).astype("int8")
    d["rsi_mid_up"] = ((d["rsi"] > 50) & (d["rsi"].shift() <= 50)).astype("int8")

    ema12          = _ema(c, 12)
    ema26          = _ema(c, 26)
    d["macd"]      = (ema12 - ema26).astype("float32")
    d["macd_sig"]  = _ema(d["macd"], 9).astype("float32")
    d["macd_hist"] = (d["macd"] - d["macd_sig"]).astype("float32")
    d["macd_xup"]  = (
        (d["macd"] > d["macd_sig"]) & (d["macd"].shift() <= d["macd_sig"].shift())
    ).astype("int8")
    d["macd_xdn"]  = (
        (d["macd"] < d["macd_sig"]) & (d["macd"].shift() >= d["macd_sig"].shift())
    ).astype("int8")

    bb_mid         = c.rolling(20).mean()
    bb_std         = c.rolling(20).std()
    d["bb_up"]     = (bb_mid + 2 * bb_std).astype("float32")
    d["bb_dn"]     = (bb_mid - 2 * bb_std).astype("float32")
    d["bb_pos"]    = ((c - d["bb_dn"]) / (d["bb_up"] - d["bb_dn"] + 1e-9)).astype("float32")
    d["bb_wid"]    = ((d["bb_up"] - d["bb_dn"]) / (bb_mid + 1e-9)).astype("float32")
    d["bb_sq"]     = (d["bb_wid"] < d["bb_wid"].rolling(20).mean()).astype("int8")

    atr_s          = _atr(d)
    d["atr"]       = atr_s
    d["atr_n"]     = (atr_s / c).astype("float32")
    d["atr_exp"]   = (atr_s > atr_s.rolling(10).mean() * 1.3).astype("int8")

    lo14           = l.rolling(14).min()
    hi14           = h.rolling(14).max()
    d["stk_k"]     = (100 * (c - lo14) / (hi14 - lo14 + 1e-9)).astype("float32")
    d["stk_d"]     = d["stk_k"].rolling(3).mean().astype("float32")
    d["stk_xup"]   = (
        (d["stk_k"] > d["stk_d"]) & (d["stk_k"].shift() <= d["stk_d"].shift())
    ).astype("int8")
    d["stk_os"]    = (d["stk_k"] < 20).astype("int8")
    d["stk_ob"]    = (d["stk_k"] > 80).astype("int8")

    d["bull_eng"]  = (
        (o > c.shift()) & (c > o.shift()) & (d["body"] > d["body"].shift() * 1.3)
    ).astype("int8")
    d["bear_eng"]  = (
        (o < c.shift()) & (c < o.shift()) & (d["body"] > d["body"].shift() * 1.3)
    ).astype("int8")
    d["hammer"]    = (
        (d["wick_dn"] > 2 * d["body"]) & (d["wick_up"] < d["body"]) & (d["body_pct"] < 0.4)
    ).astype("int8")
    d["shoot_st"]  = (
        (d["wick_up"] > 2 * d["body"]) & (d["wick_dn"] < d["body"]) & (d["body_pct"] < 0.4)
    ).astype("int8")
    d["doji"]      = (d["body_pct"] < 0.05).astype("int8")
    d["morn_st"]   = (
        (c.shift(2) > o.shift(2)) &
        (d["body"].shift(1) < d["body"].shift(2) * 0.3) &
        (c > o.shift(2))
    ).astype("int8")
    d["eve_st"]    = (
        (c.shift(2) < o.shift(2)) &
        (d["body"].shift(1) < d["body"].shift(2) * 0.3) &
        (c < o.shift(2))
    ).astype("int8")
    d["three_up"]  = (
        (c > c.shift()) & (c.shift() > c.shift(2)) & (c.shift(2) > c.shift(3))
    ).astype("int8")
    d["three_dn"]  = (
        (c < c.shift()) & (c.shift() < c.shift(2)) & (c.shift(2) < c.shift(3))
    ).astype("int8")

    d["vol_r"]     = (v / (v.rolling(20).mean() + 1e-9)).astype("float32")
    d["vol_bull"]  = ((d["vol_r"] > 1.5) & (c > o)).astype("int8")
    d["vol_bear"]  = ((d["vol_r"] > 1.5) & (c < o)).astype("int8")

    hi20           = h.rolling(20).max()
    lo20           = l.rolling(20).min()
    d["res_dist"]  = ((hi20 - c) / c).astype("float32")
    d["sup_dist"]  = ((c - lo20) / c).astype("float32")
    d["near_res"]  = (d["res_dist"] < 0.015).astype("int8")
    d["near_sup"]  = (d["sup_dist"] < 0.015).astype("int8")

    d["rsi_bull_div"] = ((d["rsi"] > d["rsi"].shift()) & (l < l.shift())).astype("int8")
    d["rsi_bear_div"] = ((d["rsi"] < d["rsi"].shift()) & (h > h.shift())).astype("int8")

    return d.dropna()


FEAT = [
    "body_pct", "close_pos", "wick_up", "wick_dn", "bull",
    "ret_1", "ret_2", "ret_3", "ret_5", "ret_10", "ret_20",
    "trend_5_20", "trend_20_50", "trend_50_200", "bull_align", "bear_align", "gc", "dc",
    "rsi", "rsi_os", "rsi_ob", "rsi_mid_up",
    "macd", "macd_hist", "macd_xup", "macd_xdn",
    "bb_pos", "bb_wid", "bb_sq",
    "atr_n", "atr_exp",
    "stk_k", "stk_d", "stk_xup", "stk_os", "stk_ob",
    "bull_eng", "bear_eng", "hammer", "shoot_st", "doji", "morn_st", "eve_st", "three_up", "three_dn",
    "vol_r", "vol_bull", "vol_bear",
    "res_dist", "sup_dist", "near_res", "near_sup",
    "rsi_bull_div", "rsi_bear_div",
]


def _labels(df: pd.DataFrame, fwd: int = 5, thr: float = 0.006) -> pd.Series:
    ret = df["Close"].shift(-fwd) / df["Close"] - 1
    y   = pd.Series(1, index=df.index, dtype="int8")
    y[ret >  thr] = 2
    y[ret < -thr] = 0
    return y


def _fetch(symbol: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data: {symbol}")
    df = df.reset_index()
    df = df.set_index("Date" if "Date" in df.columns else "Datetime")
    df.index = pd.to_datetime(df.index)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


class OnnxEngine:
    def __init__(self, onnx_path: Path):
        self.session      = None
        self.input_name   = None
        self.output_name  = None
        self.input_shape  = None
        self._load(onnx_path)

    def _load(self, path: Path):
        if not path.exists():
            log.warning(f"[ ONNX ] Model not found at {path} — ONNX inference disabled.")
            return
        try:
            opts = ort.SessionOptions()
            opts.log_severity_level = 3
            self.session     = ort.InferenceSession(str(path), sess_options=opts)
            self.input_name  = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape
            log.info(f"[ ONNX ] Paladin ONNX engine loaded.")
            log.info(f"[ ONNX ] Input  : {self.input_name} {self.input_shape}")
            log.info(f"[ ONNX ] Output : {self.output_name}")
        except Exception as e:
            log.error(f"[ ONNX ] Failed to load ONNX model: {e}")
            self.session = None

    def is_ready(self) -> bool:
        return self.session is not None

    def infer(self, x: np.ndarray) -> np.ndarray:
        if not self.is_ready():
            raise RuntimeError("[ ONNX ] Session not initialized.")
        x = x.astype("float32")
        result = self.session.run([self.output_name], {self.input_name: x})
        return np.array(result[0])

    def infer_proba(self, x: np.ndarray) -> np.ndarray:
        if not self.is_ready():
            raise RuntimeError("[ ONNX ] Session not initialized.")
        x = x.astype("float32")
        outputs = self.session.run(None, {self.input_name: x})
        if len(outputs) >= 2:
            return np.array(outputs[1])
        raw = np.array(outputs[0])
        if raw.ndim == 2 and raw.shape[1] == 3:
            exp = np.exp(raw - raw.max(axis=1, keepdims=True))
            return exp / exp.sum(axis=1, keepdims=True)
        return raw


class TradingBrainV2:
    def __init__(self):
        self.model       = None
        self.scaler      = None
        self.onnx_engine = OnnxEngine(ONNX_PATH)
        self._load_or_train()

    def _load_or_train(self):
        model_path = MODEL_PATH if MODEL_PATH.exists() else RR_MODEL_PATH
        if model_path.exists() and SCALER_PATH.exists():
            try:
                self.model  = joblib.load(model_path)
                self.scaler = joblib.load(SCALER_PATH)
                if not isinstance(self.scaler, RobustScaler):
                    log.warning("[ BRAIN ] Loaded scaler is not RobustScaler. Retraining.")
                    self._train()
                else:
                    log.info(f"[ BRAIN ] Model loaded from {model_path.name} with RobustScaler.")
            except Exception as e:
                log.warning(f"[ BRAIN ] Load failed: {e}. Retraining.")
                self._train()
        else:
            self._train()

    def _train(self, symbols: Optional[List[str]] = None):
        if symbols is None:
            symbols = [
                "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA",
                "AMZN", "META", "JPM", "BRK-B", "V",
            ]

        Xs, ys = [], []
        for sym in symbols:
            try:
                raw = _fetch(sym, "3y", "1d")
                d   = _features(raw)
                y   = _labels(d)
                if not set(FEAT).issubset(d.columns):
                    missing = [c for c in FEAT if c not in d.columns]
                    log.warning(f"[ TRAIN ] {sym} skipped: missing features {missing}")
                    continue
                Xs.append(d[FEAT].values.astype("float32"))
                ys.append(y.values)
                log.info(f"[ TRAIN ] {sym}: {len(d)} bars")
            except Exception as e:
                log.warning(f"[ TRAIN ] {sym} skipped: {e}")

        if not Xs:
            raise RuntimeError("[ TRAIN ] No training data collected.")

        X    = np.vstack(Xs).astype("float32")
        y    = np.hstack(ys).astype("int8")
        mask = ~np.isnan(X).any(axis=1)
        X, y = X[mask], y[mask]

        log.info(f"[ TRAIN ] Dataset: {X.shape[0]} rows x {X.shape[1]} features | classes {np.bincount(y)}")

        self.scaler = RobustScaler()
        X           = self.scaler.fit_transform(X)

        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=0.15, random_state=42, stratify=y
        )

        params = dict(
            objective="multiclass",
            num_class=3,
            n_estimators=600,
            learning_rate=0.03,
            max_depth=6,
            num_leaves=48,
            min_child_samples=30,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.2,
            n_jobs=-1,
            random_state=42,
            verbose=-1,
        )

        base       = lgb.LGBMClassifier(**params)
        self.model = CalibratedClassifierCV(base, method="isotonic", cv=3)
        self.model.fit(X_tr, y_tr)

        acc = self.model.score(X_te, y_te)
        log.info(f"[ TRAIN ] Accuracy: {acc:.2%}")

        joblib.dump(self.model,  MODEL_PATH,  compress=3)
        joblib.dump(self.scaler, SCALER_PATH, compress=3)
        log.info("[ TRAIN ] Model and RobustScaler saved.")

    def _resolve_inference(self, X: np.ndarray, X_seq_buf: np.ndarray = None) -> tuple[np.ndarray, str]:
        if self.onnx_engine.is_ready():
            try:
                input_shape = self.onnx_engine.input_shape
                if len(input_shape) == 3:
                    timesteps = int(input_shape[1]) if input_shape[1] is not None else 60
                    features  = int(input_shape[2]) if input_shape[2] is not None else X.shape[1]
                    if X_seq_buf is not None and X_seq_buf.shape[0] >= timesteps:
                        seq = X_seq_buf[-timesteps:, :features]
                        if seq.shape[1] < features:
                            pad = np.zeros((seq.shape[0], features - seq.shape[1]), dtype="float32")
                            seq = np.concatenate([seq, pad], axis=1)
                        X_seq = seq.reshape(1, timesteps, features).astype("float32")
                    else:
                        X_seq = np.zeros((1, timesteps, features), dtype="float32")
                        n_feats = min(X.shape[1], features)
                        X_seq[0, -1, :n_feats] = X[0, :n_feats]
                    proba = self.onnx_engine.infer_proba(X_seq)
                else:
                    proba = self.onnx_engine.infer_proba(X)

                proba = np.array(proba).flatten()
                if len(proba) == 3:
                    return proba, "Paladin ONNX"
                else:
                    log.warning(f"[ ONNX ] Unexpected output shape {proba.shape} — falling back to LightGBM.")
            except Exception as e:
                log.warning(f"[ ONNX ] Inference failed: {e} — falling back to LightGBM.")

        if self.model is None:
            raise RuntimeError("[ BRAIN ] No inference engine available.")

        proba = self.model.predict_proba(X)[0]
        return np.array(proba), "LightGBM"

    def generate_signal(self, symbol: str, interval: str = "1d") -> TradeSignal:
        period_map = {
            "1m":  "1d",
            "5m":  "5d",
            "15m": "5d",
            "1h":  "60d",
            "1d":  "1y",
            "1wk": "5y",
        }
        period = period_map.get(interval, "1y")

        try:
            raw = _fetch(symbol, period, interval)
            if len(raw) < 50:
                return TradeSignal(symbol=symbol, reasoning="Insufficient data.")

            d       = _features(raw)
            missing = [c for c in FEAT if c not in d.columns]
            if missing:
                return TradeSignal(symbol=symbol, reasoning=f"Missing features: {missing}")

            row = d[FEAT].iloc[-1].astype("float32").values.reshape(1, -1)

            if self.scaler is None:
                return TradeSignal(symbol=symbol, reasoning="Scaler not initialized.")

            expected_n = getattr(self.scaler, "n_features_in_", None)
            if expected_n is not None and row.shape[1] != expected_n:
                return TradeSignal(
                    symbol=symbol,
                    reasoning=f"Feature mismatch: expected {expected_n}, got {row.shape[1]}"
                )

            X_all           = self.scaler.transform(d[FEAT].values.astype("float32"))
            X               = X_all[[-1]]
            proba, source   = self._resolve_inference(X, X_all)
            pred            = int(np.argmax(proba))
            conf            = float(np.max(proba))

            entry = float(d["Close"].iloc[-1])
            atr   = float(d["atr"].iloc[-1])

            if atr <= 0 or np.isnan(atr):
                atr = entry * 0.005

            direction_map = {2: "BUY", 1: "HOLD", 0: "SELL"}
            direction     = direction_map[pred]

            if direction == "BUY":
                sl = entry - 1.5 * atr
                tp = entry + 2.5 * atr
            elif direction == "SELL":
                sl = entry + 1.5 * atr
                tp = entry - 2.5 * atr
            else:
                sl = entry - 1.0 * atr
                tp = entry + 1.0 * atr

            rr      = abs(tp - entry) / (abs(entry - sl) + 1e-9)
            pattern = self._pattern(d.iloc[-1])
            phases, reasoning, regime, divergence, vol_state, trend_score, confluence = \
                self._build_phases(d.iloc[-1], direction, entry, sl, tp, atr)
            annotations = self._build_annotations(d, entry, sl, tp, atr, direction)

            return TradeSignal(
                symbol=symbol,
                direction=direction,
                confidence=round(conf, 4),
                entry_price=round(entry, 4),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                risk_reward=round(rr, 2),
                pattern=pattern,
                reasoning=reasoning,
                source=source,
                annotations=annotations,
                phases=phases,
                regime=regime,
                divergence=divergence,
                vol_state=vol_state,
                trend_score=round(trend_score, 3),
                confluence=confluence,
            )

        except Exception as e:
            log.error(f"[ SIGNAL ] Error for {symbol}: {e}")
            return TradeSignal(symbol=symbol, reasoning=str(e))

    def _pattern(self, row) -> str:
        checks = [
            ("bull_eng",  "Bullish Engulfing"),
            ("bear_eng",  "Bearish Engulfing"),
            ("hammer",    "Hammer"),
            ("shoot_st",  "Shooting Star"),
            ("morn_st",   "Morning Star"),
            ("eve_st",    "Evening Star"),
            ("gc",        "Golden Cross"),
            ("dc",        "Death Cross"),
            ("three_up",  "3 White Soldiers"),
            ("three_dn",  "3 Black Crows"),
            ("doji",      "Doji"),
        ]
        found = [name for key, name in checks if row.get(key, 0)]
        return " + ".join(found) if found else "Price Action"

    def _build_phases(self, row, direction: str, entry: float, sl: float, tp: float, atr: float):
        """Build 5 structured analysis phases with verdicts, and derive metadata."""
        GREEN_C = "#22c55e"
        RED_C   = "#ef4444"
        YELLOW_C= "#eab308"
        TEAL_C  = "#14b8a6"

        trend_score = 0.0
        confluence  = 0

        # ── PHASE 0: Trend Structure ──────────────────────────────────────
        trend_lines = []
        if row.get("bull_align"):
            trend_lines.append("All four SMAs (5 > 20 > 50 > 200) are stacked bullishly. This is textbook uptrend structure — momentum is broad and confirmed across every timeframe layer.")
            trend_score += 1.0; confluence += 2
        elif row.get("bear_align"):
            trend_lines.append("All four SMAs (5 < 20 < 50 < 200) are stacked bearishly. Every moving average confirms the downtrend — sellers are in control at every horizon.")
            trend_score -= 1.0; confluence += 2
        else:
            b5_20 = row.get("trend_5_20", 0); b20_50 = row.get("trend_20_50", 0); b50_200 = row.get("trend_50_200", 0)
            bull_layers = b5_20 + b20_50 + b50_200
            trend_score += (bull_layers - 1.5) / 1.5
            if bull_layers >= 2:
                trend_lines.append(f"{bull_layers}/3 SMA layers are bullish — trend structure is leaning long but not fully confirmed. Watch for SMA alignment to complete.")
            elif bull_layers <= 1:
                trend_lines.append(f"Only {bull_layers}/3 SMA layers are bullish — structure is weak or bearish. Price is navigating a contested zone.")
            else:
                trend_lines.append("Mixed SMA alignment — no dominant trend direction. The market is in a transition or ranging phase.")
        if row.get("gc"):
            trend_lines.append("GOLDEN CROSS: SMA 20 just crossed above SMA 200. This is a major long-term bullish signal historically associated with sustained uptrends.")
            trend_score += 0.5; confluence += 1
        elif row.get("dc"):
            trend_lines.append("DEATH CROSS: SMA 20 just crossed below SMA 200. This major bearish signal historically precedes extended downtrends — caution warranted.")
            trend_score -= 0.5; confluence += 1

        trend_verdict = "BULLISH" if trend_score > 0.3 else ("BEARISH" if trend_score < -0.3 else "NEUTRAL")
        p0 = ReasoningPhase(phase=0, title="Trend Structure", verdict=trend_verdict,
                            detail=" ".join(trend_lines) if trend_lines else "Trend structure is indeterminate with no clear SMA alignment.")

        # ── PHASE 1: Momentum ─────────────────────────────────────────────
        mom_score = 0.0
        mom_lines = []
        rsi = row.get("rsi", 50)
        if rsi < 30:
            mom_lines.append(f"RSI at {rsi:.1f} — deeply oversold. Selling pressure is statistically extreme. Mean-reversion setups have historically high success rates at these levels.")
            mom_score -= 0.5; confluence += 1
        elif rsi < 40:
            mom_lines.append(f"RSI at {rsi:.1f} — oversold territory. Buyers are beginning to show interest. Watch for a close above 40 to confirm momentum shift.")
            mom_score -= 0.3
        elif rsi > 70:
            mom_lines.append(f"RSI at {rsi:.1f} — overbought. Buying pressure has been sustained but is statistically stretched. Pullback or consolidation is elevated probability.")
            mom_score += 0.5; confluence += 1
        elif rsi > 60:
            mom_lines.append(f"RSI at {rsi:.1f} — strong bullish momentum, not yet overbought. Trend continuation setups are favoured in this RSI zone.")
            mom_score += 0.4
        elif rsi > 50:
            mom_lines.append(f"RSI at {rsi:.1f} — mild bullish bias. Momentum favours buyers but lacks conviction. No extreme reading to trade against.")
            mom_score += 0.1
        else:
            mom_lines.append(f"RSI at {rsi:.1f} — neutral to slightly bearish. No momentum edge in either direction from this indicator alone.")
            mom_score -= 0.1

        if row.get("macd_xup"):
            mom_lines.append("MACD crossed above its signal line this bar — a fresh bullish momentum crossover. This is an early-stage signal; confirm with price action.")
            mom_score += 0.4; confluence += 1
        elif row.get("macd_xdn"):
            mom_lines.append("MACD crossed below its signal line this bar — bearish momentum crossover confirmed. Short-side pressure is picking up.")
            mom_score -= 0.4; confluence += 1
        elif row.get("macd_hist", 0) > 0:
            mom_lines.append(f"MACD histogram is positive ({row.get('macd_hist',0):.4f}) — bullish momentum is intact and building.")
            mom_score += 0.2
        else:
            mom_lines.append(f"MACD histogram is negative ({row.get('macd_hist',0):.4f}) — bears hold the momentum edge.")
            mom_score -= 0.2

        stk = row.get("stk_k", 50)
        if row.get("stk_xup") and stk < 40:
            mom_lines.append(f"Stochastic %K ({stk:.0f}) crossed above %D from oversold — a high-probability reversal signal historically.")
            mom_score += 0.3; confluence += 1
        elif row.get("stk_os"):
            mom_lines.append(f"Stochastic is oversold at {stk:.0f}. Position in the bottom quartile. Buyers tend to defend these levels.")
        elif row.get("stk_ob"):
            mom_lines.append(f"Stochastic is overbought at {stk:.0f}. Extended buying — distribution risk is present.")

        if row.get("rsi_bull_div"):
            mom_lines.append("RSI BULLISH DIVERGENCE detected: price made a lower low but RSI is rising. This hidden strength is a high-conviction reversal signal — the bears are losing power.")
            mom_score += 0.5; confluence += 2
        elif row.get("rsi_bear_div"):
            mom_lines.append("RSI BEARISH DIVERGENCE detected: price made a higher high but RSI is falling. Hidden weakness — bulls are losing steam even as price rises.")
            mom_score -= 0.5; confluence += 2

        mom_verdict = "BULLISH" if mom_score > 0.3 else ("BEARISH" if mom_score < -0.3 else "NEUTRAL")
        p1 = ReasoningPhase(phase=1, title="Momentum Analysis", verdict=mom_verdict,
                            detail=" ".join(mom_lines))

        # ── PHASE 2: Volatility & Structure ──────────────────────────────
        vol_lines = []
        atr_n = row.get("atr_n", 0)
        vol_state = "NORMAL"
        if row.get("atr_exp"):
            vol_lines.append(f"ATR is expanded at {atr_n*100:.2f}% of price — volatility is elevated. Widen stops by at least 20% above default to avoid noise-induced exits.")
            vol_state = "HIGH"
        else:
            vol_lines.append(f"ATR is normal at {atr_n*100:.2f}% of price — standard volatility regime. Default stop placement is appropriate.")

        bb = row.get("bb_pos", 0.5)
        if row.get("bb_sq"):
            vol_lines.append("BOLLINGER BAND SQUEEZE: bands have compressed below their 20-period average width. Volatility is coiling — a high-magnitude breakout is statistically imminent. Direction unknown until price commits.")
            vol_state = "SQUEEZE"
        elif bb < 0.05:
            vol_lines.append("Price is touching the lower Bollinger Band. Statistically, closes below -2σ are uncommon — a snap-back to the mean (middle band) is the base-case expectation.")
        elif bb > 0.95:
            vol_lines.append("Price is touching the upper Bollinger Band. While strong trends can walk the band, rejection here is the higher-probability outcome for mean-reversion traders.")
        elif bb < 0.2:
            vol_lines.append(f"Price is in the lower 20% of the Bollinger range (BB position: {bb:.2f}). This is oversold on a volatility-adjusted basis.")
        elif bb > 0.8:
            vol_lines.append(f"Price is in the upper 20% of the Bollinger range (BB position: {bb:.2f}). Overbought on volatility basis.")

        vol_r = row.get("vol_r", 1.0)
        if row.get("vol_bull"):
            vol_lines.append(f"Volume is {vol_r:.1f}× the 20-bar average on a bullish candle — institutional accumulation is the likely driver. High-volume breakouts have substantially higher follow-through rates.")
        elif row.get("vol_bear"):
            vol_lines.append(f"Volume is {vol_r:.1f}× the 20-bar average on a bearish candle — institutional distribution likely. High-volume breakdowns are harder to reverse.")
        elif vol_r < 0.5:
            vol_lines.append(f"Volume is only {vol_r:.1f}× average — low conviction. Any move on thin volume should be treated with scepticism until confirmed by volume.")

        vol_verdict = "CAUTION" if vol_state in ("HIGH","SQUEEZE") else ("BULLISH" if bb < 0.3 else ("BEARISH" if bb > 0.7 else "NEUTRAL"))
        p2 = ReasoningPhase(phase=2, title="Volatility & Bands", verdict=vol_verdict,
                            detail=" ".join(vol_lines))

        # ── PHASE 3: Key Levels & Pattern ────────────────────────────────
        lvl_lines = []
        if row.get("near_sup"):
            sup = row.get("sup_dist", 0)
            lvl_lines.append(f"Price is within {sup*100:.2f}% of its 20-day support floor. This is a key demand zone — buyers have historically defended this level. A bounce here is the higher-probability base case.")
            confluence += 1
        if row.get("near_res"):
            res = row.get("res_dist", 0)
            lvl_lines.append(f"Price is within {res*100:.2f}% of its 20-day resistance ceiling. Supply is concentrated overhead — sellers have previously absorbed rallies at this level. Breakout probability depends on volume and momentum.")
            confluence += 1

        pattern_name = self._pattern(row)
        pattern_detail = {
            "Bullish Engulfing":  "A large bullish body has completely engulfed the prior bearish body. This candle demonstrates that buyers overwhelmed sellers decisively in a single session — high-conviction reversal signal.",
            "Bearish Engulfing":  "The current bearish body has engulfed the prior bullish body entirely. Sellers have decisively taken control in a single session — reversal is confirmed on close.",
            "Hammer":             "A hammer formed: long lower wick (2× body), minimal upper shadow. Buyers rejected the lows emphatically. Strong reversal signal when appearing at support.",
            "Shooting Star":      "Shooting Star: long upper wick, small body near the low. Buyers attempted a rally and were completely rejected. Bearish reversal signal at resistance.",
            "Morning Star":       "Three-candle Morning Star pattern: bearish candle, indecision doji/spin, then strong bullish close above the midpoint. Classic bottom-reversal structure.",
            "Evening Star":       "Three-candle Evening Star: bullish candle, indecision at the top, then bearish engulf. Classic top-reversal structure — bulls exhausted.",
            "Golden Cross":       "The 20-period SMA has crossed above the 200-period SMA — the celebrated Golden Cross. Long-term trend has officially turned bullish.",
            "Death Cross":        "The 20-period SMA has crossed below the 200-period SMA — the Death Cross. Long-term trend has officially turned bearish.",
            "3 White Soldiers":   "Three consecutive higher closes with expanding bodies. Systematic accumulation by buyers over multiple sessions — powerful continuation signal.",
            "3 Black Crows":      "Three consecutive lower closes with expanding bearish bodies. Systematic distribution — sellers are in full control across multiple sessions.",
            "Doji":               "A Doji formed: open and close nearly identical, indicating perfect balance of buyers and sellers. A moment of market indecision — the next directional bar is the deciding vote.",
        }.get(pattern_name, "")

        if pattern_detail:
            lvl_lines.append(f"Pattern detected — {pattern_name}: {pattern_detail}")
        else:
            lvl_lines.append("No high-conviction candle pattern detected. The AI signal is based primarily on indicator confluence rather than a specific price action formation.")

        # Risk/reward narrative
        rr = abs(tp - entry) / (abs(entry - sl) + 1e-9)
        dist_sl = abs(entry - sl)
        dist_tp = abs(entry - tp)
        lvl_lines.append(f"Entry ${entry:,.2f} → Stop ${sl:,.2f} (${dist_sl:,.2f} risk, {dist_sl/entry*100:.2f}%) → Target ${tp:,.2f} (${dist_tp:,.2f} reward). R:R = 1:{rr:.2f}. {'Favourable — reward exceeds risk by 2×+.' if rr >= 2 else ('Acceptable — minimum 1.5× reward-to-risk.' if rr >= 1.5 else 'Below ideal — consider tightening stop or adjusting target.')}")

        lvl_verdict = "BULLISH" if direction == "BUY" else ("BEARISH" if direction == "SELL" else "NEUTRAL")
        p3 = ReasoningPhase(phase=3, title="Key Levels & Pattern", verdict=lvl_verdict,
                            detail=" ".join(lvl_lines))

        # ── PHASE 4: Final Verdict ────────────────────────────────────────
        conf_pct = 0  # will be filled by caller
        if direction == "BUY":
            verdict_txt = (
                f"PALADIN recommends LONG. "
                f"The confluence of {confluence} agreeing signals across trend, momentum, and structure aligns with a bullish bias. "
                f"{'Trend structure is fully aligned and momentum confirms.' if trend_verdict == 'BULLISH' and mom_verdict == 'BULLISH' else 'Not all indicators agree — this is a moderate-conviction setup.'} "
                f"Regime: {('BULL TREND — ride the structure.' if trend_score > 0.5 else 'EMERGING BULL — early positioning.')} "
                f"Execute at ${entry:,.2f}, defend ${sl:,.2f}, target ${tp:,.2f}."
            )
        elif direction == "SELL":
            verdict_txt = (
                f"PALADIN recommends SHORT. "
                f"The confluence of {confluence} agreeing signals points decisively bearish. "
                f"{'Trend structure is fully aligned bearish and momentum confirms distribution.' if trend_verdict == 'BEARISH' and mom_verdict == 'BEARISH' else 'Some indicators diverge — manage risk accordingly.'} "
                f"Regime: {('BEAR TREND — trade with the pressure.' if trend_score < -0.5 else 'EMERGING BEAR — early positioning.')} "
                f"Short at ${entry:,.2f}, cover above ${sl:,.2f}, target ${tp:,.2f}."
            )
        else:
            verdict_txt = (
                f"PALADIN advises HOLD / WAIT. "
                f"The signal confluence ({confluence} signals) is insufficient for a high-conviction directional trade. "
                f"Trend: {trend_verdict} | Momentum: {mom_verdict} | Volatility: {vol_state}. "
                f"Wait for a cleaner setup: SMA alignment, a pattern break, or RSI confirmation before committing capital."
            )

        regime = ("BULL TREND" if trend_score > 0.5 else
                  ("BEAR TREND" if trend_score < -0.5 else
                   ("COMPRESSION" if vol_state == "SQUEEZE" else "RANGING")))
        divergence = ("BULL DIV" if row.get("rsi_bull_div") else
                      ("BEAR DIV" if row.get("rsi_bear_div") else "NONE"))

        p4 = ReasoningPhase(phase=4, title="AI Verdict", verdict=direction,
                            detail=verdict_txt)

        # Flatten to legacy reasoning string
        reasoning = "\n\n".join([
            f"▶ {ph.title}  [{ph.verdict}]\n{ph.detail}"
            for ph in [p0, p1, p2, p3, p4]
        ])

        return [p0, p1, p2, p3, p4], reasoning, regime, divergence, vol_state, trend_score, confluence

    def _build_annotations(self, d: pd.DataFrame, entry: float, sl: float, tp: float,
                           atr: float, direction: str) -> List[ChartAnnotation]:
        """Generate the list of chart drawings the AI will place."""
        GREEN_C  = "#22c55e"
        RED_C    = "#ef4444"
        YELLOW_C = "#eab308"
        TEAL_C   = "#14b8a6"
        BLUE_C   = "#3b82f6"
        PURPLE_C = "#8b5cf6"
        anns = []
        n    = len(d)
        last = n - 1
        row  = d.iloc[-1]

        # Phase 0 — Trend lines (SMA levels as horizontal reference markers)
        close = d["close"].values if "close" in d.columns else d["Close"].values

        # 20-day support/resistance zone
        hi20 = d["high"].rolling(20).max().iloc[-1] if "high" in d.columns else 0
        lo20 = d["low"].rolling(20).min().iloc[-1]  if "low"  in d.columns else 0
        if lo20 > 0:
            anns.append(ChartAnnotation(kind="zone", price=lo20, price2=lo20 + atr * 0.4,
                                        label="Support Zone", color=GREEN_C, alpha=0.08, phase=0,
                                        tooltip=f"20-day support floor: ${lo20:,.2f}"))
        if hi20 > 0:
            anns.append(ChartAnnotation(kind="zone", price=hi20 - atr * 0.4, price2=hi20,
                                        label="Resistance Zone", color=RED_C, alpha=0.08, phase=0,
                                        tooltip=f"20-day resistance ceiling: ${hi20:,.2f}"))

        # Phase 1 — Entry / SL / TP lines
        anns.append(ChartAnnotation(kind="hline", price=entry, label=f"Entry  ${entry:,.2f}",
                                    color=TEAL_C, alpha=0.85, phase=1,
                                    tooltip="AI recommended entry price"))
        anns.append(ChartAnnotation(kind="hline", price=sl, label=f"Stop  ${sl:,.2f}",
                                    color=RED_C, alpha=0.85, phase=1,
                                    tooltip=f"Stop loss — risk ${abs(entry-sl):,.2f}/share"))
        anns.append(ChartAnnotation(kind="hline", price=tp, label=f"Target  ${tp:,.2f}",
                                    color=GREEN_C, alpha=0.85, phase=1,
                                    tooltip=f"Take profit — reward ${abs(tp-entry):,.2f}/share"))

        # SL–TP zone fill
        zone_lo = min(sl, tp)
        zone_hi = max(sl, tp)
        zone_col = GREEN_C if direction == "BUY" else RED_C
        anns.append(ChartAnnotation(kind="zone", price=zone_lo, price2=zone_hi,
                                    label="", color=zone_col, alpha=0.05, phase=1,
                                    tooltip="Risk-reward corridor"))

        # Phase 2 — Bollinger Band squeeze or stretch callout
        bb_pos = row.get("bb_pos", 0.5)
        if row.get("bb_sq", 0):
            anns.append(ChartAnnotation(kind="callout", price=close[-1], xi=last,
                                        label="⚡ BB SQUEEZE", color=YELLOW_C, alpha=0.9, phase=2,
                                        tooltip="Bollinger Band squeeze — breakout imminent"))
        elif bb_pos < 0.05:
            anns.append(ChartAnnotation(kind="callout", price=close[-1], xi=last,
                                        label="↗ OVERSOLD (BB)", color=GREEN_C, alpha=0.9, phase=2,
                                        tooltip="Price at lower Bollinger Band — snap-back probable"))
        elif bb_pos > 0.95:
            anns.append(ChartAnnotation(kind="callout", price=close[-1], xi=last,
                                        label="↘ OVERBOUGHT (BB)", color=RED_C, alpha=0.9, phase=2,
                                        tooltip="Price at upper Bollinger Band — rejection risk high"))

        # Phase 2 — Volume spike marker
        if row.get("vol_bull", 0) or row.get("vol_bear", 0):
            col = GREEN_C if row.get("vol_bull", 0) else RED_C
            lbl = "📈 INST. BUY" if row.get("vol_bull", 0) else "📉 INST. SELL"
            anns.append(ChartAnnotation(kind="marker", price=close[-1], xi=last,
                                        label=lbl, color=col, alpha=0.9, phase=2,
                                        tooltip="Institutional-volume candle detected"))

        # Phase 3 — Pattern arrow
        pattern = self._pattern(row)
        if pattern not in ("Price Action", "—"):
            bull_patterns = {"Bullish Engulfing","Hammer","Morning Star","Golden Cross","3 White Soldiers"}
            p_col = GREEN_C if any(p in pattern for p in bull_patterns) else RED_C
            anns.append(ChartAnnotation(kind="arrow", price=close[-1], xi=last,
                                        label=f"◆ {pattern}", color=p_col, alpha=0.95, phase=3,
                                        tooltip=f"Pattern: {pattern}"))

        # Phase 3 — Divergence marker
        if row.get("rsi_bull_div", 0):
            anns.append(ChartAnnotation(kind="callout", price=close[-1], xi=last,
                                        label="↑ BULL DIV", color=GREEN_C, alpha=0.9, phase=3,
                                        tooltip="RSI bullish divergence — hidden strength"))
        elif row.get("rsi_bear_div", 0):
            anns.append(ChartAnnotation(kind="callout", price=close[-1], xi=last,
                                        label="↓ BEAR DIV", color=RED_C, alpha=0.9, phase=3,
                                        tooltip="RSI bearish divergence — hidden weakness"))

        # Phase 4 — Final signal arrow at entry
        sig_col = GREEN_C if direction == "BUY" else (RED_C if direction == "SELL" else YELLOW_C)
        sig_lbl = f"▲ BUY" if direction == "BUY" else (f"▼ SELL" if direction == "SELL" else "◈ HOLD")
        anns.append(ChartAnnotation(kind="signal", price=entry, xi=last,
                                    label=sig_lbl, color=sig_col, alpha=1.0, phase=4,
                                    tooltip=f"AI Signal: {direction} at ${entry:,.2f}"))

        return anns

    def retrain(self, symbols: Optional[List[str]] = None):
        self._train(symbols)


_instance = None


def get_brain_v2() -> TradingBrainV2:
    global _instance
    if _instance is None:
        _instance = TradingBrainV2()
    return _instance