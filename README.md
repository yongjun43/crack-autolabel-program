# 🖌️ samat + YOLOv8-Seg 자동 라벨링 툴  
**최종 갱신: 2025-07-28 (Asia/Seoul)**

> SAMat GUI 에 **YOLOv8 Auto Label** 버튼을 추가해  
> 2830×2830 원본 이미지를 1024 패치 슬라이딩 → YOLOv8-Seg 추론 → 전역 마스크 병합까지 **원-클릭 라벨링**이 가능합니다.

---

## 1. 환경 · 프로젝트 준비

```bash
# ① Samat 소스 클론
git clone <repo_url> ~/samat
cd ~/samat

# ② Python 3.11 가상환경
python3.11 -m venv .venv
source .venv/bin/activate

# ③ Samat 개발 모드 설치
pip install -e .
```

### 📂 데이터셋 구조

```
~/samat/
├── images/    # 2830×2830 원본 PNG
├── labels/    # (빈 폴더) 자동 저장될 라벨
├── sam/       # 빈 회색 PNG (SAM 버그 회피용)
└── classes.json
```

### `config.toml`

```toml
[paths]
data = "/home/tenant/samat"
sam_weights = ""
```

---

## 2. UI 개조 요약

| 파일 | 수정 |
|------|------|
| `main_window.py` | · **SAM assistance 체크박스** → **YOLOv8 Auto Label** 버튼<br>· 버튼 → `on_yolo_button_click()` 슬롯 연결<br>· 단축키 충돌 라인 삭제 (`self.sam_checkbox.toggle()`) |
| `label_layer.py` | `add_mask(rgba)` 구현 → `self._pixmap` 위 RGBA 누적 합성 |
| GraphicsScene | `self._graphics_view._scene.label_item.add_mask(rgba)` 경로 |

---

## 3. YOLOv8-Seg 패치 추론 흐름

1. 2830×2830 → **1024×1024 / 256 픽셀 오버랩** 슬라이딩
2. 각 패치 → `model(tile, retina_masks=False)` 추론
3. 마스크 `> 0.5` → **이진화** 후 `global_mask |= patch`
4. `binary_closing(3×3)` 으로 seam 제거
5. 선택 클래스 색(RGBA) ↷ `add_mask()` 호출
6. 함수 마지막에 `self.save_current_label()` → 즉시 저장

---

## 4. 저장 트리거

| 이벤트 | 동작 |
|--------|------|
| 이미지 전환 `,` / `.` | `save_current_label()` → `labels/<stem>.png` |
| 프로그램 종료 | 동일 |
| YOLOv8 Auto Label 버튼 클릭 끝 | 즉시 저장(옵션) |

---

## 5. 의존성

```bash
pip install ultralytics opencv-python scipy numpy pillow
```

> **Tip** : 전체 의존성은 `pip freeze > requirements.txt` 로 추출해 커밋하면 편리합니다.

---

## 6. 사용 플로우

```bash
# Samat GUI 실행
python .
```

1. **Classes** 패널에서 라벨 클래스를 선택  
2. **YOLOv8 Auto Label** 버튼 클릭 → 자동 마스크 생성  
3. 필요 시 GUI로 수정 후 `,`/`.` 로 다음 이미지  
4. 전환·종료 시 **labels/ 폴더에 PNG** 자동 저장

---

### 🚀 TODO / 향후 개선
- [ ] Git LFS로 모델(`0715_seg.pt`) 관리  
- [ ] Retina masks 후-처리, TTA(optional)  
- [ ] CLI 배치 레이블러 스크립트

---

## 📝 라이선스
MIT License — 자유롭게 사용·수정·배포 가능하며, 출처 표시를 부탁드립니다.

