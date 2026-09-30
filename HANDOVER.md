# Bàn giao phát triển — PXU xét miễn học phần

Cập nhật: **30/09/2026**. Nền importer tại `d335033`; bắt đầu phát triển tiếp từ `bdb1e30` trên nhánh `feat/ocr-to-recommendation`. Hướng dẫn chạy/nhập dữ liệu: [README.md](README.md).

## 1. Nhận việc trong buổi đầu

1. Clone/pull `main`, ghi lại commit và kiểm tra working tree. Đọc README để cài local; không dùng `.env.example` production như cấu hình local.
2. Chọn khởi tạo mới hoặc khôi phục database/media từ máy cũ. Git không mang theo trạng thái phê duyệt, tài khoản hay hồ sơ đã xử lý.
3. Chạy migrate, system check, kiểm tra migration và test baseline. Ghi phiên bản Python/dependency thực tế.
4. Tạo Sales/Teacher thử, chạy luồng tạo hồ sơ → upload → mở bản gốc → OCR → xác nhận/sửa trường. Đánh dấu chỗ chưa có đường đi từ giao diện.
5. Làm đầu việc A bên dưới; cần chủ học thuật xác nhận đầu việc B song song trước khi nghiệm thu kết quả miễn môn. Mỗi đầu việc dùng commit/PR nhỏ có bằng chứng kiểm tra.

Các `STATUS.md` trong `app/docs/` ghi theo thời điểm từng phase, không phải ảnh chụp toàn hệ thống hiện tại. Ví dụ phase 9 còn ghi thiếu notification/UI nhưng phase 10 và code đã có; phase 10 còn ghi thiếu dashboard nhưng phase 11 đã có metrics/CSV. Dùng code và kết quả chạy để xác nhận, không cộng các nhãn “hoàn thành” thành kết luận production-ready.

## 2. Hiện có gì và giới hạn ở đâu

| Mảng | Đã có trong code | Giới hạn cần nhớ |
| --- | --- | --- |
| Tài khoản/quyền | Session login, `UserProfile`, Sales/Teacher/Admin, kiểm tra owner/assignment ở các luồng chính | Mọi `is_staff=True` được coi là Admin nghiệp vụ; chưa có bộ test đầy đủ mọi endpoint/role |
| Hồ sơ/tài liệu | Tạo hồ sơ, chọn teacher, upload, checksum, xem file qua view có kiểm tra quyền | Chưa có quét malware và triển khai private storage production |
| OCR | pypdf text, Ollama ảnh/scan, raw evidence, màn hình sửa/xác nhận/thêm trường; giáo viên có thể ghép tường minh các trường đã xác nhận thành dòng môn học | OCR đồng bộ, scan hồ sơ tối đa 10 trang; lỗi bị gộp vào `NEEDS_REVIEW`; không tự nhóm tên/điểm/tín chỉ từ các dòng khác nhau |
| Danh mục/nguồn | Import 5 khung, giữ ô/dòng nguồn, staging lịch sử, OCR draft quy định | Không tự khôi phục qua Git; phần lớn nội dung học thuật cần rà/duyệt |
| Đề xuất | API/UI tạo run từ dòng môn học đã ghép ở server, yêu cầu rule/curriculum đã duyệt, idempotency, mapping `APPROVED`, lưu snapshot field/document/curriculum | Cần chủ học thuật rà nguồn thật; evaluator chưa thực thi `RuleVersion.definition`; mapping chưa ràng buộc phiên bản curriculum; OCR không tự phát hiện đủ dòng bảng |
| Xét duyệt | Teacher quyết định/override có lý do, audit và thông báo trong app | Cần kiểm tra trạng thái hồ sơ khi nhiều run, chạy lại hoặc bổ sung tài liệu |
| Quản trị | Django Admin cho rule/mapping/curriculum/history; metrics và CSV tổng hợp | Chưa có gói triển khai, CI và nghiệm thu end-to-end production |

