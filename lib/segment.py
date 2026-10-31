"""Person mask for every frame ("text behind your head", orbit cards behind you).

Uses the open u2net_human_seg model (ONNX, ~170 MB), downloaded once into
~/.cache/claude-video-effects/. Masks are computed at a reduced fps and
cached as a compressed .npz next to the video, then interpolated per frame.
"""
import os, subprocess, sys, urllib.request
import numpy as np
import cv2

MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx"
CACHE = os.path.expanduser("~/.cache/claude-video-effects")


def _model_path():
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "u2net_human_seg.onnx")
    if not os.path.exists(p):
        print("downloading person-segmentation model (once, ~170 MB)…", file=sys.stderr)
        urllib.request.urlretrieve(MODEL_URL, p)
    return p


def _session():
    import onnxruntime as ort
    return ort.InferenceSession(_model_path(), providers=["CPUExecutionProvider"])


def _infer(sess, rgb):
    h, w = rgb.shape[:2]
    x = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    out = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    out = (out - out.min()) / (out.max() - out.min() + 1e-6)
    return cv2.resize(out, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)


def compute_masks(video, fps=10, out=None):
    """Return (times, masks[N,H/2,W/2] uint8). Cached in <video>.masks.npz."""
    out = out or video + ".masks.npz"
    if os.path.exists(out):
        d = np.load(out)
        return d["t"], d["m"]
    probe = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                     "-show_entries", "stream=width,height", "-of", "csv=p=0", video]).decode()
    w, h = map(int, probe.strip().split(","))
    sw, sh = 360, int(round(360 * h / w / 2) * 2)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={sw}:{sh}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    sess = _session()
    masks = []
    while True:
        buf = p.stdout.read(sw * sh * 3)
        if len(buf) < sw * sh * 3:
            break
        rgb = np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
        masks.append((_infer(sess, rgb) * 255).astype(np.uint8))
        if len(masks) % 20 == 0:
            print(f"  masks: {len(masks)} frames", file=sys.stderr)
    m = np.stack(masks)
    t = np.arange(len(m)) / fps
    np.savez_compressed(out, t=t, m=m)
    return t, m


class MaskTrack:
    """Smooth per-frame person mask at any time t, any output size."""

    def __init__(self, video, fps=10):
        self.t, self.m = compute_masks(video, fps)
        self.fps = fps

    def at(self, t, size):
        w, h = size
        f = np.clip(t * self.fps, 0, len(self.m) - 1)
        i = int(f); j = min(i + 1, len(self.m) - 1); a = f - i
        m = self.m[i].astype(np.float32) * (1 - a) + self.m[j].astype(np.float32) * a
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
        m = np.clip((m - 60) * 255.0 / 130.0, 0, 255)          # harden the edge a little
        m = cv2.GaussianBlur(m, (0, 0), 1.6)
        return (m / 255.0).astype(np.float32)


if __name__ == "__main__":
    compute_masks(sys.argv[1])
    print("ok")
