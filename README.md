# PXU — Hệ thống xét miễn, giảm học phần

Ứng dụng nội bộ hỗ trợ Sales nộp hồ sơ, OCR tài liệu, lập đề xuất miễn học phần và giảng viên xét duyệt. AI chỉ hỗ trợ; quyết định cuối cùng thuộc người có thẩm quyền.

Repository: [hphuongnam89/xetmiengiammonhocpxu](https://github.com/hphuongnam89/xetmiengiammonhocpxu), nhánh `main`.

**Người tiếp nhận:** làm lần lượt phần cài đặt, tài khoản, dữ liệu và kiểm tra bên dưới; sau đó đọc [HANDOVER.md](HANDOVER.md) để biết cần hoàn thiện gì, sửa ở đâu và nghiệm thu thế nào. Đây là bản đang phát triển, chưa nghiệm thu production.

## 1. Cấu trúc và dữ liệu được bàn giao

| Vị trí | Nội dung |
| --- | --- |
| `app/backend/` | Django + Django REST Framework; giao diện HTML dùng Django templates |
| `app/backend/api/` | API, màn hình web, upload, OCR, đề xuất và quyết định |
| `app/backend/reviews/` | Model, migration, Django Admin, các lệnh import |
| `app/config/import-manifests/` | Cấu hình ánh xạ cột/sheet Excel và danh sách PDF quy định |
| `app/docs/00-product/` … `16-deployment/` | Phạm vi, thiết kế và ghi nhận từng phase |
| `12. XÉT MIỄN MÔN/` | Excel/PDF nguồn đã đưa lên Git |

Repo hiện không có frontend Node/React riêng, Docker Compose, pipeline CI hay file khóa dependency. Celery có trong dependency nhưng chưa có worker/task OCR được tích hợp.

Git **không chứa** `.venv`, `.env` thực tế, SQLite local, tài liệu upload trong `app/backend/media/`, tài khoản hoặc model Ollama đã tải. Clone trên máy mới sẽ không có các bản ghi đã nhập/duyệt trên máy cũ. Muốn giữ nguyên trạng thái đó, xem phần 7.

## 2. Cài trên máy mới

### Chuẩn bị

- Git và Python **3.12** để cài mới với bộ dependency hiện tại. `pyproject.toml` cho phép Python từ 3.12 nhưng đang ràng buộc Pillow 10.4; [bảng tương thích chính thức của Pillow](https://pillow.readthedocs.io/en/stable/installation/python-support.html) hỗ trợ 3.12 cho dòng này, không liệt kê 3.13/3.14. Việc môi trường cũ chạy được không chứng minh cài sạch được trên Python mới hơn.
- Internet khi clone/cài package. Tài khoản GitHub có quyền repository nếu cần push.
- Chỉ khi dùng OCR ảnh/PDF scan mới cần thêm Ollama và Poppler; xem phần 5.

### macOS / Linux — Terminal

```bash
git clone https://github.com/hphuongnam89/xetmiengiammonhocpxu.git
cd xetmiengiammonhocpxu
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ./app/backend
python -m pip install "pytest>=8.3,<9" "pytest-django>=4.9,<5"
export APP_ENV=development
export DEBUG=true
export ALLOWED_HOSTS=localhost,127.0.0.1
```

### Windows — PowerShell

```powershell
git clone https://github.com/hphuongnam89/xetmiengiammonhocpxu.git
cd xetmiengiammonhocpxu
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ./app/backend
python -m pip install "pytest>=8.3,<9" "pytest-django>=4.9,<5"
$env:APP_ENV = "development"
$env:DEBUG = "true"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
```

Nếu PowerShell chặn activation, dùng `.\.venv\Scripts\python.exe` thay cho `python` ở các lệnh sau; không cần thay chính sách toàn máy. Nếu clone xong đang ở một thư mục khác, quay lại thư mục có `README.md` trước khi chạy lệnh.

**Cấu hình local:** mặc định dùng SQLite ở `app/backend/db.sqlite3`, file upload local và cache trong bộ nhớ; không cần PostgreSQL/Redis. Dùng terminal không có các biến cấu hình production cũ (`DB_ENGINE`, `DB_NAME`, `MEDIA_STORAGE_BACKEND`).

**Lưu ý về `.env`:** [`.env.example`](app/backend/.env.example) hiện là mẫu **production**. Code chỉ đọc biến môi trường qua `os.getenv`, chưa gọi `load_dotenv()`. Chỉ copy thành `.env` sẽ không nạp cấu hình. Các lệnh `export` / `$env:...` ở trên có hiệu lực trong terminal hiện tại và phải đặt lại khi mở terminal mới. `SECRET_KEY` mặc định chỉ phục vụ local.

### Khởi tạo và chạy — từ thư mục gốc repo

```bash
python app/backend/manage.py migrate
python app/backend/manage.py check
python app/backend/manage.py createsuperuser
python app/backend/manage.py runserver 127.0.0.1:8000
```

Khi tạo superuser, tự đặt tên/mật khẩu; validator hiện yêu cầu mật khẩu tối thiểu 12 ký tự. Mỗi lần làm việc tiếp theo: mở repo, kích hoạt `.venv`, đặt biến local rồi chạy `runserver`; không cần tạo lại database hoặc tài khoản.

| Địa chỉ local | Công dụng |
| --- | --- |
| `http://127.0.0.1:8000/health/` | Trả JSON `{"status":"ok"}`; chỉ là kiểm tra tiến trình web |
| `http://127.0.0.1:8000/accounts/login/` | Đăng nhập |
| `http://127.0.0.1:8000/app/` | Dashboard nghiệp vụ |
| `http://127.0.0.1:8000/admin/` | Quản trị Django |
| `http://127.0.0.1:8000/app/admin/metrics/` | Thống kê dành cho Admin |

Địa chỉ `/` chưa có trang chủ; mở `/app/`. `runserver` dành cho phát triển, không phải cách triển khai production.

## 3. Tạo tài khoản và thử giao diện

1. Đăng nhập `/admin/` bằng superuser.
2. Trong **Users**, tạo tài khoản Sales và Teacher thử nghiệm, bật `Active` và đặt mật khẩu riêng.
3. Trong **User profiles**, tạo profile cho từng tài khoản, chọn đúng `SALES` hoặc `TEACHER`.
4. Để `Staff status` **tắt** ở hai tài khoản này. Code hiện coi mọi user có `is_staff=True` là Admin nghiệp vụ; Django Group không thay thế `UserProfile.role`.
5. Đăng nhập Sales tại `/accounts/login/`, tạo hồ sơ qua `/app/submissions/new/`, chọn giảng viên và upload tài liệu thử không chứa dữ liệu thật. Định dạng được nhận: PDF/JPEG/PNG, tối đa 10 MB/file.
6. Mở màn hình OCR của tài liệu: `/app/documents/<document_uuid>/extraction/`. Sales phụ trách hoặc Admin có thể chạy OCR; người có quyền có thể đối chiếu/sửa/xác nhận trường trích xuất. Teacher chỉ truy cập hồ sơ được giao.
7. Thử bằng hai tài khoản Sales và hai Teacher để kiểm tra không xem được hồ sơ ngoài quyền. Xem danh sách nghiệm thu đầy đủ trong [HANDOVER.md](HANDOVER.md).

Giảng viên mở `/app/documents/<document_uuid>/extraction/`, đối chiếu và xác nhận từng trường. Sau đó ghép tường minh tên môn, điểm, tín chỉ (và mã môn nếu có) từ cùng lần OCR, chọn môn đích trong một curriculum đã duyệt. Không có bước ghép tự động giữa các trường rời. Sales phụ trách/Admin mở `/app/submissions/<submission_uuid>/review/` để chọn các dòng đã ghép, rule đã được xác nhận về học thuật và phiên bản curriculum đích, rồi tạo đề xuất. Giảng viên được giao xem nguồn/căn cứ và ghi quyết định cuối tại cùng màn hình.

Nếu chưa có curriculum/rule/mapping đã duyệt, hệ thống không tạo đề xuất như thể dữ liệu đó đã được duyệt. Dữ liệu rule và mapping thực tế trong repo vẫn cần chủ học thuật xác minh; deterministic evaluator hiện chưa thực thi đầy đủ nội dung rule và mapping chưa gắn chặt với phiên bản curriculum.

## 4. Nhập lại dữ liệu trên database mới

Mở terminal thứ hai, kích hoạt `.venv` và cấu hình local như phần 2. **Tất cả lệnh phần này chạy tại thư mục gốc repo**, kể cả lệnh OCR quy định vì manifest PDF dùng đường dẫn tương đối từ đó.

Nếu đã khôi phục database từ máy cũ, kiểm tra dữ liệu trước, không import/duyệt lại theo thói quen. Các lệnh sau giữ file nguồn nguyên trạng. Giữ nguyên tên file Unicode và thư mục nguồn; khi báo không tìm thấy file, dùng tab-completion để lấy đúng tên trên máy.

### 4.1. Năm khung chương trình

Ví dụ xem trước QTKD, chưa ghi database:

```bash
python app/backend/manage.py import_curriculum --workbook "12. XÉT MIỄN MÔN/5. Khung CTĐT QTKD-NBS-29042024.xlsx" --config app/config/import-manifests/curriculum-qtkd.json --dry-run
```

Có thể thêm `--dry-run` vào từng lệnh bên dưới để kiểm tra trước. Khi sẵn sàng nhập, chạy cả năm lệnh:

```bash
python app/backend/manage.py import_curriculum --workbook "12. XÉT MIỄN MÔN/5. Khung CTĐT QTKD-NBS-29042024.xlsx" --config app/config/import-manifests/curriculum-qtkd.json
python app/backend/manage.py import_curriculum --workbook "12. XÉT MIỄN MÔN/CTDT Ngành Ngôn Ngữ Trung_NBS.xlsx" --config app/config/import-manifests/curriculum-nnt.json
python app/backend/manage.py import_curriculum --workbook "12. XÉT MIỄN MÔN/CTDT Ngôn ngữ Anh_NBS.xlsx" --config app/config/import-manifests/curriculum-nna.json
python app/backend/manage.py import_curriculum --workbook "12. XÉT MIỄN MÔN/NBS_CT đồ họa kỹ thuật số.xlsx" --config app/config/import-manifests/curriculum-dhktso.json
python app/backend/manage.py import_curriculum --workbook "12. XÉT MIỄN MÔN/NBS_Khung CTDT Du Lịch.xlsx" --config app/config/import-manifests/curriculum-tourism.json
python app/backend/manage.py activate_imported_curricula
```

Import tạo `DRAFT`; chạy lại cùng checksum/sheet sẽ bỏ qua dữ liệu đã nhập. Lệnh cuối **chỉ xem trước** kích hoạt, kỳ vọng 5 khung, 380 dòng nguồn, 301 dòng có mã/tên và 79 dòng cấu trúc. Không tự bổ sung tín chỉ trống.

`activate_imported_curricula --apply` là lệnh đặc thù khôi phục bộ 380 dòng đã được chấp thuận trong lần phát triển trước. Chỉ chạy khi đúng bộ nguồn và chủ nghiệp vụ xác nhận tiếp tục dùng bộ đó. Lệnh này đặt trạng thái `APPROVED` nhưng audit không có tài khoản người duyệt (`actor=None`); không dùng nó thay quy trình duyệt khung mới. Nếu số dòng khác hoặc có nhiều phiên bản một chương trình, dừng đối chiếu thay vì bỏ kiểm tra trong code.

### 4.2. Kết quả xét lịch sử QTKD

Xem trước toàn bộ workbook theo cấu hình hiện có:

```bash
python app/backend/manage.py stage_historical_workbook --workbook "12. XÉT MIỄN MÔN/16 SV KHUNG CŨ XÉT LẠI KHUNG MỚI_QTKD K2.xlsx" --config app/config/import-manifests/historical-qtkd-16-students.json
```

Kỳ vọng: 16 sheet khớp, 107 sheet bỏ qua, 155 dòng ứng viên gồm 132 `FULL` và 23 `PARTIAL`. Kiểm tra đúng nguồn rồi chạy lại **thêm `--apply`** để lưu. Các dòng vẫn `PENDING`, không tự trở thành precedent được duyệt. `FULL/PARTIAL` ở đây là kết quả đọc từ cột nguồn, không phải trạng thái đã nghiệm thu.

Giảng viên/chủ nghiệp vụ phải rà nguồn; Admin dùng quy trình approve/reject trong **Historical decisions** để ghi người và thời điểm duyệt. Những sheet không khớp cần manifest riêng. Lệnh `import_historical_reviews` dành cho một sheet với config khác; không truyền manifest staging nhiều sheet ở trên cho lệnh đó.

### 4.3. Văn bản quy định

Kiểm tra file/page, chưa gọi AI và chưa ghi dữ liệu:

```bash
python app/backend/manage.py stage_scanned_rulebooks --config app/config/import-manifests/rulebook-sources.json
```

Sau khi cấu hình Ollama/Poppler ở phần 5, chạy lại **thêm `--apply`** để OCR và lưu `RuleVersion` dạng `DRAFT`, `UNVERIFIED_OCR`. Lệnh này OCR mọi trang nguồn, lưu từng trang và có thể tiếp tục lần sau nếu bị ngắt. Đây không phải bộ quy tắc thực thi được duyệt.

Để duyệt quy tắc/mapping cần nguồn đối chiếu và xác nhận của chủ học thuật; xem [HANDOVER.md](HANDOVER.md) và [các bảng còn cần chép/kiểm chứng](app/docs/02-rulebook/PENDING_MAPPINGS.md). Không tự đặt `verified=true` chỉ để vượt kiểm tra của Admin.

## 5. Bật OCR ảnh/PDF scan

PDF có text layer dùng `pypdf` sẵn trong dependency. Ảnh/PDF scan gọi Ollama; PDF scan còn cần `pdftoppm` của Poppler.

1. Cài và mở [Ollama](https://ollama.com/download). Nếu chưa có dịch vụ chạy, mở terminal riêng và chạy `ollama serve`.
2. Chạy `ollama list` để xem model đã cài. Model cần hỗ trợ ảnh theo [Ollama Vision](https://docs.ollama.com/capabilities/vision).
3. Code mặc định dùng tag `gemma4:e4b-it-qat`. Có thể thử `ollama pull gemma4:e4b-it-qat`; nếu tag không có ở môi trường đích, chọn model vision thực sự có sẵn, tải bằng `ollama pull <model-tag>` rồi đặt `OLLAMA_VISION_MODEL` đúng tag. Lần bàn giao tài liệu chưa chạy OCR model thật.
4. Cài Poppler: macOS có Homebrew dùng `brew install poppler`; Ubuntu/Debian dùng `sudo apt install poppler-utils`. Windows cần bản Poppler có `pdftoppm.exe`, thêm thư mục `bin` vào PATH hoặc đặt `PDFTOPPM_BIN` tới file đó. Kiểm tra bằng `pdftoppm -v`.
5. Trong terminal chạy Django, đặt biến rồi khởi động lại server.

macOS/Linux:

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_VISION_MODEL=gemma4:e4b-it-qat
# Chỉ cần nếu pdftoppm không nằm trong PATH; thay bằng đường dẫn thật:
# export PDFTOPPM_BIN=/absolute/path/to/pdftoppm
```

PowerShell:

```powershell
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OLLAMA_VISION_MODEL = "gemma4:e4b-it-qat"
# Chỉ cần nếu không có trong PATH; thay bằng đường dẫn thật:
# $env:PDFTOPPM_BIN = "C:\path\to\poppler\bin\pdftoppm.exe"
```

Thử một ảnh và một PDF scan nhỏ, kiểm tra trường đọc được và đối chiếu bản gốc. Chỉ thấy `NEEDS_REVIEW` **không đủ chứng minh OCR thành công**: code hiện cũng trả trạng thái này khi Ollama/Poppler lỗi. OCR hồ sơ scan hiện giới hạn 10 trang và chạy đồng bộ trong request; lệnh OCR văn bản quy định ở phần 4.3 là luồng riêng xử lý mọi trang.

## 6. Kiểm tra trước khi tiếp tục phát triển

Từ thư mục gốc repo, môi trường local đã kích hoạt:

```bash
python app/backend/manage.py check
python app/backend/manage.py makemigrations --check --dry-run
cd app/backend
python -m pytest -q
cd ../..
git diff --check
```

Suite hiện có một test gọi adapter OCR với ảnh giả. Để test không phụ thuộc model thật, đặt `OLLAMA_BASE_URL=http://127.0.0.1:9` riêng cho lượt test. macOS/Linux: `OLLAMA_BASE_URL=http://127.0.0.1:9 python -m pytest -q`; PowerShell: đặt `$env:OLLAMA_BASE_URL` trước khi test và trả về `http://127.0.0.1:11434` trước khi dùng OCR thật. Test hiện tạo một số file upload dưới `media/` local; chúng bị Git bỏ qua.

Mốc kiểm tra 30/09/2026: clone nguồn `8c6dc62` sang thư mục tạm, migrate database rỗng và chạy baseline 19 test. Khi chạy import thật phát hiện lỗi đọc header sau khi đóng workbook; bản bàn giao này sửa lỗi và bổ sung test hồi quy, **20 test đạt**, `check`/migration check sạch. Đã nhập lại 5 khung trên database tạm, đối chiếu 380 dòng và chạy preview lịch sử/quy định. Dùng interpreter/dependency sẵn có trên máy bàn giao (Python 3.14.5, Django 5.2.17); không đồng nghĩa đã cài sạch toàn bộ dependency trên Python 3.12/Windows. Đã build wheel bằng Poetry backend với `pip wheel --no-deps`. Chi tiết: [HANDOVER.md](HANDOVER.md).

## 7. Giữ nguyên dữ liệu khi chuyển máy

Chọn một trong hai cách:

- **Môi trường phát triển mới:** migrate, tạo tài khoản và import như trên. Không có hồ sơ/quyết định/OCR từ máy trước.
- **Tiếp tục đúng trạng thái máy cũ:** bàn giao riêng database và thư mục media cùng thời điểm, qua kênh riêng được phép truy cập. Cả hai không được lưu trong Git.

Với local SQLite: ghi lại `git rev-parse HEAD` trên máy cũ, dừng các tiến trình ghi (server/OCR/import), sao lưu database và toàn bộ `app/backend/media/`. Nếu có SQLite WAL, tạo backup nhất quán bằng SQLite backup API thay vì chỉ chép file chính khi database đang mở. Có thể tạo bản backup không trùng tên từ thư mục gốc:

```bash
python -c "import sqlite3, datetime; name='handover-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.sqlite3'; src=sqlite3.connect('file:app/backend/db.sqlite3?mode=ro', uri=True); dst=sqlite3.connect(name); src.backup(dst); dst.close(); src.close(); print(name)"
```

Trên máy mới, dùng cùng phiên bản code trước, cài dependency, dừng server rồi đặt bản backup vào `app/backend/db.sqlite3` và media vào đúng `app/backend/media/`. Sao lưu dữ liệu đích nếu đã tồn tại trước khi thay. Sau đó chạy `migrate`, `check`, đăng nhập và mở một hồ sơ/tài liệu đã bàn giao. Tài khoản đã có trong database không cần tạo lại; secret/cấu hình thật và model Ollama phải bàn giao/cài riêng. Kiểm tra `git status --short` không có dữ liệu runtime trước mọi lần push.

## 8. Làm tiếp và cập nhật GitHub

Từ thư mục gốc repo, khi working tree sạch:

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/ocr-to-recommendation
```

Tên nhánh là ví dụ cho đầu việc đầu tiên; đổi theo công việc. Làm theo thứ tự trong [HANDOVER.md](HANDOVER.md), chạy test và kiểm tra giao diện liên quan, rồi:

```bash
git status --short
git diff --check
git add <cac-file-da-sua>
git diff --cached --check
git diff --cached --stat
git commit -m "feat: describe the completed change"
git push -u origin HEAD
```

Thay `<cac-file-da-sua>` bằng danh sách đường dẫn thực tế, kiểm tra nội dung staged rồi mới commit. Push cần quyền ghi GitHub; nếu HTTPS hỏi mật khẩu, dùng cơ chế đăng nhập GitHub/PAT của bạn, không ghi token vào URL/file repo. Mở pull request để review và merge; máy khác chỉ lấy thay đổi đã merge vào `main` khi `git pull`. Nếu remote đi trước, cập nhật/giải quyết xung đột có kiểm tra; không force-push `main`. GitHub chứa code, **push không tự triển khai website**.

## 9. Lỗi thường gặp

| Hiện tượng | Kiểm tra / cách xử lý |
| --- | --- |
| Không cài được Pillow trên Python mới | Dùng Python 3.12 với dependency hiện tại; nâng dependency là đầu việc riêng cần test |
| `No module named django`, `api` hoặc `config` | Kích hoạt đúng venv, cài editable, chạy `python app/backend/manage.py ...` từ repo; chưa dùng wheel để deploy độc lập |
| Copy `.env` nhưng cấu hình không đổi | App chưa tự đọc `.env`; đặt biến môi trường vào tiến trình đang chạy |
| Bị yêu cầu PostgreSQL/Redis/private storage | `APP_ENV` đang là `production`; dùng đúng cấu hình local ở phần 2 |
| `no such table` | Chạy `migrate`; kiểm tra có vô tình dùng `DB_NAME` của database khác không |
| `/` trả 404 | Dùng `/app/` hoặc `/accounts/login/` |
| Đăng nhập được nhưng thiếu quyền / danh sách teacher trống | Kiểm tra `UserProfile.role`, `is_staff`, teacher assignment |
| Có OCR status nhưng không có text/fields | Kiểm tra Ollama/model/Poppler; `NEEDS_REVIEW` hiện chưa phân biệt lỗi với chờ duyệt |
| Khung chương trình/lịch sử không xuất hiện sau clone | Database không nằm trên Git; thực hiện phần 4 hoặc 7 |
| Manifest không tìm thấy file hoặc header | Chạy từ repo root, giữ tên Unicode, đối chiếu đúng workbook/sheet/header; không đoán cột thay thế |

## 10. Trước khi đưa lên production

Đọc [PRODUCTION.md](app/docs/16-deployment/PRODUCTION.md) và phần production trong [HANDOVER.md](HANDOVER.md). Hiện repo mới có ràng buộc cấu hình; chưa có bộ triển khai vận hành hoàn chỉnh. Cần hoàn thiện server WSGI/ASGI, static, storage riêng tư, PostgreSQL, Redis TLS, HTTPS, backup/restore và kiểm tra phân quyền trên môi trường đích trước nghiệm thu.