### Điểm cần hiểu trước khi sửa rule engine

[`api/rule_engine.py`](app/backend/api/rule_engine.py) hiện chỉ kiểm tra evidence, trạng thái rule, điểm số `>=5`, tín chỉ `>0` và `content_match`. API hiện đã dựng `items` từ các dòng OCR xác nhận phía server; nó không nhận điểm/evidence hay `content_match` của caller. Tuy vậy, evaluator **không thực thi nội dung `RuleVersion.definition` như một bộ luật cấu hình**. Mapping phải khớp tên/mã môn nguồn với mã môn đích và có xác nhận học thuật, nhưng chưa ràng buộc đầy đủ theo phiên bản chương trình/thời hiệu. Khi mapping thiếu hoặc nhập nhằng, kết quả cần Teacher review; nhánh `PARTIAL` chưa được tự suy ra từ nội dung mapping.

Vì vậy, “có rule `APPROVED`” chưa chứng minh đủ điều kiện tính kết quả học thuật. Precedent lịch sử được duyệt hiện chỉ thêm thông tin tổng hợp, không thay quyết định của rule engine. Không suy diễn threshold/mapping/ngoại lệ từ code đơn giản này thành quy định của trường.

## 3. Các bước hoàn thiện theo thứ tự

### A. Nối OCR đã xác nhận → đề xuất học phần → màn hình xét

**Tiến độ 30/09/2026:** Đã triển khai nền luồng ở nhánh `feat/ocr-to-recommendation`: mô hình `ExtractedCourseRow`; ghép thủ công các field `HUMAN_ACCEPTED` cùng extraction run; chọn môn đích trong curriculum/course đã duyệt; tạo run từ row ID phía server; lưu giá trị field gốc/đã xác nhận, evidence, trang, checksum tài liệu, mapping và curriculum; giao diện Sales tạo/xem run và Teacher đã giao ghi quyết định. Một run được đánh dấu hiện hành; run mới thay thế run hiện hành và API từ chối quyết định run cũ. Đã có test API/UI với fixture học thuật tổng hợp. **Đầu việc A chưa nghiệm thu đầy đủ:** chưa có nguồn rule/mapping thật được chủ học thuật duyệt trên database dùng được; OCR bảng vẫn cần người rà/ghép thủ công; cần UAT phân quyền nhiều tài khoản, chạy lại sau khi thay tài liệu, và kiểm tra deployment.

**Bắt đầu tại:** [`api/web.py`](app/backend/api/web.py), [`api/extraction.py`](app/backend/api/extraction.py), [`api/recommendations.py`](app/backend/api/recommendations.py), [`reviews/models.py`](app/backend/reviews/models.py), các template trong `app/backend/reviews/templates/reviews/`.

1. Xác định schema một dòng môn học: tên/mã môn nguồn, điểm, tín chỉ, tài liệu/trang/ô và trường đã được người dùng xác nhận. Các `ExtractedField` hiện là trường rời; không ghép các tên/điểm/tín chỉ khác dòng theo phỏng đoán.
2. Chọn chương trình/phiên bản curriculum đích rõ ràng; hiển thị các trường thiếu cần bổ sung. Chỉ lấy giá trị đã xác nhận làm đầu vào nghiệp vụ.
3. Dựng `items` phía server từ dữ liệu có quyền truy cập. Kiểm tra kiểu dữ liệu, giá trị hữu hạn, danh mục môn hợp lệ, chống giả evidence/điểm từ request; dữ liệu không đủ chuyển rà soát.
4. Thêm thao tác tạo/xem đề xuất ở giao diện, chọn rule/mapping đúng phiên bản đã duyệt, giữ snapshot nguồn và idempotency. Chưa có rule được duyệt thì báo rõ điều kiện còn thiếu.
5. Đưa kết quả tới Teacher được giao; hiển thị đề xuất AI/rule và quyết định cuối riêng biệt. Xác định run nào có hiệu lực khi chạy lại hoặc thay tài liệu.

