"""Off-screen image and video capture for `one` scenes (no window pops up).

House style (figstyle.py): pictures are rendered at the exact size of a HALF or
FULL 16:9 slide area; videos default to 1280x720 (720p, 16:9).

Usage from a figure script inside <doc>/scripts/:

    import sys; sys.path.insert(0, r"<path to doc-maker>/scripts")
    from one import ovw, ossop
    from one_capture import OffscreenCapture

    base = ovw.World(win_size=(1280, 720), visible=False)
    ossop.frame().attach_to(base.scene)
    cap = OffscreenCapture(base, layout="half")   # "half" | "full" | "video"
    cap.frame(robot, view="auto")                 # target fills the picture
    cap.snapshot("../imgs/robot_half.png")

    def step(i):                                  # called before each video frame
        base.camera.orbit(angle_rad=0.02)
    cap.record("../videos/orbit.mp4", n_frames=150, fps=30, step=step)
    # 1280x720 by default (re-framed for 16:9); also writes ../videos/orbit.png

Create the World with ``visible=False``; never call ``base.run()``.
"""
import os

import numpy as np
import pyglet.gl as gl

import one.viewer.render_target as ovrt

import figstyle as fs


class OffscreenCapture:
    def __init__(self, base, layout="half", width=None, height=None, samples=4):
        self.base = base
        self.layout = layout
        self.samples = samples
        self._last_frame = None
        w, h = (width, height) if width and height else fs.size_px(layout)
        self.resize(w, h)

    def resize(self, width, height):
        """Change the output size; re-applies the last frame() call."""
        self.width, self.height = int(width), int(height)
        self.base.switch_to()
        self.base.camera._rebuild_projmat(self.width, self.height)
        self.rt = ovrt.RenderTarget(self.width, self.height, samples=self.samples)
        if self._last_frame is not None:
            self.frame(*self._last_frame)
        return self

    def grab(self):
        """Render the scene once and return an (H, W, 3) uint8 RGB array."""
        self.base.switch_to()
        self.rt.bind()
        self.base.render.draw(self.base.scene)
        for overlay in getattr(self.base, "overlays", []):
            overlay()
        self.rt.unbind()  # resolves MSAA into rt.fbo
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, self.rt.fbo)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        buf = (gl.GLubyte * (self.width * self.height * 4))()
        gl.glReadPixels(0, 0, self.width, self.height,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, buf)
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, 0)
        img = np.frombuffer(buf, dtype=np.uint8).reshape(self.height, self.width, 4)
        return np.ascontiguousarray(img[::-1, :, :3])  # GL origin is bottom-left

    # ------------------------------------------------------------------ framing
    def frame(self, targets=None, view="auto", fill=0.92, up=(0, 0, 1)):
        """Point the camera at ``targets`` so they fill the image.

        targets: SceneObject / robot (MechBase) / list of them; None = whole scene.
        view:    "auto" (pick the iso view that shows the most), "iso", "front",
                 "back", "left", "right", "top", or a 3-vector pointing from the
                 target toward the camera.
        fill:    fraction of the image the targets' extent should occupy (0..1).
        """
        self._last_frame = (targets, view, fill, up)
        pts = _world_points(self.base.scene if targets is None else targets)
        if len(pts) == 0:
            raise ValueError("frame(): targets have no visible geometry")
        center = 0.5 * (pts.min(0) + pts.max(0))
        d = _pick_view(pts, view) if isinstance(view, str) else _unit(view)
        cam = self.base.camera
        aspect = self.width / self.height
        t_y = np.tan(np.radians(cam.fov) / 2) * fill
        t_x = t_y * aspect
        fwd = -d
        right = _unit(np.cross(fwd, up if abs(np.dot(_unit(up), fwd)) < .99 else (0, 1, 0)))
        upv = np.cross(right, fwd)
        rel = pts - center
        x, y, z = rel @ right, rel @ upv, rel @ fwd
        dist = np.max(np.maximum(np.abs(x) / t_x, np.abs(y) / t_y) - z)
        dist = max(dist, 1e-3)
        cam.near = max(dist * 1e-3, 1e-4)
        cam.far = max(dist * 100, 10.0)
        cam.set_to(pos=center + d * dist, look_at=center, up=upv)
        return self

    def snapshot(self, path, crop=False, pad=0.03):
        """Save a PNG at the layout size (exact HALF / FULL slide shape).
        ``crop=True`` instead trims the empty background border (free aspect)."""
        from PIL import Image
        _mkdir_for(path)
        img = self.grab()
        if crop:
            img = _autocrop(img, pad)
        Image.fromarray(img).save(path)
        return os.path.abspath(path)

    def record(self, path, n_frames, fps=30, step=None, poster="first",
               size=fs.VIDEO_SIZE):
        """Record ``n_frames`` frames to an .mp4, by default 1280x720 (16:9).

        ``step(i)`` is called before frame ``i`` to move robots / camera.
        A poster image (same name, .png) is saved next to the video; slides use
        it as the still shown in the exported PDF. ``poster`` is "first",
        "last", or a frame index. The capture is temporarily resized (and the
        last frame() re-applied for the new aspect), then restored.
        """
        import imageio.v2 as iio
        from PIL import Image
        _mkdir_for(path)
        old = (self.width, self.height)
        w, h = int(size[0]) // 2 * 2, int(size[1]) // 2 * 2   # libx264: even sizes
        if (w, h) != old:
            self.resize(w, h)
        poster_idx = {"first": 0, "last": n_frames - 1}.get(poster, poster)
        poster_path = os.path.splitext(path)[0] + ".png"
        try:
            with iio.get_writer(path, fps=fps, codec="libx264", quality=8,
                                pixelformat="yuv420p", macro_block_size=1) as writer:
                for i in range(n_frames):
                    if step is not None:
                        step(i)
                    frame = self.grab()
                    writer.append_data(frame)
                    if i == poster_idx:
                        Image.fromarray(frame).save(poster_path)
        finally:
            if (w, h) != old:
                self.resize(*old)
        return os.path.abspath(path), os.path.abspath(poster_path)


