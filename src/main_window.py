from pathlib import Path
import json

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QKeyEvent, QCloseEvent, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QCheckBox,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
)

from .graphics_view import GraphicsView


class MainWindow(QMainWindow):
    brush_feedback = pyqtSignal(int)  # allows QSlider react on mouse wheel
    sam_signal = pyqtSignal(bool)  # used to propagate sam mode to all widgets

    def __init__(self, workdir: str):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Nepes Crack AutoLabel")
        self.resize(1000, 1000)

        self._workdir = Path(workdir)
        self._class_dir = self._workdir / "classes.json"
        self._image_dir = self._workdir / "images"
        self._label_dir = self._workdir / "labels"
        self._sam_dir = self._workdir / "sam"
        self._label_dir.mkdir(exist_ok=True)
        self._image_stems = [path.stem for path in sorted(self._image_dir.iterdir())]
        with open(self._class_dir, "r") as f:
            self._classes = json.loads("".join(f.readlines()))["classes"]
        ids = [c["id"] for c in self._classes]
        colors = [c["color"] for c in self._classes]
        self._id2color = {k: v for k, v in zip(ids, colors)}

        self.brush_feedback.connect(self.on_brush_size_change)
        self._graphics_view = GraphicsView(self.brush_feedback)
        self.sam_signal.connect(self._graphics_view.handle_sam_signal)

        # Dataset group
        ds_group = QGroupBox(self.tr("Dataset"))

        self.ds_label = QLabel()
        self.ds_label.setText("Sample: 000000.png")

        ds_vlay = QVBoxLayout(ds_group)
        ds_vlay.addWidget(self.ds_label)

        # Layers group
        ls_group = QGroupBox(self.tr("Layers"))

        self.ls_label_value = QLabel()
        self.ls_label_value.setText("Label opacity: 50%")

        self.ls_label_slider = QSlider()
        self.ls_label_slider.setOrientation(Qt.Orientation.Horizontal)
        self.ls_label_slider.setMinimum(0)
        self.ls_label_slider.setMaximum(100)
        self.ls_label_slider.setSliderPosition(50)
        self.ls_label_slider.valueChanged.connect(self.on_ls_label_slider_change)

        self.ls_sam_value = QLabel()
        self.ls_sam_value.setText("SAM opacity: 0%")

        self.ls_sam_slider = QSlider()
        self.ls_sam_slider.setOrientation(Qt.Orientation.Horizontal)
        self.ls_sam_slider.setMinimum(0)
        self.ls_sam_slider.setMaximum(100)
        self.ls_sam_slider.setSliderPosition(0)
        self.ls_sam_slider.valueChanged.connect(self.on_ls_sam_slider_change)

        ls_vlay = QVBoxLayout(ls_group)
        ls_vlay.addWidget(self.ls_label_value)
        ls_vlay.addWidget(self.ls_label_slider)
        ls_vlay.addWidget(self.ls_sam_value)
        ls_vlay.addWidget(self.ls_sam_slider)

        # # SAM group <- 기존 코드 부분
        # sam_group = QGroupBox(self.tr("SAM"))

        # self.sam_checkbox = QCheckBox("SAM assistance")
        # self.sam_checkbox.stateChanged.connect(self.on_sam_change)

        # sam_vlay = QVBoxLayout(sam_group)
        # sam_vlay.addWidget(self.sam_checkbox)

        # YOLO group < - 수정 부분(SAM group -> YOLO group)
        yolo_group = QGroupBox(self.tr("YOLOv8 Auto Label"))

        self.yolo_btn = QCheckBox("Run YOLOv8 on current image")
        self.yolo_btn.clicked.connect(self.on_yolo_button_click)

        yolo_vlay = QVBoxLayout(yolo_group)
        yolo_vlay.addWidget(self.yolo_btn)


        # Brush size group
        bs_group = QGroupBox(self.tr("Brush"))

        self.bs_value = QLabel()
        self.bs_value.setText("Size: 50 px")

        self.bs_slider = QSlider()
        self.bs_slider.setOrientation(Qt.Orientation.Horizontal)
        self.bs_slider.setMinimum(1)
        self.bs_slider.setMaximum(150)
        self.bs_slider.setSliderPosition(50)
        self.bs_slider.valueChanged.connect(self.on_bs_slider_change)

        bs_vlay = QVBoxLayout(bs_group)
        bs_vlay.addWidget(self.bs_value)
        bs_vlay.addWidget(self.bs_slider)

        # Classs selection group
        cs_group = QGroupBox(self.tr("Classes"))

        self.cs_list = QListWidget()
        for i, c in enumerate(self._classes):
            color = QColor(c["color"])
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            text = f"[{i+1}] {c['name']}"
            item = QListWidgetItem(QIcon(pixmap), text)
            self.cs_list.addItem(item)
        self.cs_list.itemClicked.connect(self.on_item_clicked)

        cs_vlay = QVBoxLayout(cs_group)
        cs_vlay.addWidget(self.cs_list)

        vlay = QVBoxLayout()
        vlay.addWidget(ds_group)
        #vlay.addWidget(sam_group)
        vlay.addWidget(yolo_group)
        vlay.addWidget(ls_group)
        vlay.addWidget(bs_group)
        vlay.addWidget(cs_group)
        vlay.addStretch()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        lay = QHBoxLayout(central_widget)
        lay.addWidget(self._graphics_view, stretch=1)
        lay.addLayout(vlay, stretch=0)

        self._curr_id = 0
        self._graphics_view.set_brush_color(QColor(colors[0]))
        self.cs_list.setCurrentRow(0)

    @pyqtSlot(int)
    def on_sam_change(self, state: int):
        if state == Qt.CheckState.Checked:
            self.sam_signal.emit(True)
        elif state == Qt.CheckState.Unchecked:
            self.sam_signal.emit(False)
        else:
            print("unsupported check state")

    @pyqtSlot(int)
    def on_ls_label_slider_change(self, value: int):
        self.ls_label_value.setText(f"Label opacity: {value}%")
        self._graphics_view.set_label_opacity(value)

    @pyqtSlot(int)
    def on_ls_sam_slider_change(self, value: int):
        self.ls_sam_value.setText(f"SAM opacity: {value}%")
        self._graphics_view.set_sam_opacity(value)

    @pyqtSlot(int)
    def on_bs_slider_change(self, value: int):
        self.bs_value.setText(f"Size: {value} px")
        self._graphics_view.set_brush_size(value)

    @pyqtSlot(int)
    def on_brush_size_change(self, value: int):
        # updates slider and value label on brush size change via mouse wheel
        self.bs_value.setText(f"Size: {value} px")
        self.bs_slider.setSliderPosition(value)

    def on_item_clicked(self, item: QListWidgetItem):
        idx = self.sender().currentRow()
        color = self._id2color[idx + 1]
        self._graphics_view.set_brush_color(QColor(color))

    def save_current_label(self):
        curr_label_path = self._label_dir / f"{self._image_stems[self._curr_id]}.png"
        self._graphics_view.save_label_to(curr_label_path)

    def _load_sample_by_id(self, id: int):
        self._curr_id = id
        name = f"{self._image_stems[self._curr_id]}.png"
        image_path = self._image_dir / name
        label_path = self._label_dir / name
        sam_path = self._sam_dir / name
        self._graphics_view.load_sample(image_path, label_path, sam_path)
        self.ds_label.setText(f"Sample: {name}")

    def load_latest_sample(self):
        labels = list(self._label_dir.iterdir())
        images = list(self._image_dir.iterdir())
        if len(labels) < len(images):
            self._load_sample_by_id(len(labels))
        else:
            self._load_sample_by_id(0)

    def _switch_sample_by(self, step: int):
        if step == 0:
            return
        self.save_current_label()
        max_id = len(self._image_stems) - 1
        corner_case_id = 0 if step < 0 else max_id
        new_id = self._curr_id + step
        new_id = new_id if new_id in range(max_id + 1) else corner_case_id
        self._load_sample_by_id(new_id)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if a0.key() == Qt.Key.Key_Space:
            self._graphics_view.reset_zoom()
        elif a0.key() == Qt.Key.Key_S:
            self.sam_checkbox.toggle()
        elif a0.key() == Qt.Key.Key_C:
            self._graphics_view.clear_label()
        elif a0.key() == Qt.Key.Key_E:
            self.cs_list.clearSelection()
            self._graphics_view.set_eraser(True)
        elif a0.key() in range(49, 58):
            num_key = int(a0.key()) - 48
            color = self._id2color.get(num_key)
            if color:
                self._graphics_view.set_brush_color(QColor(color))
                self.cs_list.setCurrentRow(num_key - 1)
        elif a0.key() == Qt.Key.Key_Comma:
            self._switch_sample_by(-1)
        elif a0.key() == Qt.Key.Key_Period:
            self._switch_sample_by(1)

        return super().keyPressEvent(a0)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.save_current_label()
        return super().closeEvent(a0)
    
    @pyqtSlot()
    def on_yolo_button_click(self):
        """
        2830×2830 이미지를 1024 패치(+256 오버랩)로 추론,
        마스크 OR 병합 후 RGBA로 변환해 LabelLayer.add_mask() 호출
        """
        import numpy as np, cv2
        from scipy.ndimage import binary_closing          # pip install scipy
        from ultralytics import YOLO

        TILE, OVERLAP, THRESH = 1024, 256, 0.5
        RETINA = False            # 모델.predict(retina_masks=True) 쓸 땐 True

        # 0) 원본 이미지 로드
        stem = self._image_stems[self._curr_id]
        img_path = self._image_dir / f"{stem}.png"
        orig = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if orig is None:
            print(f"[YOLOv8] failed to read {img_path}")
            return
        H, W, _ = orig.shape

        # 1) 모델 1회 로딩
        if not hasattr(self, "_yolo_model"):
            mdl = self._workdir / "0715_seg.pt"
            self._yolo_model = YOLO(str(mdl))
            print(f"[YOLOv8] model loaded → {mdl}")
        model = self._yolo_model

        # 2) 전역 마스크
        global_mask = np.zeros((H, W), dtype=np.uint8)

        # 3) 패치 슬라이딩 추론
        y_steps = range(0, H, TILE - OVERLAP)
        x_steps = range(0, W, TILE - OVERLAP)
        for y0 in y_steps:
            for x0 in x_steps:
                y1, x1 = min(y0 + TILE, H), min(x0 + TILE, W)
                tile = orig[y0:y1, x0:x1]
                pad_b, pad_r = TILE - tile.shape[0], TILE - tile.shape[1]
                if pad_b or pad_r:
                    tile = cv2.copyMakeBorder(tile, 0, pad_b, 0, pad_r,
                                            cv2.BORDER_CONSTANT, value=(0, 0, 0))

                res = model(tile, verbose=False, retina_masks=RETINA)[0]
                if res.masks is None:
                    continue
                for m in res.masks.data.cpu().numpy():
                    if RETINA:  # retina=True ⇒ 1/4 해상도
                        m = cv2.resize(m, (TILE, TILE), interpolation=cv2.INTER_NEAREST)
                    m_bin = (m > THRESH).astype(np.uint8)
                    mh, mw = y1 - y0, x1 - x0
                    global_mask[y0:y1, x0:x1] |= m_bin[:mh, :mw]

        if not global_mask.any():
            print("[YOLOv8] no cracks detected.")
            return

        # 4) seam 미세 틈 메우기 (3×3 closing)
        global_mask = binary_closing(global_mask, structure=np.ones((3,3))).astype(np.uint8)

        # 5) RGBA 변환 (현재 선택 클래스 색)
        row = self.cs_list.currentRow()
        if row < 0:
            print("[YOLOv8] class not selected.")
            return
        cls_id = self._classes[row]["id"]
        hex_c = self._id2color[cls_id]
        r, g, b = int(hex_c[1:3],16), int(hex_c[3:5],16), int(hex_c[5:7],16)

        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = r, g, b
        rgba[..., 3] = global_mask * 255

        # 6) 레이어에 적용
        self._graphics_view._scene.label_item.add_mask(rgba)
        print(f"[YOLOv8] mask added – {global_mask.sum()} foreground px")