**Hoàn tất khi:** hồ sơ thử đi được từ upload tới đề xuất và giảng viên quyết định ngay trên UI; truy ngược được mỗi kết quả về nguồn; trường chưa xác nhận không tự được xét đủ điều kiện; gọi lại cùng key không tạo trùng; người ngoài hồ sơ không tạo/xem/sửa được kết quả. Bộ nguồn học thuật chưa duyệt chỉ dùng dữ liệu giả được ghi nhãn để test kỹ thuật.

### B. Chốt và triển khai bộ quy tắc học thuật

**Bắt đầu tại:** [`02-rulebook/PENDING_MAPPINGS.md`](app/docs/02-rulebook/PENDING_MAPPINGS.md), [`02-rulebook/rules.yaml`](app/docs/02-rulebook/rules.yaml), [`api/rule_engine.py`](app/backend/api/rule_engine.py), [`reviews/admin.py`](app/backend/reviews/admin.py), model `RuleVersion` và `RuleMappingVersion`.

1. Chủ học thuật đối chiếu PDF gốc và xác nhận hiệu lực áp dụng. Tài liệu candidate trong repo không tự có giá trị phê duyệt.
2. Chép/kiểm chứng bảng chính trị, pháp luật, GDQP, GDTC, ngoại ngữ, CNTT và ngoại lệ theo trang nguồn. Ghi điều kiện, môn đích, chuyển đổi điểm, thời hạn và người duyệt.
3. Chốt schema rule/mapping, liên kết chương trình/phiên bản và thời hiệu; làm evaluator đọc nội dung đã duyệt thay vì chỉ kiểm tra cờ trạng thái.
4. Bổ sung giới hạn tín chỉ toàn hồ sơ, ngoại lệ và partial recognition theo căn cứ đã xác nhận. Giữ kết quả không chắc chắn ở trạng thái cần người xét.
5. Mỗi điều kiện có test từ nguồn: dưới/đúng/trên ngưỡng, chứng chỉ hết hạn, thiếu evidence, khác ngành/phiên bản, không có mapping, chạm/vượt cap, FULL/PARTIAL/NOT_ELIGIBLE.

**Cổng duyệt hiện tại:** rule cần `definition.rules` và `academic_owner_review` có `verified=true`, `reviewer`, `note`; mapping cần bộ xác nhận tương tự trong `mapping_data`. Các trường này ghi nhận một xác nhận đã thực hiện, không phải hướng dẫn tự duyệt. Rule/mapping đã duyệt phải tạo phiên bản mới khi sửa.

**Hoàn tất khi:** người phụ trách học thuật ký/xác nhận bộ nguồn và bảng ca kiểm thử; kết quả từng ca khớp; rule không duyệt/không hiệu lực không chạy được; định danh phiên bản và evidence được lưu trong kết quả.

### C. Hoàn thiện dữ liệu khung chương trình và lịch sử

**Bắt đầu tại:** [`app/config/import-manifests/`](app/config/import-manifests/), [`reviews/management/commands/`](app/backend/reviews/management/commands/), các phase 14–15.

1. Rà 5 khung đã nhập: 380 dòng nguồn gồm 301 dòng mã/tên và 79 dòng cấu trúc; kiểm tra tín chỉ trống, mã trùng, nhóm tự chọn. Không đổi dòng cấu trúc thành học phần.
2. Duyệt curriculum theo tài khoản thực và phạm vi được giao. `activate_imported_curricula` là batch cố định cho bộ dữ liệu cũ, không phải importer/approval chung cho mọi nguồn.
3. Rà 155 dòng lịch sử đang ở `PENDING`, đối chiếu ô nguồn rồi approve/reject. “132 FULL/23 PARTIAL” không có nghĩa đã được duyệt.
4. Phân loại 107 sheet không khớp và các workbook khác; chỉ bổ sung manifest sau khi xác nhận header/cột. Dry-run, kiểm tra số dòng, import idempotent và giữ provenance.
5. Xây chức năng nhập phiên bản mới, so sánh thay đổi và duyệt có audit; không sửa đè dữ liệu nguồn đã phê duyệt.

