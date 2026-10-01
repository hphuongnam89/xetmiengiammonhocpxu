# Gói duyệt rule/mapping — 2026-10-01

Phạm vi: môi trường thử nghiệm. Nguồn quy định chính là `017/2024/QĐ-PXU-NBS`, các trang ghi dưới đây. Không tự suy diễn nội dung chưa có trong nguồn.

## A. Rule đề nghị duyệt

| ID | Nội dung cần chốt | Nguồn |
| --- | --- | --- |
| `RULE-COMPARE-001` | Đối chiếu chuẩn đầu ra, nội dung, khối lượng học tập, phương thức đánh giá và điều kiện chất lượng với chương trình hiện hành. | trang 4 |
| `RULE-GRADE-001` | Kết quả môn trước tối thiểu 5/10 hoặc D+ khi nguồn chỉ có điểm chữ. | trang 4 |
| `RULE-CERTIFICATE-001` | Chứng chỉ dùng để xét phải còn hiệu lực theo quy định áp dụng. | trang 3–4 |
| `RULE-PARTIAL-001` | Nếu chỉ bao phủ một phần học phần thì chỉ công nhận phần có căn cứ; phần thiếu phải bổ sung và đánh giá. | trang 4 |
| `RULE-CREDIT-CAP-001` | Tổng khối lượng được công nhận không vượt 50% chương trình, không tính GDTC và GDQP. | trang 5 |
| `RULE-UNIT-001` | Quy đổi DVTHT, giờ học và tín chỉ theo đúng bảng công bố; không dùng công thức tự suy ra. | trang 5 |
| `RULE-GRADE-CONVERSION-001` | Dùng bảng quy đổi 10 điểm ↔ điểm chữ/4 điểm trong nguồn. | trang 6 |
| `RULE-ENGLISH-CREDITS-001` | Dùng bảng khối lượng tín chỉ/DVTHT tiếng Anh để xác định English 1, English 1–2 hoặc English 1–3. | trang 10 |
| `RULE-ENGLISH-CERTIFICATE-001` | Chứng chỉ tiếng Anh quốc tế dùng để xét phải nằm trong thời hạn 24 tháng theo nguồn. | trang 11–12 |

## B. Mapping cần nhập bảng chi tiết trước khi duyệt

Các mục dưới đây chưa được tự điền vì cần đúng từng dòng nguồn, điều kiện, học phần đích, điểm, ngoại lệ và thời hạn:

- Chính trị: trang 6–7.
- Pháp luật: trang 7–8.
- Giáo dục quốc phòng: trang 8–9.
- Giáo dục thể chất: trang 9.
- Bằng/chứng chỉ tiếng Anh: trang 10–12.
- Bằng/chứng chỉ CNTT: trang 12–13.
- Hội đồng và quy trình: trang 13–14.

## C. Dữ liệu Excel lịch sử

- Đã staging: 155 dòng có kết quả, gồm 132 `FULL` và 23 `PARTIAL`.
- 107 sheet chưa khớp cấu trúc và chưa được nhập.
- 155 dòng vẫn giữ trạng thái `PENDING`.
- Khi duyệt, mỗi dòng sẽ khóa nội dung, lưu người duyệt/thời điểm/ghi chú và chỉ được dùng làm precedent tham khảo.
- Dữ liệu lịch sử không tự thay thế rule và không tự quyết định hồ sơ mới.

## Quyết định đã ghi nhận

- `RULE-COMPARE-001`: bỏ/retire theo chốt ngày 2026-10-01.
- 8 rule còn lại trong mục A: `APPROVED` trong database demo, có audit actor/time và ghi chú phạm vi test.
- Các mapping chi tiết mục B vẫn chưa executable vì chưa có bảng từng dòng trong dữ liệu nguồn.

## Cách chốt

Reply theo một trong hai dạng:

1. `DUYỆT A` — duyệt 9 rule ở mục A, giữ B và C ở trạng thái chờ nhập/đối chiếu.
2. Ghi ID cần sửa, ví dụ: `Sửa RULE-CREDIT-CAP-001: ...; duyệt các ID còn lại.`

Sau khi có chốt, hệ thống sẽ tạo version thử nghiệm, ghi audit và dùng đúng các version đã duyệt trong demo.
