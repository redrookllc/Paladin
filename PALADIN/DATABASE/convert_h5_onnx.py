import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "3"
os.environ["CUDA_VISIBLE_DEVICES"]  = ""

import sys
import gc
import json
import importlib

import tensorflow as tf
tf.get_logger().setLevel("ERROR")

for _gpu in tf.config.experimental.list_physical_devices("GPU"):
    tf.config.experimental.set_memory_growth(_gpu, True)

import tf2onnx
import onnx
from tensorflow.keras import layers
from tensorflow.keras.saving import register_keras_serializable


@register_keras_serializable(package="Paladin")
class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, dropout_rate=0.3, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim    = embed_dim
        self.num_heads    = num_heads
        self.ff_dim       = ff_dim
        self.dropout_rate = dropout_rate
        self.att          = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn          = tf.keras.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm1   = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2   = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1     = layers.Dropout(dropout_rate)
        self.dropout2     = layers.Dropout(dropout_rate)

    def call(self, inputs, training=False):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1        = self.layernorm1(inputs + attn_output)
        ffn_output  = self.ffn(out1)
        ffn_output  = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim":    self.embed_dim,
            "num_heads":    self.num_heads,
            "ff_dim":       self.ff_dim,
            "dropout_rate": self.dropout_rate,
        })
        return config

    @classmethod
    def from_config(cls, config):
        return cls(**config)


def load_general_info(py_path: str) -> dict:
    print("[ KNOWLEDGE ] Loading Paladin knowledge base...")
    if not os.path.exists(py_path):
        raise FileNotFoundError(f"Knowledge base not found: {py_path}")
    dir_path    = os.path.dirname(os.path.abspath(py_path))
    module_name = os.path.splitext(os.path.basename(py_path))[0]
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    module = importlib.import_module(module_name)
    data   = getattr(module, "SYSTEM_PROMPT_JSON", None)
    if data is None:
        raise AttributeError(f"SYSTEM_PROMPT_JSON not found in {py_path}")
    return data


def flatten_knowledge(obj, prefix="") -> list:
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            lines += flatten_knowledge(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            lines += flatten_knowledge(item, f"{prefix}[{i}]")
    else:
        lines.append(f"{prefix} : {obj}")
    return lines


def build_conversation_context(lines: list) -> list:
    turns = []
    for line in lines:
        if " : " in line:
            key, value = line.split(" : ", 1)
            turns.append({"role": "system", "domain": key.strip(), "knowledge": value.strip()})
    return turns


def display_summary(kb: dict, lines: list, turns: list):
    meta           = kb.get("meta_identity", {})
    designation    = meta.get("designation",    "Paladin")
    classification = meta.get("classification", "OMEGA")
    issued_by      = meta.get("issued_by",      "RED ROOK, LLC")
    print(f"[ KNOWLEDGE ] Designation    : {designation}")
    print(f"[ KNOWLEDGE ] Classification : {classification}")
    print(f"[ KNOWLEDGE ] Issued By      : {issued_by}")
    print(f"[ KNOWLEDGE ] Top Domains    : {len(kb.keys())}")
    print(f"[ KNOWLEDGE ] Context Lines  : {len(lines)}")
    print(f"[ KNOWLEDGE ] Conv Turns     : {len(turns)}")
    print(f"[ KNOWLEDGE ] Status         : INJECTED")


def save_context(turns: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(turns, f, indent=2)
    print(f"[ KNOWLEDGE ] Context saved  : {path}")


def load_keras_model(path: str, custom_objects: dict):
    with tf.keras.utils.custom_object_scope(custom_objects):
        return tf.keras.models.load_model(path, custom_objects=custom_objects)


def convert_to_onnx(model, output_path: str):
    spec = (tf.TensorSpec(shape=(None,) + model.input_shape[1:], dtype=tf.float32, name="input"),)
    tf2onnx.convert.from_keras(
        model,
        input_signature=spec,
        opset=13,
        output_path=output_path,
        optimizers=None,
    )


def validate_onnx(path: str):
    model = onnx.load(path)
    onnx.checker.check_model(model)
    return model


def main():
    BASE           = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH     = os.path.join(BASE, "paladin.h5")
    ONNX_PATH      = os.path.join(BASE, "paladin.onnx")
    KB_PATH        = os.path.join(BASE, "general_info.py")
    CONTEXT_PATH   = os.path.join(BASE, "paladin_contextv2.json")
    CUSTOM_OBJECTS = {"TransformerBlock": TransformerBlock}

    print("RED ROOK, LLC | Paladin — Model Export Pipeline v2")
    print("=" * 55)

    print("[ STAGE 0/5 ] Loading knowledge base...")
    kb    = load_general_info(KB_PATH)
    lines = flatten_knowledge(kb)
    turns = build_conversation_context(lines)
    display_summary(kb, lines, turns)
    save_context(turns, CONTEXT_PATH)
    print("[ STAGE 0/5 ] Complete.")
    print("-" * 55)

    print("[ STAGE 1/5 ] Loading Keras model...")
    model = load_keras_model(MODEL_PATH, CUSTOM_OBJECTS)
    print(f"[ STAGE 1/5 ] Loaded.  Input: {model.input_shape}  Output: {model.output_shape}")

    print("[ STAGE 2/5 ] Binding knowledge context...")
    model._paladin_context         = turns
    model._paladin_knowledge_lines = len(lines)
    print(f"[ STAGE 2/5 ] Bound {len(turns)} entries.")

    print("[ STAGE 3/5 ] Releasing memory before conversion...")
    gc.collect()
    tf.keras.backend.clear_session()
    model = load_keras_model(MODEL_PATH, CUSTOM_OBJECTS)
    gc.collect()
    print("[ STAGE 3/5 ] Memory released. Model reloaded clean.")

    print("[ STAGE 4/5 ] Converting to ONNX (optimizers disabled)...")
    convert_to_onnx(model, ONNX_PATH)
    del model
    gc.collect()
    print("[ STAGE 4/5 ] Conversion complete.")

    print("[ STAGE 5/5 ] Validating ONNX integrity...")
    validate_onnx(ONNX_PATH)
    print("[ STAGE 5/5 ] Validation passed.")

    size_mb = os.path.getsize(ONNX_PATH) / (1024 * 1024)
    print("=" * 55)
    print(f"[ COMPLETE  ] ONNX file      : {ONNX_PATH}")
    print(f"[ COMPLETE  ] Context file   : {CONTEXT_PATH}")
    print(f"[ COMPLETE  ] ONNX size      : {size_mb:.2f} MB")
    print(f"[ COMPLETE  ] Knowledge turns: {len(turns)}")
    print(f"[ COMPLETE  ] Paladin v2 pipeline finished.")
    print("=" * 55)


if __name__ == "__main__":
    main()