**Hoàn tất khi:** mỗi dòng dùng trong xét có nguồn và trạng thái duyệt rõ ràng; phần chưa rà có danh sách riêng; chạy lại không nhân bản; số dòng và checksum đối chiếu được trên máy mới.

### D. Làm OCR vận hành ổn định

**Bắt đầu tại:** [`api/ollama_ocr.py`](app/backend/api/ollama_ocr.py), [`api/extraction.py`](app/backend/api/extraction.py), model `ExtractionRun`/`AIUsageEvent`.

1. Tách trạng thái lỗi kết nối/model/render/parser khỏi `NEEDS_REVIEW`; lưu lỗi hữu ích mà không lộ tài liệu/secret, cho phép thử lại.
2. Đưa OCR dài sang job nền có trạng thái, giới hạn đồng thời, retry và chống chạy trùng. Cấu hình worker/broker thực sự; dependency Celery hiện chưa tạo ra luồng bất đồng bộ.
3. Xử lý mọi trang hoặc báo rõ trang chưa đọc; không âm thầm dừng ở 10 trang. Kiểm tra cả PDF có text xen trang scan.
4. Bảo toàn liên kết các ô cùng môn, evidence trang/vị trí và dữ liệu gốc; không dùng điểm confidence như thay thế người kiểm chứng.
5. Mock dịch vụ ngoài trong unit test; bổ sung smoke test riêng trên model thật với ảnh/PDF nhiều bố cục. Ghi model tag và bộ mẫu đã kiểm thử.

**Hoàn tất khi:** OCR dài không giữ request web; lỗi/thử lại rõ; đủ trang và truy vết field; token usage được ghi nhận; giảng viên có thể sửa mà raw evidence còn nguyên.

### E. Kiểm tra và hoàn thiện luồng nghiệp vụ

**Bắt đầu tại:** [`api/web.py`](app/backend/api/web.py), [`api/views.py`](app/backend/api/views.py), [`api/permissions.py`](app/backend/api/permissions.py), [`api/notifications.py`](app/backend/api/notifications.py), `reviews/templates/`.

- Kiểm tra Sales chỉ xem hồ sơ của mình, Teacher chỉ xem hồ sơ được giao; bao phủ danh sách, chi tiết, upload/download, OCR, recommendation, quyết định và notification cả API lẫn UI.
- Hoàn thiện phân công lại Teacher, yêu cầu bổ sung, từ chối, nộp lại và thông báo theo state machine đã thống nhất. Tài liệu sản phẩm mô tả các luồng này nhưng không xem đó là bằng chứng đã có đủ nút/endpoint.
- Đối chiếu logic hoàn tất hồ sơ giữa API và UI, nhất là nhiều recommendation run và quyết định còn thiếu; thống nhất quy tắc khóa/chỉnh sửa sau khi chốt.
- Kiểm tra form validation/CSRF, double-submit, trang rỗng, lỗi upload/OCR và bố cục trên điện thoại. Bổ sung xuất kết quả hồ sơ nếu nằm trong phạm vi chủ nghiệp vụ xác nhận.

**Hoàn tất khi:** chạy checklist phần 4 bằng các tài khoản độc lập, ghi kết quả và bằng chứng UI, không chỉ dựa vào unit test.

### F. Cài đặt tái lập và triển khai

**Bắt đầu tại:** [`pyproject.toml`](app/backend/pyproject.toml), [`config/settings.py`](app/backend/config/settings.py), [`.env.example`](app/backend/.env.example), [`16-deployment/PRODUCTION.md`](app/docs/16-deployment/PRODUCTION.md).

