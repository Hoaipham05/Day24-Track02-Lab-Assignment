# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam; enforce qua region lock ở hạ tầng triển khai
- [ ] Backup cũng phải ở trong lãnh thổ VN; backup bucket/volume đặt tại region VN và có kiểm tra định kỳ
- [ ] Log việc transfer data ra ngoài nếu có; ghi audit log cho mọi export/copy sang hệ thống ngoài VN

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training; lưu consent flag trước khi đưa vào pipeline
- [ ] Có mechanism để user rút consent (Right to Erasure); soft-delete + remove khỏi training set lần build kế tiếp
- [ ] Lưu consent record với timestamp; lưu vào bảng audit/consent riêng

## C. Breach Notification (72h)
- [ ] Có incident response plan; định nghĩa owner, mức độ nghiêm trọng và playbook xử lý
- [ ] Alert tự động khi phát hiện breach; dùng Prometheus/Alertmanager để kích hoạt cảnh báo
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h; có checklist pháp lý và mẫu báo cáo sẵn

## D. DPO Appointment
- [ ] Đã bổ nhiệm Data Protection Officer
- [ ] DPO có thể liên hệ tại: dpo@medviet.local

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM envelope encryption at rest, TLS 1.3 in transit | 🚧 In Progress | Infra Team |
| Audit logging | Append-only API access logs, auth events, data export events, retention 90+ days | ⬜ Todo | Platform Team |
| Breach detection | Prometheus alerts on anomalous access patterns, export spikes, and auth failures | ⬜ Todo | Security Team |

## F. TODO: Điền vào phần còn thiếu
Với mỗi row còn "⬜ Todo", mô tả technical solution cụ thể bạn sẽ implement.

- Audit logging: ghi log JSON có timestamp, user, role, resource, action, status, request_id; đẩy sang storage chỉ-ghi.
- Breach detection: tạo alert rule cho số lần 403/401 tăng đột biến, truy cập raw data bất thường, và export dữ liệu ngoài giờ.
