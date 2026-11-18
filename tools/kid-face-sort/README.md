# kid-face-sort — 우리 아이 사진 자동 분류 (100% 로컬)

[InsightFace](https://github.com/deepinsight/insightface) `buffalo_l`의 검출(`det_10g.onnx`, SCRFD-10GF)과 인식(`w600k_r50.onnx`, ResNet50@WebFace600K) 모델을 ONNX Runtime으로 사용합니다. 이 앱은 detection/recognition 모듈만 로드하며,
사진 폴더에서 아이 얼굴을 찾아 아이별 폴더로 분류합니다. 사진은 어디에도 업로드되지 않습니다.

## 설치 (Mac, 한 줄)
```bash
cd kid-face-sort && bash install.sh
```
(Xcode CLT가 없으면 `xcode-select --install` 먼저. 모델은 처음 한 번만 ~280MB 다운로드)

## 사용법
```bash
./kidface.sh enroll 지우 ~/Pictures/ref_jiwoo/        # 기준 사진(아이 혼자 나온 사진 3~10장 권장)
./kidface.sh sort ~/Pictures/2026 -o ~/Pictures/sorted  # 기본: 심볼릭 링크 (--mode copy | dry)
./kidface.sh tune 지우 정답폴더/ 다른사람폴더/          # 임계값 추천
./kidface.sh list / ./kidface.sh forget 지우
```
- 결과: `sorted/<이름>/`, 애매한 사진은 `sorted/_unsure/`, 전체 점수는 `sorted/report.csv`
- 단체사진: 얼굴마다 점수를 매겨 한 명이라도 일치하면 해당 아이 폴더에 넣음 (아이 둘 다 나오면 두 폴더 모두)
- 기본 임계값 `-t 0.55`, `--margin 0.10` (0.45~0.55는 _unsure). 또래 아이끼리 최대 0.39까지 나와서 0.40은 너무 낮음
- 지원 형식: JPG/PNG/HEIC/HEIF/WEBP (EXIF 회전 자동 보정)

## 팁
- 아이 얼굴은 빨리 변하므로 6개월마다 최근 사진으로 `enroll`을 추가하세요(누적 저장).
- 형제·사촌은 점수가 높게 나올 수 있으니 `_unsure`는 사람이 확인하세요.

## 개인정보
- 임베딩(얼굴 특징 숫자)만 `~/.kidface/embeddings.npz`(권한 600)에 저장, 사진 원본은 복사/저장하지 않음(심볼릭 링크 기본).
- 네트워크는 최초 모델 다운로드에만 사용.

## 라이선스 주의
- 코드(insightface 패키지): MIT. **사전학습 모델(buffalo_l 등)은 비상업적 연구용만 허용**.
  가족 개인 사용은 문제없지만, 유료 서비스로 팔려면 InsightFace에 상업 라이선스 문의하거나
  대체 모델(예: dlib 기반 face_recognition — 모델 포함 MIT/CC0 계열, 정확도는 낮음)로 교체 필요.

## 성장 반영 (v2)
아이 얼굴은 계속 변하므로, 기준 얼굴을 **3개월 버킷(예: 2026-Q4)** 으로 나눠 관리합니다.
- **DB 메타데이터**: 각 기준 얼굴마다 파일 해시(sha1), 촬영일(EXIF DateTimeOriginal → 없으면 파일 수정일), 버킷, 점수, 추가 시각, origin(manual/auto) 저장. 구버전 DB는 자동 인식되며 `./kidface.sh migrate`로 새 형식 저장.
- **점수 규칙**: `점수 = max(코사인 × 가중치)`, `가중치 = max(0.85, 1 − 0.02 × 버킷거리)`
  - 사진 촬영일을 알면 → 사진 시기와 가까운 버킷의 기준 얼굴이 우선
  - 모르면 → 최신 버킷이 우선. 오래된 기준도 최대 15%만 감점되어 계속 쓰임
- `list` 로 버킷/출처별 개수 확인

### refresh (자동 보강)
```bash
./kidface.sh refresh 지우 ~/Pictures/sorted/report.csv      # dry-run: 추가 후보만 표시
./kidface.sh refresh 지우 ~/Pictures/2026-10/ --apply        # 실제 적용 (적용 전 자동 백업)
./kidface.sh rollback 지우     # 가장 최근 백업으로 복원 (all = 전체)
```
옵션: `--min-score 0.65` `--dup-cos 0.95` `--cap 20`(버킷당 최대, 초과 시 가장 다양한 얼굴만 유지)
백업: `~/.kidface/backups/<시각>.npz`

### 드리프트 안전 규칙 (다른 아이로 서서히 오염되는 것 방지)
1. 점수 0.65 이상만 후보 (sort 임계값 0.55보다 높게)
2. **수동 등록 기준(manual)만으로 계산한 점수도 0.65 이상**이어야 추가 (auto가 auto를 끌어들이지 못함)
3. `_unsure` 경로의 사진은 절대 추가 안 함
4. 한 사진에서 0.65 이상 얼굴이 2개 이상이면(형제 등) 제외
5. 같은 파일(sha1) / 거의 같은 얼굴(cos>0.95) 중복 제외
6. 버킷당 최대 20개, 수동 기준은 절대 삭제 안 함
7. 매 적용 전 백업 → 이상하면 `rollback`. 가끔 `sort` 결과를 눈으로 확인하세요.

### 매월 자동 실행 (macOS)
`schedule/monthly_refresh.sh` 가 `sort --mode dry` → `refresh --apply` 를 실행합니다.
**launchd (권장)**
```bash
cp schedule/com.kidface.refresh.plist ~/Library/LaunchAgents/   # 파일 안 YOURNAME/이름/폴더 수정
launchctl load ~/Library/LaunchAgents/com.kidface.refresh.plist
launchctl start com.kidface.refresh   # 즉시 테스트
```
사진 폴더가 ~/Pictures 등 보호 폴더면 `/bin/bash`에 *전체 디스크 접근 권한*이 필요할 수 있습니다(시스템 설정 → 개인정보 보호).
**cron**: `crontab -e` → `0 10 1 * * KIDFACE_NAME=지우 KIDFACE_PHOTOS=$HOME/Pictures/kids /bin/bash $HOME/kid-face-sort/schedule/monthly_refresh.sh`

## 스캔 캐시 (재실행 시 이미 본 사진 건너뛰기)
`~/.kidface/scan_cache.sqlite` (권한 600, 로컬 전용) 에 사진별로 저장:
파일 내용 해시(sha1) + 경로/크기/수정시각, 얼굴별 bbox·검출점수·**임베딩**, 아이별 점수, 판정(폴더), 모델명/버전, 기준DB 해시, 임계값, 스캔 시각.
- 같은 파일(크기·수정시각 동일)은 해시도 다시 안 계산하고 바로 건너뜀
- `enroll`/`refresh`로 기준이 바뀌면 → **얼굴 검출 없이 캐시된 임베딩으로 재채점만** (매우 빠름)
- 임계값이 바뀌어도 재채점만. 모델이 바뀌면 자동 재검출
- 파일을 옮겨도 내용이 같으면 해시로 인식
```bash
./kidface.sh sort 사진폴더 -o 결과            # 두 번째부터는 새/변경 사진만 검출
./kidface.sh sort 사진폴더 -o 결과 --rescan   # 강제 재검출
./kidface.sh sort 사진폴더 -o 결과 --no-cache # 캐시 사용 안 함
./kidface.sh refresh 지우 cache               # 폴더 재스캔 없이 캐시에서 바로 보강 후보 추출
./kidface.sh cache stats | clear | export 결과.csv
```
`-v`를 주면 캐시로 건너뛴 사진도 한 줄씩 출력합니다. 사진 원본은 캐시에 저장되지 않지만, 임베딩은 생체정보이므로 클라우드 동기화 폴더에 두지 마세요.

## 사진 자체에 결과 기록 (선택)
기본은 **캐시만** 사용하며 원본은 절대 수정하지 않습니다.
- `--write-meta` (= sidecar): 사진 옆에 `IMG_0001.xmp` 생성 (dc:subject `kidface:지우`, kidface:Scores `지우=0.7803`). 원본 무변경. 같은 이름의 기존 xmp(우리 것이 아닌)는 덮어쓰지 않음
- `--write-meta inplace`: **exiftool로 원본 파일 안에 XMP 키워드/점수 기록** (`brew install exiftool` 필요). 원본 바이트가 바뀌므로 iCloud 사진/동기화 재업로드, 백업 중복, 파일 수정일 변경이 생길 수 있음. 캐시는 새 해시로 자동 연결되어 재검출하지 않음
- `--finder-tag` (macOS만): Finder 태그 `kidface:지우` 추가 (확장 속성만 변경, 이미지 데이터 무변경). 기존 태그 유지
- 사진 앱(Photos 라이브러리) 내부 파일은 직접 수정하지 마세요. 내보낸 폴더에서 사용하세요.