1. Chọn phiên bản Python hỗ trợ và khóa dependency. Xác minh cài sạch trên máy đích; test group Poetry không được cài tự động bằng `pip install -e`, nên README cài test packages riêng.
2. Nếu deploy bằng wheel, bổ sung package `api`: danh sách `tool.poetry.packages` hiện chỉ có `config` và `reviews`. Build wheel thành công chưa chứng minh package chạy độc lập. Hướng dẫn hiện chạy từ checkout bằng `manage.py`.
3. Quyết định cơ chế nạp biến môi trường cho web/worker/management command. Hiện `.env` chưa tự nạp; không chỉ thêm `.env` rồi coi đã cấu hình xong.
4. Tạo CI: cài sạch, `check`, migration check, tests, build/package; dùng dữ liệu test giả và mock OCR. Khi có worker/storage, bổ sung integration test tương ứng.
5. Cấu hình PostgreSQL với SSL, Redis `rediss://`, secret thực, private object storage có backend đã cài, credentials/ACL phù hợp; kiểm tra đường mở tài liệu qua storage thật. Code mới kiểm tra class storage, không chứng minh bucket riêng tư.
6. Thêm server WSGI/ASGI, cách chạy tiến trình, `collectstatic`, phục vụ static và reverse proxy HTTPS. Nếu container hóa, viết Dockerfile/Compose cùng healthcheck và volume phù hợp.
7. Hoàn thiện giới hạn upload/quét malware, giám sát, xoay log/secret, MFA quản trị và backup/restore drill. Chạy `check --deploy` với cấu hình production thật và xử lý các cảnh báo còn lại theo hạ tầng.
8. UAT trên staging từ trình duyệt tới database/storage/worker; kiểm tra phân quyền, OCR model thật, tắt/mở dịch vụ, khôi phục backup. Lập hướng dẫn rollback cùng quy trình migration.

**Hoàn tất khi:** người khác triển khai theo tài liệu từ môi trường sạch, có dữ liệu kiểm chứng, phục hồi được backup và có biên bản nghiệm thu của người dùng nghiệp vụ.

## 4. Checklist nghiệm thu end-to-end

Chạy trên dữ liệu giả hoặc bộ dữ liệu được phép kiểm thử, ghi commit/cấu hình/model; ô trống là chưa kiểm tra, không phải mặc định đạt.

- [ ] Sales A tạo hồ sơ, chọn Teacher A, upload đúng định dạng; file vượt dung lượng/sai signature bị từ chối.
- [ ] Sales B và Teacher B không truy cập được hồ sơ/tài liệu/kết quả đó qua cả URL trực tiếp và API.
- [ ] Mở bản gốc, OCR PDF text, ảnh và PDF scan; thiếu dịch vụ hoặc trang lỗi hiển thị chính xác.
- [ ] Sửa/xác nhận/thêm trường có evidence; raw OCR còn nguyên và có audit.
- [ ] Nối các dòng học phần đã xác nhận với curriculum đúng phiên bản; trường thiếu không bị tự điền.
- [ ] Rule/mapping DRAFT không tạo kết quả như đã duyệt; các ca biên đã được chủ học thuật xác nhận cho kết quả đúng.
- [ ] Bấm tạo đề xuất hai lần không tạo trùng; chạy lại bằng phiên bản khác có dấu vết và run hiệu lực rõ.
- [ ] Teacher A duyệt/override có lý do, yêu cầu bổ sung theo luồng đã hoàn thiện; người ngoài không chốt được.
- [ ] Hồ sơ chỉ hoàn tất khi đủ quyết định của run hiệu lực; Sales nhận thông báo đúng hồ sơ và đánh dấu đã đọc được.
- [ ] Admin metrics/CSV khớp dữ liệu kiểm thử; Sales/Teacher không mở được chức năng Admin.
- [ ] Khởi động lại dịch vụ vẫn còn tài liệu/quyết định; backup khôi phục và mở được file thật.
- [ ] Máy mới clone/cài/migrate/test/chạy được theo README; Git không chứa secret/database/media runtime.