_NAMED_VIEWS = {
    "iso": (1, -1, 0.8), "front": (1, 0, 0.25), "back": (-1, 0, 0.25),
    "left": (0, 1, 0.25), "right": (0, -1, 0.25), "top": (0, 0, 1),
}


def _unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def _pick_view(pts, view):
    if view != "auto":
        return _unit(_NAMED_VIEWS[view])
    # elevated diagonal views; pick the one with the largest projected
    # silhouette (2-D bounding-box area), i.e. the most informative view
    best, best_area = None, -1.0
    for az in np.radians(np.arange(0, 360, 45) + 22.5):
        d = _unit((np.cos(az), np.sin(az), 0.7))
        right = _unit(np.cross(-d, (0, 0, 1)))
        upv = np.cross(right, -d)
        rel = pts - pts.mean(0)
        area = np.ptp(rel @ right) * np.ptp(rel @ upv)
        if area > best_area + 1e-9:
            best, best_area = d, area
    return best


def _iter_nodes(targets):
    import one.scene.scene as osc
    if isinstance(targets, osc.Scene):
        yield from targets
        return
    if not isinstance(targets, (list, tuple, set)):
        targets = [targets]
    for t in targets:
        roots = getattr(t, "runtime_lnks", None) or [t]
        for r in roots:
            yield from osc._walk_subtree(r)


def _world_points(targets, max_pts=40000):
    chunks = []
    for node in _iter_nodes(targets):
        for model in getattr(node, "visuals", []):
            vs = np.asarray(model.geom.vs, dtype=float)
            if len(vs) == 0:
                continue
            tf = np.asarray(node.wd_tf @ model.tf, dtype=float)
            chunks.append(vs @ tf[:3, :3].T + tf[:3, 3])
    if not chunks:
        return np.zeros((0, 3))
    pts = np.concatenate(chunks)
    if len(pts) > max_pts:
        pts = pts[:: len(pts) // max_pts + 1]
    return pts


def _autocrop(img, pad=0.03, tol=8):
    bg = img[0, 0].astype(int)
    mask = np.any(np.abs(img.astype(int) - bg) > tol, axis=2)
    if not mask.any():
        return img
    rows, cols = np.where(mask.any(1))[0], np.where(mask.any(0))[0]
    h, w = img.shape[:2]
    p = int(pad * max(rows[-1] - rows[0], cols[-1] - cols[0]))
    r0, r1 = max(rows[0] - p, 0), min(rows[-1] + p + 1, h)
    c0, c1 = max(cols[0] - p, 0), min(cols[-1] + p + 1, w)
    return img[r0:r1, c0:c1]


def _mkdir_for(path):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
