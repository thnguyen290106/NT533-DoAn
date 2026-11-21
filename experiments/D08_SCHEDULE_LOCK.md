# D08-HXN · Lịch và trace đã khóa

- D9 có 54 lượt, D10 có 41 lượt, D11 có 9 lượt hiệu năng và 60 lượt mapping. Thứ tự dùng seed 53300. Window và trace được sinh trước lượt chính thức đầu tiên.
- CPU N=512000. Mỗi dòng lịch gắn profile, block, algorithm, số VU và SHA-256 trace. Bộ khóa A4 và trọng số hot-ID cũng có SHA-256 riêng theo seed.
- Ngân sách thời gian tăng vì warm-up 300 s đồng đều, thêm 312 phút cho 104 lượt so với warm-up 120 s. Dữ liệu chính thức bắt đầu sau khóa G3.

```text
b57a57f9aad1cfde534da6222242226524feee74a928be9a394f5be163dab363  locked.json
0ed502a7919a34f2dd1209de140635d1a2caf5c4b3dc4fe7e8d8bf3a4bb8f35e  schedule.csv
eafa7cf00ae41aee882faffbf63945369b45699df88a8825ad4f6371dae4d6ef  mapping-schedule.csv
```