## 5. Bằng chứng kiểm tra lần bàn giao này

| Kiểm tra | Kết quả / phạm vi |
| --- | --- |
| Clone riêng nguồn `8c6dc62` | Thư mục tạm, không dùng database/media đang làm việc |
| `manage.py migrate` | Đạt với SQLite mới |
| `manage.py check` | Không có lỗi |
| `makemigrations --check --dry-run` | Không có thay đổi migration |
| `pytest -q` | Baseline 19/19; sau sửa importer có 20/20 đạt. Ollama trỏ tới cổng không chạy dịch vụ; media test của lượt cuối dùng thư mục tạm |
| Regression importer | Test tái hiện lỗi `Attempt to use ZIP archive that was already closed` trước sửa và đạt sau sửa; kiểm tra header/cell/raw value, tín chỉ công thức không bị đoán, dry-run và import lặp |
| Nối OCR → recommendation → teacher review (nhánh hiện tại) | 28 test đạt trên Python 3.12.14/Django 5.2.17; UI flow test dùng dữ liệu curriculum/mapping/rule tổng hợp. Migrate `0010`–`0012`, check và migration check sạch. Chưa nghiệm thu bằng nguồn học thuật thật hoặc browser UAT nhiều role |
| Import 5 curriculum trên clone tạm sau sửa | 5 khung DRAFT, 380 dòng nguồn; preview activation đúng 301 dòng mã/tên và 79 dòng cấu trúc; không kích hoạt dữ liệu thật |
| Preview lịch sử | 16 sheet khớp, 107 bỏ qua, 155 dòng (132 FULL, 23 PARTIAL); chưa ghi/duyệt lịch sử |
| Preview PDF quy định | Tìm đủ 3 file với 14/2/3 trang; chưa gọi OCR. pypdf cảnh báo trùng metadata `/Info` ở nguồn nhưng kiểm tra page count kết thúc thành công |
| Build wheel `pip wheel --no-deps` | Đạt; chưa chứng minh wheel có đủ package hoặc cài đầy đủ dependencies trên máy sạch |

Môi trường test dùng Python 3.14.5 và dependency đã cài trên máy bàn giao; hướng dẫn cài mới đề xuất Python 3.12 vì ràng buộc Pillow. Chưa nghiệm thu cài sạch Python 3.12/Windows, OCR thực, toàn bộ UI, PostgreSQL/Redis/private storage hay production. Kết quả test không thay thế phê duyệt học thuật.

## 6. Quy tắc cập nhật tài liệu khi bàn giao tiếp

Mỗi PR ghi: vấn đề và hành vi đã thay đổi; file/luồng bị tác động; migration/biến môi trường mới; lệnh kiểm tra và kết quả; phần còn thiếu; cách chạy lại trên máy mới. Cập nhật README nếu thay lệnh cài/chạy/import. Cập nhật bảng hiện trạng và bỏ đầu việc chỉ khi đạt tiêu chí nghiệm thu.

Gợi ý nội dung giao cho người/agent tiếp theo:

> Đọc README.md và HANDOVER.md, kiểm tra commit/trạng thái repo và chạy baseline trước. Bắt đầu từ đầu việc A: nối OCR đã xác nhận với đề xuất và màn hình giảng viên, giữ nguồn và audit. Giữ dữ liệu học thuật thiếu ở trạng thái cần kiểm chứng; không tự phê duyệt rule/mapping/precedent. Tách từng thay đổi nhỏ, kiểm tra UI/API liên quan, cập nhật tài liệu và push nhánh để review. Ghi rõ điều gì đã kiểm chứng, điều gì còn cần chủ học thuật hoặc môi trường production.
